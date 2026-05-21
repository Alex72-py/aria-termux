"""Provider-agnostic API client for ARIA."""

import json
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    import google.generativeai as genai
except ModuleNotFoundError:
    genai = None

logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    api_key: str
    model: str = "gemma-4-26b-a4b-it"
    temperature: float = 0.7
    max_tokens: int = 8192
    provider: str = "google"
    timeout: int = 60
    stream: bool = False


class ProviderError(RuntimeError):
    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class BaseProvider:
    name = "base"

    def list_models(self) -> List[str]:
        raise NotImplementedError

    def generate(self, prompt: str, system_instruction: Optional[str], config: APIConfig) -> str:
        raise NotImplementedError


class GoogleProvider(BaseProvider):
    name = "google"

    def __init__(self, api_key: str):
        if genai is None:
            raise ProviderError(
                "Google provider requires the optional dependency `google-generativeai`",
                retryable=False,
            )
        self.api_key = api_key
        genai.configure(api_key=api_key)

    def list_models(self) -> List[str]:
        try:
            models = genai.list_models()
            return [m.name.replace("models/", "") for m in models]
        except Exception as e:
            raise ProviderError(f"Google model list failed: {e}", retryable=False) from e

    def generate(self, prompt: str, system_instruction: Optional[str], config: APIConfig) -> str:
        try:
            model = genai.GenerativeModel(
                model_name=config.model,
                system_instruction=system_instruction,
                generation_config=genai.types.GenerationConfig(
                    temperature=config.temperature,
                    max_output_tokens=config.max_tokens,
                ),
            )
            response = model.generate_content(prompt)
            text = getattr(response, "text", None)
            if not text:
                raise ProviderError("Google returned an empty/malformed response", retryable=True)
            return text
        except Exception as e:
            msg = str(e).lower()
            retryable = any(k in msg for k in ("timeout", "tempor", "429", "quota", "unavailable"))
            raise ProviderError(f"Google request failed: {e}", retryable=retryable) from e


class OpenAICompatProvider(BaseProvider):
    """Provider for OpenRouter and NVIDIA NIM using OpenAI-compatible chat API."""

    def __init__(self, name: str, api_key: str, base_url: str, extra_headers: Optional[Dict[str, str]] = None):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.extra_headers = extra_headers or {}

    def _request_json(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        headers.update(self.extra_headers)
        req = urllib.request.Request(url, method=method, data=data, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            lowered = body.lower()
            if e.code in (401, 403):
                raise ProviderError(f"{self.name} auth failed (invalid API key)", retryable=False)
            if e.code == 404:
                raise ProviderError(f"{self.name} model/API route unavailable", retryable=False)
            if e.code == 429:
                raise ProviderError(f"{self.name} rate limit reached", retryable=True)
            if 500 <= e.code <= 599:
                raise ProviderError(f"{self.name} provider downtime/server error ({e.code})", retryable=True)
            raise ProviderError(f"{self.name} HTTP {e.code}: {body[:180]}", retryable=("timeout" in lowered))
        except urllib.error.URLError as e:
            raise ProviderError(f"{self.name} network error: {e}", retryable=True) from e
        except json.JSONDecodeError as e:
            raise ProviderError(f"{self.name} returned malformed JSON: {e}", retryable=True) from e
        except Exception as e:
            raise ProviderError(f"{self.name} unexpected failure: {e}", retryable=True) from e

    def list_models(self) -> List[str]:
        data = self._request_json("GET", "/models")
        models: List[str] = []
        for item in data.get("data", []):
            model_id = item.get("id")
            if model_id:
                models.append(model_id)
        if not models:
            raise ProviderError(f"{self.name} returned no models", retryable=False)
        return models

    def generate(self, prompt: str, system_instruction: Optional[str], config: APIConfig) -> str:
        messages: List[Dict[str, str]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": config.model,
            "messages": messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "stream": bool(config.stream),
        }
        if config.stream:
            return self._generate_stream(payload, timeout=config.timeout)
        data = self._request_json("POST", "/chat/completions", payload=payload, timeout=config.timeout)
        try:
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise ProviderError(f"{self.name} malformed completion payload", retryable=True) from e

    def _generate_stream(self, payload: Dict[str, Any], timeout: int) -> str:
        """Best-effort streaming with graceful fallback if stream interrupts."""
        url = f"{self.base_url}/chat/completions"
        req = urllib.request.Request(
            url,
            method="POST",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                **self.extra_headers,
            },
        )
        chunks: List[str] = []
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    body = line[5:].strip()
                    if body == "[DONE]":
                        break
                    try:
                        event = json.loads(body)
                        delta = event.get("choices", [{}])[0].get("delta", {}).get("content")
                        if delta:
                            chunks.append(delta)
                    except Exception:
                        continue
        except Exception as e:
            if chunks:
                # Partial stream recovery for interruptions.
                return "".join(chunks)
            raise ProviderError(f"{self.name} streaming interrupted: {e}", retryable=True) from e
        text = "".join(chunks).strip()
        if not text:
            raise ProviderError(f"{self.name} returned empty streamed response", retryable=True)
        return text


class APIClient:
    SUPPORTED_PROVIDERS: Dict[str, str] = {
        "google": "Google AI Studio",
        "openrouter": "OpenRouter",
        "nvidia_nim": "NVIDIA NIM",
    }

    def __init__(self, config: APIConfig):
        self.config = config
        self.available_models: List[str] = []
        self.last_error: Optional[str] = None
        self._provider: Optional[BaseProvider] = None
        self._initialize_provider()

    def _initialize_provider(self):
        p = self.config.provider.lower().strip()
        key = (self.config.api_key or "").strip()
        if not key:
            raise ValueError(f"No API key configured for provider '{p}'")
        try:
            if p == "google":
                self._provider = GoogleProvider(key)
            elif p == "openrouter":
                self._provider = OpenAICompatProvider(
                    name="OpenRouter",
                    api_key=key,
                    base_url="https://openrouter.ai/api/v1",
                    extra_headers={"HTTP-Referer": "https://termux.dev", "X-Title": "ARIA-Termux"},
                )
            elif p == "nvidia_nim":
                self._provider = OpenAICompatProvider(
                    name="NVIDIA NIM",
                    api_key=key,
                    base_url="https://integrate.api.nvidia.com/v1",
                )
            else:
                raise ValueError(f"Unsupported provider: {self.config.provider}")
            logger.info(f"API provider initialized: {p} model={self.config.model}")
        except ProviderError as e:
            self._provider = None
            logger.error(f"API provider unavailable: {e}")

    def get_supported_providers(self) -> Dict[str, str]:
        return dict(self.SUPPORTED_PROVIDERS)

    def fetch_available_models(self) -> List[str]:
        try:
            self.available_models = self._provider.list_models() if self._provider else []
            self.last_error = None
            return self.available_models
        except ProviderError as e:
            self.last_error = str(e)
            logger.error(self.last_error)
            return self.available_models[:]

    def validate_model(self, model: str) -> bool:
        if not self.available_models:
            self.fetch_available_models()
        return model in self.available_models if self.available_models else True

    def generate_content(self, prompt: str, system_instruction: Optional[str] = None, max_retries: int = 3) -> str:
        if not self._provider:
            return self._get_fallback_response()

        validated = self.validate_model(self.config.model)
        if not validated and self.available_models:
            old = self.config.model
            self.config.model = self.available_models[0]
            logger.warning(f"Model '{old}' unavailable; switched to '{self.config.model}'")

        for attempt in range(max_retries):
            try:
                text = self._provider.generate(prompt, system_instruction, self.config)
                self.last_error = None
                return text
            except ProviderError as e:
                self.last_error = str(e)
                logger.warning(f"Provider attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt >= max_retries - 1 or not e.retryable:
                    break
                time.sleep(min(4, 2 ** attempt))
            except Exception as e:
                self.last_error = str(e)
                logger.warning(f"Unexpected attempt failure {attempt + 1}/{max_retries}: {e}")
                if attempt >= max_retries - 1:
                    break
                time.sleep(min(4, 2 ** attempt))
        return self._get_fallback_response()

    def _get_fallback_response(self) -> str:
        return (
            f"API Error ({self.config.provider}/{self.config.model}): {self.last_error}\n\n"
            "Fallback: offline mode is active; use `/kb <query>` for offline help.\n"
            "Try `/provider list`, `/provider set <name>`, `/model list`, or `/config`."
        )

    def is_available(self) -> bool:
        return bool(self.fetch_available_models())

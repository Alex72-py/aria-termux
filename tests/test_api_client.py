"""
Tests for API client module.
"""

import pytest
from aria.api_client import APIClient, APIConfig


def test_api_config_creation():
    """Test API config creation."""
    config = APIConfig(
        api_key="test-key",
        model="gemma-4-26b-a4b-it",
        temperature=0.7,
        max_tokens=2048,
    )
    
    assert config.api_key == "test-key"
    assert config.model == "gemma-4-26b-a4b-it"
    assert config.temperature == 0.7
    assert config.max_tokens == 2048


def test_api_client_initialization():
    """Test API client initialization."""
    config = APIConfig(api_key="test-key")
    client = APIClient(config)
    
    assert client.config.api_key == "test-key"
    assert client.available_models == []
    assert client.last_error is None


def test_api_client_fallback_response():
    """Test fallback response generation."""
    config = APIConfig(api_key="test-key")
    client = APIClient(config)
    client.last_error = "Test error"
    
    response = client._get_fallback_response()
    
    assert "API Error" in response
    assert "offline mode" in response.lower()
    assert "Test error" in response


# --- Google provider without google-generativeai (issue #2) ---

import io
import json
import urllib.error

from aria import api_client
from aria.api_client import GoogleRESTProvider, ProviderError


class _FakeResponse:
    def __init__(self, payload):
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _http_error(code, body):
    return urllib.error.HTTPError(
        "https://example.test", code, "err", {}, io.BytesIO(json.dumps(body).encode("utf-8"))
    )


def _patch_urlopen(monkeypatch, handler):
    calls = []

    def fake(req, timeout=None):
        calls.append(req)
        return handler(req)

    monkeypatch.setattr(api_client.urllib.request, "urlopen", fake)
    return calls


def test_google_uses_rest_provider_without_sdk(monkeypatch):
    monkeypatch.setattr(api_client, "genai", None)
    client = APIClient(APIConfig(api_key="k", provider="google"))
    assert isinstance(client._provider, GoogleRESTProvider)
    assert client.last_error is None


def test_google_rest_list_models_paginates_and_filters(monkeypatch):
    pages = [
        {
            "models": [
                {"name": "models/gemma-4-26b-a4b-it", "supportedGenerationMethods": ["generateContent"]},
                {"name": "models/embedding-001", "supportedGenerationMethods": ["embedContent"]},
            ],
            "nextPageToken": "t2",
        },
        {"models": [{"name": "models/gemma-4-31b-it", "supportedGenerationMethods": ["generateContent"]}]},
    ]
    calls = _patch_urlopen(monkeypatch, lambda req: _FakeResponse(pages[len(calls) - 1]))

    models = GoogleRESTProvider("secret-key").list_models()

    assert models == ["gemma-4-26b-a4b-it", "gemma-4-31b-it"]
    assert "pageToken=t2" in calls[1].full_url
    for req in calls:
        assert "secret-key" not in req.full_url
        assert req.get_header("X-goog-api-key") == "secret-key"


def test_google_rest_generate_payload_and_parse(monkeypatch):
    calls = _patch_urlopen(
        monkeypatch,
        lambda req: _FakeResponse(
            {"candidates": [{"content": {"parts": [{"text": "hidden", "thought": True}, {"text": "hello"}]}}]}
        ),
    )
    cfg = APIConfig(api_key="k", model="models/gemma-4-26b-a4b-it", temperature=0.2, max_tokens=99)

    out = GoogleRESTProvider("k").generate("hi", "be brief", cfg)

    assert out == "hello"
    assert calls[0].full_url.endswith("/models/gemma-4-26b-a4b-it:generateContent")
    body = json.loads(calls[0].data)
    assert body["systemInstruction"]["parts"][0]["text"] == "be brief"
    assert body["contents"][0]["parts"][0]["text"] == "hi"
    assert body["generationConfig"] == {"temperature": 0.2, "maxOutputTokens": 99}


def test_google_rest_retries_without_system_instruction(monkeypatch):
    def handler(req):
        if "systemInstruction" in json.loads(req.data):
            raise _http_error(400, {"error": {"message": "Developer instruction is not enabled"}})
        return _FakeResponse({"candidates": [{"content": {"parts": [{"text": "ok"}]}}]})

    calls = _patch_urlopen(monkeypatch, handler)
    out = GoogleRESTProvider("k").generate("question", "rules", APIConfig(api_key="k"))

    assert out == "ok"
    assert len(calls) == 2
    assert json.loads(calls[1].data)["contents"][0]["parts"][0]["text"] == "rules\n\nquestion"


def test_google_rest_invalid_key_is_not_retryable(monkeypatch):
    _patch_urlopen(monkeypatch, lambda req: (_ for _ in ()).throw(
        _http_error(400, {"error": {"message": "API key not valid. Please pass a valid API key."}})
    ))
    with pytest.raises(ProviderError) as exc:
        GoogleRESTProvider("bad").list_models()
    assert "invalid API key" in str(exc.value)
    assert exc.value.retryable is False


def test_google_rest_empty_response_is_retryable(monkeypatch):
    _patch_urlopen(monkeypatch, lambda req: _FakeResponse({"candidates": []}))
    with pytest.raises(ProviderError) as exc:
        GoogleRESTProvider("k").generate("hi", None, APIConfig(api_key="k"))
    assert exc.value.retryable is True


def test_google_rest_blocked_prompt_is_not_retryable(monkeypatch):
    _patch_urlopen(monkeypatch, lambda req: _FakeResponse({"promptFeedback": {"blockReason": "SAFETY"}}))
    with pytest.raises(ProviderError) as exc:
        GoogleRESTProvider("k").generate("hi", None, APIConfig(api_key="k"))
    assert exc.value.retryable is False

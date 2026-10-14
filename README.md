<div align="center">

# ARIA — AI Terminal Co-Pilot for Termux

[![Python](https://img.shields.io/badge/Python-89%25-3776ab?logo=python&logoColor=white)](https://python.org)
[![Shell](https://img.shields.io/badge/Shell-11%25-4EAA25?logo=gnu-bash&logoColor=white)](https://www.gnu.org/software/bash/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**A terminal AI assistant that actually understands Termux.**

</div>

---

## Status

ARIA was originally built for the Google Gemma 4 Challenge ([write-up](https://dev.to/alex72py/i-built-aria-an-ai-terminal-co-pilot-for-termux-using-gemma-4-be4)). That's over, and it's now a regular open-source tool that works with any model its providers offer. It's built and maintained by one person, so work is driven by [issues](https://github.com/Alex72-py/aria-termux/issues) and pull requests rather than a deadline.

- **Stable:** the core loop, slash commands, Guardian, watch mode, offline knowledge base, and three providers (Google AI Studio, OpenRouter, NVIDIA NIM).

---

## What is this?

ARIA is an AI assistant that lives in your terminal. It knows about Termux, Android filesystem quirks, proot containers, clang-not-gcc, and all the weird stuff you deal with when developing on a phone.

It can answer questions, diagnose errors, suggest fixes, and auto-repair broken installs, all from a slash-command interface inside Termux.

**It's lightweight.** One dependency (`rich`). Everything else is stdlib. No bloated frameworks.

---

## Screenshots

<details>
<summary><b>Click to expand</b></summary>

### Startup
<img width="1080" height="2173" alt="Startup" src="https://github.com/user-attachments/assets/8ad4418c-72b1-4581-9dff-092006ff4b67" />

### Model Selection
<img width="1080" height="2157" alt="Model Selection" src="https://github.com/user-attachments/assets/8f8a4674-ba89-4204-8f99-f54bbca52833" />

### Error Analysis
<img width="1079" height="2162" alt="Error Analysis" src="https://github.com/user-attachments/assets/a216a5a2-9897-4e68-90ed-94dfe55bae00" />

</details>

## Demo

https://github.com/user-attachments/assets/1795a534-37a9-4f81-b217-e13b95cb1836

---

## Install

```bash
pkg update && pkg upgrade -y
pkg install python git -y

git clone https://github.com/Alex72-py/aria-termux.git
cd aria-termux
pip install -r requirements.txt --break-system-packages

python run_aria.py
```

The Google provider works with no extra packages. If `google-generativeai` is installed, ARIA uses it. If not, ARIA talks to the Google API directly over HTTPS. You only need the package if you specifically want the SDK path:
```bash
pip install google-generativeai --break-system-packages
```

---

## First Run

On first launch, ARIA detects there's no config and walks you through setup:

```
Choose provider [google/openrouter/nvidia_nim]: google
Enter API key: ••••••••••••••
Enter model (press Enter for the default):
Enable Guardian mode? [y/n]: y
```

It validates your key right there. If something's wrong, you'll know immediately instead of getting cryptic errors later.

**Get a free key:**
- Google: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- OpenRouter: [openrouter.ai/keys](https://openrouter.ai/keys)
- NVIDIA NIM: [build.nvidia.com](https://build.nvidia.com)

---

## Usage

Just type. Bare text goes to the model as a question. Or use slash commands:

| Command | What it does |
|---------|-------------|
| `/ask <question>` | Ask anything |
| `/fix` | Diagnose the last failed command |
| `/fix "error text"` | Diagnose a specific error |
| `/provider list` | Show configured providers |
| `/provider openrouter` | Switch provider |
| `/provider cycle` | Rotate to next provider |
| `/provider key <name>` | Update a provider's API key |
| `/model list` | List available models |
| `/model set <name>` | Switch model |
| `/kb <query>` | Search offline knowledge base |
| `/watch` | Toggle watch mode (monitors errors from other sessions) |
| `/status` | Show current state |
| `/config` | Re-run the setup wizard |
| `/help` | Show all commands |

### Watch Mode

Enable `/watch`, then work in another Termux session. When a command fails there, the shell hook writes it to `~/.aria/last_fail.json`. Come back to ARIA, type `/fix`, and it reads the failure automatically.

---

## Providers

| Provider | Endpoint | Auth |
|----------|----------|------|
| `google` | Google AI Studio | API key from aistudio |
| `openrouter` | openrouter.ai | API key from dashboard |
| `nvidia_nim` | integrate.api.nvidia.com | API key from build.nvidia.com |

ARIA auto-discovers available models from whichever provider you're using. Run `/model list` to see them and `/model set <name>` to switch.

---

## Architecture

```
aria/
├── main.py          — Main loop, command dispatch, setup wizard
├── api_client.py    — Provider abstraction (Google, OpenRouter, NVIDIA)
├── command_system.py — Slash command registry and parsing
├── config.py        — JSON config management (~/.aria/config.json)
├── guardian.py      — Risk scoring and confirmation prompts
├── knowledge_base.py — Offline Termux troubleshooting data
├── watch_mode.py    — File watcher for cross-session error capture
├── repair_agent.py  — Local-first fix planning (no model call needed)
└── ui.py            — Rich terminal output, spinners, formatting
```

The API layer uses Python's `urllib` directly. No `requests`, no `httpx`, no heavy HTTP libs. Provider switching is just changing which base URL and auth header gets used.

For the full design, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Guardian

Before ARIA suggests running anything dangerous, it scores the risk:

| Level | What happens |
|-------|-------------|
| Low (green) | Runs immediately |
| Medium (yellow) | Runs with a notice |
| High (orange) | Asks for confirmation |
| Critical (red) | Requires explicit approval |

Things like `rm -rf`, `chmod 777`, pipe-to-shell curls — all get flagged.

---

## Config

Stored at `~/.aria/config.json`:

```json
{
  "provider": "google",
  "api_key": "your-active-key",
  "api_keys": {
    "google": "...",
    "openrouter": "...",
    "nvidia_nim": "..."
  },
  "model": "your-model-name",
  "temperature": 0.7,
  "max_tokens": 8192,
  "guardian_mode": true,
  "watch_mode": false,
  "auto_apply": false
}
```

You can also override with env vars:
```bash
export ARIA_API_KEY="..."
export ARIA_PROVIDER="openrouter"
export ARIA_MODEL="your-model-name"
```

---

## Dependencies

| Package | Why | Required |
|---------|-----|:--------:|
| `rich` | Terminal UI, syntax highlighting, spinners | Yes |
| `google-generativeai` | Optional SDK for the Google provider (ARIA falls back to plain HTTPS without it) | No |

Everything else (HTTP, JSON, threading, config) is stdlib. All three providers work with no extra packages.

---

## Testing

```bash
pytest -q
pytest -v          # verbose
```

---

## Known limitations

- Watch mode works via file polling. It's not instant, but it's reliable.
- AI features need internet. The knowledge base (`/kb`) works offline.
- Built for Termux on Android. It runs on Linux too, but that's not the focus.
- Auto-fix suggestions should be reviewed before applying.

---

## Contributing

Issues and PRs are welcome. Bug reports are the most useful thing right now, especially ones that include your Termux version, Android version, Python version, and which provider you were using.

```bash
git checkout -b feature/my-thing
# make changes
git commit -m "what you did"
git push origin feature/my-thing
```

Keep it simple. PEP 8. Tests for new features. Don't add dependencies unless absolutely necessary. See [CONTRIBUTING.md](CONTRIBUTING.md) for more.

---

## License

MIT. See [LICENSE](LICENSE).

---

<div align="center">

[![Stars](https://img.shields.io/github/stars/Alex72-py/aria-termux?style=social)](https://github.com/Alex72-py/aria-termux)
[![GitHub](https://img.shields.io/badge/GitHub-Alex72--py-181717?logo=github)](https://github.com/Alex72-py)

</div>

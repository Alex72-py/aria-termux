ARIA — AI Terminal Co-Pilot for Termux

«Built for developers who use Termux as a real development environment on Android.»

ARIA is a terminal-native AI assistant designed specifically for Termux and Android development workflows. It combines Google's Gemma 4 models with a Termux-focused knowledge base, command system, and safety layer to create an AI experience that feels native to the mobile terminal environment.

Unlike generic desktop-focused coding assistants, ARIA understands the unique constraints of Android-based development:

- Clang instead of GCC
- Android filesystem quirks
- Proot/container environments
- Mobile-only workflows
- Package and permission limitations
- Termux-specific debugging patterns

---

✨ Features

- Slash Command Interface
  Claude Code-style workflows using commands like "/ask", "/fix", "/models", and "/watch".

- Model Discovery & Selection
  Automatically fetches available Gemma models and allows dynamic model switching directly inside the terminal.

- Self-Healing API Layer
  Detects invalid models, retries requests gracefully, and falls back safely when API issues occur.

- Guardian Safety Layer
  Risk scoring and confirmation prompts for dangerous shell operations.

- Rich Terminal UI
  Animated startup sequence, syntax highlighting, spinners, formatted panels, and color-coded output.

- Offline Knowledge Base
  Built-in Termux troubleshooting knowledge covering package management, common errors, proot-distro, Python environments, and Android bridge tools.

- Clipboard Integration
  Copies generated commands directly to clipboard for faster terminal workflows.

- Experimental Watch Mode
  Monitors shell output and attempts to detect common errors automatically.

---

📸 Screenshots

![Startup] <img width="1080" height="1739" alt="Screenshot_2026-05-11-13-22-33-69_84d3000e3f4017145260f7618db1d683" src="https://github.com/user-attachments/assets/d31bd32d-1888-4df5-b5ad-548351a37724" />

![Models] <img width="1080" height="2400" alt="Screenshot_2026-05-11-13-24-40-55_84d3000e3f4017145260f7618db1d683" src="https://github.com/user-attachments/assets/51797cdb-1b46-44c2-8b29-188163e48a9d" />

![Fix] <img width="1080" height="2400" alt="Screenshot_2026-05-11-13-26-51-15_84d3000e3f4017145260f7618db1d683" src="https://github.com/user-attachments/assets/f1144d39-1a67-41fc-85ea-4386a5628f30" />


---

🚀 Quick Start

Installation (Termux)

pkg update && pkg upgrade -y
pkg install python git -y

git clone https://github.com/Alex72-py/aria-termux.git
cd aria-termux

pip install -r requirements.txt

python run_aria.py

---

🔑 First Run

ARIA launches a configuration wizard on first startup:

Welcome to ARIA Configuration Wizard

Enter Google AI Studio API key:
Enter preferred model:
Enable Guardian mode? [y/n]:
Enable watch mode? [y/n]:

Get a free API key from Google AI Studio:

https://aistudio.google.com/app/apikey

---

📖 Usage

Ask Questions

/ask How do I install Python on Termux?

Fix Errors

/fix "clang: error: linker command failed"

List Available Models

/models

Search Knowledge Base

/kb python module not found

Enable Watch Mode

/watch

---

🏗️ Architecture

ARIA Core
├── Command System
├── API Client
│   ├── Auto Model Discovery
│   ├── Retry Logic
│   └── Fallback Handling
├── Guardian Safety Layer
├── Watch Mode
├── Offline Knowledge Base
└── Rich Terminal UI

---

🧠 Knowledge Base Categories

- Common Termux Errors
- Package Management
- Python & Virtual Environments
- Proot-Distro
- Android Bridge Tools
- Git & SSH
- Networking & Ports

---

🛡️ Guardian Safety Layer

ARIA analyzes potentially dangerous commands before execution.

Risk Levels

Level| Description
Low| Safe operations
Medium| Network/code operations
High| User/system modifications
Critical| Recursive deletion or destructive commands

High-risk operations require explicit confirmation.

---

📊 Supported Models

ARIA supports Google Gemma models through Google AI Studio.

Examples include:

- gemma-4-2b-it
- gemma-4-4b-it
- gemma-4-26b-a4b-it
- gemma-4-31b-it

---

⚙️ Configuration

Configuration is stored locally:

~/.aria/config.json

Environment variable overrides:

ARIA_API_KEY
ARIA_MODEL

---

🧪 Testing

python -m pytest tests/

---

⚠️ Current Limitations

- Watch mode is experimental
- Internet connection required for AI features
- Optimized primarily for Termux on Android
- Some auto-fix suggestions require manual review

---

🧠 Transparent Reasoning Output

ARIA currently exposes portions of its intermediate reasoning and response planning during some operations.

This behavior is intentional for the current development phase and helps:

- Debug prompt and model behavior
- Inspect reasoning quality
- Improve transparency during testing
- Analyze response generation in real time

Future releases will introduce:

- Optional hidden reasoning mode
- Cleaner response streaming
- User-configurable verbosity levels
- Dedicated developer/debug modes

For the hackathon version, transparent reasoning is kept enabled to prioritize observability and rapid iteration.

---
📦 Dependencies

- google-generativeai
- rich
- click
- pydantic
- python-dotenv

---

🤝 Contributing

Contributions, improvements, and issue reports are welcome.

git checkout -b feature/my-feature

---

📄 License

MIT License

---

🎯 Hackathon Submission

Submitted for the Google Gemma 4 Challenge.

Highlights:

- Real-world Termux developer workflow focus
- Dynamic model discovery and switching
- Self-healing API behavior
- Mobile-first terminal UX
- Offline fallback support
- Safety-focused command execution

---

🚀 ARIA

Making Android terminal development faster, safer, and more usable.

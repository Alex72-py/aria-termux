<div align="center">

# 🚀 ARIA — AI Terminal Co-Pilot for Termux

[![Python](https://img.shields.io/badge/Python-89%25-3776ab?logo=python&logoColor=white)](https://python.org)
[![Shell](https://img.shields.io/badge/Shell-11%25-4EAA25?logo=gnu-bash&logoColor=white)](https://www.gnu.org/software/bash/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Google Gemma 4](https://img.shields.io/badge/Google%20Gemma-4-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)

> **Built for developers who use Termux as a real development environment on Android.**

</div>

---

## 📋 Table of Contents

- [About](#about)
- [✨ Features](#-features)
- [📸 Screenshots](#-screenshots)
- [🎬 Demo](#-demo)
- [🚀 Quick Start](#-quick-start)
- [🔑 First Run](#-first-run)
- [📖 Usage](#-usage)
- [🏗️ Architecture](#-architecture)
- [🧠 Knowledge Base](#-knowledge-base)
- [🛡️ Safety Features](#-safety-features)
- [📊 Supported Models](#-supported-models)
- [⚙️ Configuration](#-configuration)
- [🧪 Testing](#-testing)
- [⚠️ Limitations](#-limitations)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## About

ARIA is a terminal-native AI assistant designed specifically for Termux and Android development workflows. It combines Google's Gemma 4 models with a Termux-focused knowledge base, command system, and[...]

### Why ARIA?

Unlike generic desktop-focused coding assistants, ARIA understands the unique constraints of Android-based development:

<table>
<tr>
<td>

⚙️ **Clang** instead of GCC  
🗂️ **Android filesystem quirks**  
🔒 **Proot/container environments**  

</td>
<td>

📱 **Mobile-only workflows**  
🚫 **Package and permission limitations**  
🐛 **Termux-specific debugging patterns**  

</td>
</tr>
</table>

---

## ✨ Features

<table>
<tr>
<td>

### 💻 Advanced Terminal UI
- Slash Command Interface (`/ask`, `/fix`, `/models`, `/watch`)
- Rich syntax highlighting & formatting
- Animated startup sequences
- Color-coded output

</td>
<td>

### 🤖 Intelligent AI
- Dynamic Gemma model discovery
- Auto model switching
- Self-healing API layer
- Graceful fallback handling

</td>
</tr>
<tr>
<td>

### 🛡️ Safety First
- Risk scoring system
- Confirmation prompts for dangerous operations
- Guardian safety layer
- Multi-level command validation

</td>
<td>

### 📚 Knowledge Base
- Common Termux errors
- Package management tips
- Python environments
- Proot-distro setup
- Android bridge tools

</td>
</tr>
<tr>
<td colspan="2">

### 📋 Additional Features
- **Clipboard Integration**: Copy commands with one keystroke  
- **Watch Mode**: Auto-detect and analyze terminal errors  
- **Offline Support**: Works without internet for KB queries  

</td>
</tr>
</table>

---

## 📸 Screenshots

<details>
<summary><b>📱 Click to expand screenshot gallery</b></summary>

### Startup Interface
<img width="1080" height="1739" alt="Startup Screen" src="https://github.com/user-attachments/assets/72ccd238-74a9-4dd0-8e2c-97c00ec17584" />

### Model Selection
<img width="1080" height="2157" alt="Model Selection" src="https://github.com/user-attachments/assets/8f8a4674-ba89-4204-8f99-f54bbca52833" />

### Error Analysis
<img width="1079" height="2162" alt="Error Analysis" src="https://github.com/user-attachments/assets/a216a5a2-9897-4e68-90ed-94dfe55bae00" />

</details>

---

## 🎬 Demo

<div align="center">

### Interactive Walkthrough

> **Add your GIF here!** Replace the placeholder below with a demo GIF showing ARIA in action.

```
[Demo GIF coming soon - showing /ask command, error fixing workflow, and model switching]
```

Or embed directly:

![ARIA Demo](your-demo-gif-url-here)

**Video Tour:** Coming soon on YouTube

</div>

---

## 🚀 Quick Start

### Prerequisites
- Termux app on Android
- Python 3.8+
- Internet connection (for AI features)

### Installation

```bash
# Update system packages
pkg update && pkg upgrade -y

# Install required tools
pkg install python git -y
pkg install termux-api -y

# Clone and install ARIA
git clone https://github.com/Alex72-py/aria-termux.git
cd aria-termux

# Install Python dependencies
pip install -r requirements.txt

# Launch ARIA
python run_aria.py
```

> 💡 **Tip:** `termux-api` is optional but recommended for clipboard integration. ARIA will gracefully fall back without it.

---

## 🔑 First Run

ARIA launches an interactive configuration wizard on first startup:

```
╔══════════════════════════════════════════╗
║  Welcome to ARIA Configuration Wizard    ║
╚══════════════════════════════════════════╝

Enter Google AI Studio API key: ••••••••••••••
Enter preferred model: gemma-4-31b-it
Enable Guardian mode? [y/n]: y
Enable watch mode? [y/n]: n
```

**Get your free API key here:**  
🔗 [Google AI Studio](https://aistudio.google.com/app/apikey)

---

## 📖 Usage

### Command Reference

<table>
<tr><th>Command</th><th>Description</th><th>Example</th></tr>
<tr>
<td><code>/ask</code></td>
<td>Ask ARIA any question about Termux or development</td>
<td><code>/ask How do I install Python on Termux?</code></td>
</tr>
<tr>
<td><code>/fix</code></td>
<td>Analyze and fix terminal errors</td>
<td><code>/fix "clang: error: linker command failed"</code></td>
</tr>
<tr>
<td><code>/models</code></td>
<td>List all available Gemma models</td>
<td><code>/models</code></td>
</tr>
<tr>
<td><code>/kb</code></td>
<td>Search the offline knowledge base</td>
<td><code>/kb python module not found</code></td>
</tr>
<tr>
<td><code>/watch</code></td>
<td>Enable automatic error detection</td>
<td><code>/watch</code></td>
</tr>
</table>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           ARIA Core System              │
├─────────────────────────────────────────┤
│  📋 Command System                      │
│  ├─ /ask, /fix, /models, /kb, /watch   │
│                                         │
│  🤖 API Client                          │
│  ├─ Auto Model Discovery                │
│  ├─ Intelligent Retry Logic             │
│  └─ Fallback Handling                   │
│                                         │
│  🛡️ Guardian Safety Layer               │
│  ├─ Risk Assessment                     │
│  └─ Confirmation Prompts                │
│                                         │
│  👀 Watch Mode                          │
│  ├─ Error Detection                     │
│  └─ Auto Analysis                       │
│                                         │
│  📚 Offline Knowledge Base              │
│  └─ Termux Troubleshooting              │
│                                         │
│  🎨 Rich Terminal UI                    │
│  ├─ Syntax Highlighting                 │
│  ├─ Animations                          │
│  └─ Color-Coded Output                  │
└─────────────────────────────────────────┘
```

---

## 🧠 Knowledge Base

ARIA includes comprehensive offline knowledge covering:

| Category | Topics |
|----------|--------|
| 🐛 **Common Errors** | Package conflicts, permission issues, build errors |
| 📦 **Package Management** | pkg, apt, pip installation & troubleshooting |
| 🐍 **Python** | Virtual environments, venv, pip caching |
| 🐧 **Proot-Distro** | Linux distributions, container setup |
| 🔌 **Android Bridge** | Termux:API, Tasker integration, system access |
| 🔐 **Git & SSH** | SSH keys, Git configuration, GitHub access |
| 🌐 **Networking** | Port forwarding, localhost, DNS issues |

---

## 🛡️ Safety Features

### Guardian Safety Layer

ARIA analyzes potentially dangerous commands before execution with a comprehensive risk assessment system:

<table>
<tr>
<th>Risk Level</th>
<th>Color</th>
<th>Description</th>
<th>Action</th>
</tr>
<tr>
<td>🟢 Low</td>
<td>Green</td>
<td>Safe operations (listing, viewing)</td>
<td>Execute immediately</td>
</tr>
<tr>
<td>🟡 Medium</td>
<td>Yellow</td>
<td>Network/code operations</td>
<td>Execute with notice</td>
</tr>
<tr>
<td>🟠 High</td>
<td>Orange</td>
<td>User/system modifications</td>
<td>Require confirmation</td>
</tr>
<tr>
<td>🔴 Critical</td>
<td>Red</td>
<td>Recursive deletion, destructive commands</td>
<td>Require explicit approval</td>
</tr>
</table>

---

## 📊 Supported Models

ARIA supports the full lineup of Google Gemma 4 models:

```
Gemma 4 Model Family
├── gemma-4-2b-it      (Lightweight, 2B parameters)
├── gemma-4-4b-it      (Balanced, 4B parameters)
├── gemma-4-26b-a4b-it (Advanced, 26B parameters)
└── gemma-4-31b-it     (Expert, 31B parameters)
```

**Auto-discovery:** ARIA fetches available models from your API key automatically.

---

## ⚙️ Configuration

### Config File

Configuration is stored locally in:
```
~/.aria/config.json
```

Example structure:
```json
{
  "api_key": "your-google-ai-studio-key",
  "model": "gemma-4-31b-it",
  "guardian_mode": true,
  "watch_mode": false
}
```

### Environment Variables

Override config with environment variables:

```bash
export ARIA_API_KEY="your-key"
export ARIA_MODEL="gemma-4-31b-it"
export ARIA_GUARDIAN_MODE="true"
```

---

## 🧪 Testing

Run the test suite with pytest:

```bash
# Run all tests
python -m pytest tests/

# Run with verbose output
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_api.py
```

---

## ⚠️ Limitations

> **Development Status:** This is a hackathon submission. These limitations are planned for future releases.

- 🔄 Watch mode is experimental and may require manual review
- 🌐 Internet connection required for AI features (knowledge base works offline)
- 📱 Optimized primarily for Termux on Android
- 🤔 Some auto-fix suggestions require manual verification
- 📊 Transparent reasoning output shows intermediate model thinking

---

## 🧠 Transparent Reasoning

ARIA intentionally exposes intermediate reasoning during operations. This helps:

✅ Debug prompt and model behavior  
✅ Inspect reasoning quality  
✅ Improve transparency during testing  
✅ Analyze response generation in real time  

**Future releases** will include:
- Optional hidden reasoning mode
- Cleaner response streaming
- User-configurable verbosity levels
- Dedicated developer/debug modes

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `google-generativeai` | Google Gemma API client |
| `rich` | Rich terminal formatting & UI |
| `click` | CLI command interface |
| `pydantic` | Data validation & models |
| `python-dotenv` | Environment variable management |

See `requirements.txt` for versions and additional dependencies.

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

```bash
# Create a feature branch
git checkout -b feature/my-feature

# Make your changes and commit
git add .
git commit -m "Add my feature"

# Push and create a pull request
git push origin feature/my-feature
```

**Guidelines:**
- Follow PEP 8 for Python code
- Add tests for new features
- Update documentation
- Keep commits focused and descriptive

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 Alex72-py

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 🎯 Hackathon Submission

**Submitted for:** Google Gemma 4 Challenge

### 🏆 Highlights

- 🎯 **Real-world Focus**: Actual Termux developer workflow optimization
- 🔄 **Dynamic Discovery**: Auto-detect and switch between available models
- 🛡️ **Resilient API**: Self-healing with intelligent retry logic
- 📱 **Mobile-First**: Terminal UI optimized for small screens
- 💾 **Offline Ready**: Fallback support without internet connection
- 🔐 **Safety-Conscious**: Risk assessment before executing commands

---

<div align="center">

### 🚀 ARIA

*Making Android terminal development faster, safer, and more usable.*

**[⬆ back to top](#-aria--ai-terminal-co-pilot-for-termux)**

[![Stars](https://img.shields.io/github/stars/Alex72-py/aria-termux?style=social)](https://github.com/Alex72-py/aria-termux)
[![GitHub](https://img.shields.io/badge/GitHub-Alex72--py-181717?logo=github)](https://github.com/Alex72-py)

</div>

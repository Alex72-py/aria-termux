# ARIA — Autonomous Repair and Intelligence Agent

**ARIA** is a terminal-native AI co-pilot designed specifically for **Termux/Android development**. It combines the power of Google's Gemma 4 LLM with deep knowledge of Termux constraints and best practices, delivering a production-grade CLI tool that feels like a native shell extension.

## 🎯 Key Features

- **Slash Command Interface**: Claude Code-style commands (`/ask`, `/fix`, `/watch`) instead of positional arguments
- **Watch Mode**: Ambient monitoring that auto-detects and fixes shell errors in real-time
- **Self-Healing API**: Automatically detects wrong models, fetches available ones, and retries gracefully
- **Guardian Safety Layer**: Risk scoring and user confirmation for dangerous operations
- **Rich Terminal UI**: Cinematic boot sequence, animations, syntax highlighting, and beautiful output
- **Termux Knowledge Base**: 100+ entries covering common Termux errors, package management, proot-distro, and Android bridge
- **Offline Fallback**: Full offline mode with embedded knowledge base when API is unavailable
- **Zero Credit Card Required**: Works with Google AI Studio free tier (15 req/min, 1500 req/day)

## 🚀 Quick Start

### Installation on Termux

```bash
# Install dependencies
pkg update && pkg upgrade
pkg install python git

# Clone repository
git clone https://github.com/yourusername/aria-agent.git
cd aria-agent

# Install ARIA
pip install -e .

# Run ARIA
aria
```

### First Run

On first run, ARIA will launch the configuration wizard:

```
Welcome to ARIA Configuration Wizard
Enter Google AI Studio API key: [paste your key]
Enter model name [default: gemma-4-26b-a4b-it]: 
Enable watch mode by default? [y/n]: y
Enable Guardian safety mode? [y/n]: y
```

**Get your free API key**: https://aistudio.google.com/app/apikey

## 📖 Usage

### Basic Commands

```bash
# Ask the AI a question
/ask How do I install Python on Termux?

# Analyze and fix an error
/fix "clang: error: linker command failed"

# Enable watch mode (auto-detect and fix errors)
/watch

# List available models
/models

# Search knowledge base
/kb port already in use

# Show command history
/history

# Display help
/help

# Exit ARIA
/exit
```

### Watch Mode

Watch mode monitors your shell output and automatically detects errors:

```bash
aria> /watch
👁️  Watch mode enabled. Monitoring shell for errors...

# Now run commands in another terminal
# ARIA will detect errors and suggest fixes
```

### Configuration

Update settings anytime:

```bash
aria> /config
Welcome to ARIA Configuration Wizard
...
```

## 🏗️ Architecture

```
ARIA Core System
├── API Client (Self-Healing)
│   ├── Auto-detect available models
│   ├── Exponential backoff retry logic
│   └── Graceful fallback to offline mode
├── Command System
│   ├── Slash command parser
│   ├── Dynamic command registration
│   └── Command history tracking
├── Guardian Safety Layer
│   ├── Risk scoring algorithm
│   ├── Dangerous pattern detection
│   └── User confirmation prompts
├── Watch Mode
│   ├── Shell output monitoring
│   ├── Error pattern matching
│   └── Auto-fix execution
├── Knowledge Base
│   ├── 100+ Termux-specific entries
│   ├── Fuzzy search matching
│   └── Category-based organization
└── Rich UI
    ├── ASCII art boot sequence
    ├── Spinner animations
    ├── Syntax highlighting
    └── Color-coded output
```

## 🧠 Knowledge Base Categories

- **Errors**: Common error patterns and solutions
- **Package Management**: pkg, apt, package installation
- **Proot-Distro**: Ubuntu/Debian in Termux
- **Android Bridge**: Termux:API integration
- **Development**: Git, SSH, Python venv, port forwarding

## 🛡️ Guardian Safety Layer

ARIA analyzes commands for risk before execution:

- **Low Risk**: Safe commands (ls, cat, grep, etc.)
- **Medium Risk**: Network operations, code evaluation
- **High Risk**: Sudo, user modification, firewall changes
- **Critical Risk**: Recursive deletion, filesystem format, fork bombs

High-risk operations require user confirmation.

## 📊 API Specifications

### Google AI Studio API

- **Base URL**: `https://generativelanguage.googleapis.com/v1beta`
- **Model**: `gemma-4-26b-a4b-it` (default)
- **Free Tier**: 15 req/min, 1500 req/day
- **No credit card required**

### Available Models

- `gemma-4-2b-it`
- `gemma-4-4b-it`
- `gemma-4-26b-a4b-it` (recommended)
- `gemma-4-31b-it`

## 🔧 Configuration

Configuration is stored in `~/.aria/config.json`:

```json
{
  "api_key": "your-api-key",
  "model": "gemma-4-26b-a4b-it",
  "temperature": 0.7,
  "max_tokens": 2048,
  "watch_mode": false,
  "guardian_mode": true,
  "created_at": "2026-05-10T12:00:00",
  "updated_at": "2026-05-10T12:00:00"
}
```

### Environment Variables

- `ARIA_API_KEY`: Override API key
- `ARIA_MODEL`: Override model name

## 📝 Examples

### Example 1: Quick Error Fix

```bash
$ aria
🔧 Initializing core systems...
🧠 Loading neural networks...
📡 Connecting to API...
📚 Loading knowledge base...
🛡️  Activating Guardian safety layer...
✅ ARIA ready for Termux development!

aria> /fix "clang: error: linker command failed"
⏳ Analyzing error...

🔍 Error Detected: Compilation error
Pattern: clang: error
💡 Solution:
Check compilation flags. Termux may need `-fPIC` for position-independent code. 
Try `pkg install build-essential` for common build tools.

🔧 Auto-fix available: pkg install clang
```

### Example 2: Knowledge Base Search

```bash
aria> /kb python module not found
📚 Knowledge Base Results (1 found):

1. NO MODULE NAMED
   Install the Python module with `pip install --user <module>` 
   or use a virtual environment with `python -m venv venv`
```

### Example 3: Model Switching

```bash
aria> /models
⏳ Fetching available models...

📊 Available Models:

  [✓] gemma-4-26b-a4b-it
  [ ] gemma-4-2b-it
  [ ] gemma-4-4b-it
  [ ] gemma-4-31b-it
```

## 🎓 Termux Development Tips

### Common Issues

| Issue | Solution |
|-------|----------|
| `command not found` | `pkg install <package>` |
| `permission denied` | Use `termux-setup-storage` or `tsu` |
| `gcc: error` | Termux uses clang: `pkg install clang` |
| `port already in use` | Use ports >= 1024 |
| `No module named` | `pip install --user <module>` |

### Useful Commands

```bash
# Update packages
pkg update && pkg upgrade

# Change package mirror (if 404 errors)
termux-change-repo

# Setup storage access
termux-setup-storage

# Install build tools
pkg install build-essential

# Get temporary root
tsu

# Check battery status
termux-battery-status

# Take screenshot
termux-camera-photo -c 0 screenshot.jpg
```

## 🔐 Security Considerations

- API key is stored locally in `~/.aria/config.json`
- Guardian mode is enabled by default
- Watch mode only analyzes shell output, doesn't execute without confirmation
- Auto-fix commands are limited to safe operations
- All API calls use HTTPS

## 📦 Dependencies

- `google-generativeai>=0.3.0`: Google AI API client
- `rich>=13.0.0`: Beautiful terminal output
- `click>=8.0.0`: CLI framework
- `pydantic>=2.0.0`: Data validation
- `python-dotenv>=1.0.0`: Environment variable management

## 🧪 Testing

```bash
# Run tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_command_system.py

# Run with coverage
python -m pytest --cov=aria tests/
```

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🐛 Bug Reports

Found a bug? Please open an issue with:

- Description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Termux version and Android version
- ARIA version

## 💡 Feature Requests

Have an idea? Open an issue with:

- Feature description
- Use case
- Proposed implementation (optional)

## 📞 Support

- **Documentation**: Check README and inline code comments
- **Knowledge Base**: Use `/kb <query>` in ARIA
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

## 🎉 Acknowledgments

- Google Gemma 4 Challenge
- Termux community
- Rich library for beautiful terminal UI
- Google AI Studio for free API access

## 📊 Hackathon Submission

This project is submitted for the **Google Gemma 4 Challenge (DEV.to)** with:

- ✅ Production-grade Python implementation
- ✅ Multi-agent architecture with self-healing capabilities
- ✅ Intentional use of Gemma 4 via Google AI Studio
- ✅ Niche, authentic solution for Termux developers
- ✅ Beautiful UI and excellent usability
- ✅ One-command installation
- ✅ MIT license
- ✅ Working code tested on Termux

---

**ARIA** — Making Termux development faster, smarter, and more beautiful. 🚀

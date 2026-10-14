# Changelog

All notable changes to ARIA will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Multi-provider support: Google AI Studio, OpenRouter, and NVIDIA NIM (2026-05-21)
- Animated logo and a local-first auto-repair agent (`repair_agent.py`) (2026-05-21)
- API keys are validated on save with a real auth check, not just an endpoint ping (2026-05-28)

### Changed

- Google provider falls back to plain HTTPS (stdlib `urllib`) when `google-generativeai` isn't installed, so it works on Termux setups where the SDK won't install. The SDK is still used when present (2026-10-14)
- When a provider can't initialize, the reason is now reported instead of `None` (2026-10-14)
- Trimmed dependencies: `rich` is the only required package, and `google-generativeai` is optional (Google provider only) (2026-05-28)
- Config schema aligned between the installer and the runtime (2026-05-28)
- `install.sh` no longer hardcodes the wrong directory name (2026-05-28)
- README rewritten twice: direct tone (2026-05-28), then for the post-hackathon phase (2026-10-14)
- `CONTRIBUTING.md` and package metadata corrected to point at this repository (2026-10-14)

### Fixed

- Google provider was unusable without `google-generativeai`: `/model list` returned nothing and `/ask` failed ([#2](https://github.com/Alex72-py/aria-termux/issues/2)) (2026-10-14)
- Stuck spinner and text wrapping on small screens (2026-05-28)
- Blocking confirmation prompts removed from threaded commands (2026-05-28)

### Removed

- Streaming mode, because non-streaming is more reliable on mobile connections (2026-05-28)

## [1.0.0] - 2026-05-24

### Added

- **Core Application**
  - Main ARIA application with interactive CLI
  - Slash command system with dynamic command registration
  - Configuration management with JSON storage
  - Comprehensive logging system

- **API Integration**
  - Google AI Studio API client with self-healing capabilities
  - Automatic model detection and switching
  - Exponential backoff retry logic
  - Graceful fallback to offline mode
  - Support for multiple Gemma 4 models

- **Guardian Safety Layer**
  - Risk scoring algorithm (0-100)
  - Dangerous pattern detection
  - User confirmation prompts for high-risk operations
  - Configurable safety mode

- **Watch Mode**
  - Real-time shell output monitoring
  - Error pattern detection
  - Auto-fix command execution
  - Integration with knowledge base

- **Knowledge Base**
  - 100+ Termux-specific entries
  - Fuzzy search matching
  - Category-based organization
  - Error patterns, package management, proot-distro, Android bridge

- **Rich Terminal UI**
  - ASCII art boot sequence
  - Spinner animations (neural, scan, pulse)
  - Syntax highlighting for code blocks
  - Color-coded output (error, success, info, warning)
  - Table display for structured data
  - Progress indicators

- **Commands**
  - `/ask <query>` - Ask the AI a question
  - `/fix <error>` - Analyze and fix errors
  - `/watch` - Enable watch mode
  - `/models` - List available models
  - `/config` - Run configuration wizard
  - `/kb <query>` - Search knowledge base
  - `/history` - Show command history
  - `/help` - Display help menu
  - `/exit` - Exit ARIA

- **CLI Interface**
  - Interactive REPL mode
  - Command-line arguments support
  - Configuration wizard
  - Help system

- **Testing**
  - Comprehensive test suite (26 tests)
  - Tests for API client, command system, knowledge base, Guardian, and config
  - Pytest integration with coverage reporting

- **Documentation**
  - Comprehensive README with installation and usage
  - Contributing guidelines
  - Architecture documentation
  - Inline code documentation with docstrings
  - Examples and use cases

- **Project Setup**
  - Python package with setuptools
  - Requirements.txt with all dependencies
  - MIT License
  - .gitignore for version control

### Features

- **Self-Healing API**: Automatically detects wrong models, fetches available ones, and retries
- **Offline Mode**: Full offline functionality with embedded knowledge base
- **Zero Credit Card**: Works with Google AI Studio free tier (15 req/min, 1500 req/day)
- **Termux Native**: Deep knowledge of Termux constraints and best practices
- **Beautiful UI**: Cinematic boot sequence and rich terminal output
- **Safe Operations**: Guardian mode prevents dangerous commands

### Technical Details

- **Language**: Python 3.8+
- **Platform**: Termux/Android, Linux
- **API**: Google Generative AI (Gemma 4)
- **UI Framework**: Rich
- **CLI Framework**: Click
- **Testing**: Pytest

### Known Limitations

- Requires Google AI Studio API key (free tier available)
- Watch mode requires shell output monitoring capability
- Some Android versions may have permission restrictions
- API rate limits apply (free tier: 15 req/min, 1500 req/day)

## Roadmap

The planned-features list that used to live here was written during the hackathon and is out of date. Current work is tracked in [issues](https://github.com/Alex72-py/aria-termux/issues).

---

## How to Report Issues

Found a bug? Please open an issue on GitHub with:
- Description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Termux version, Android version, Python version)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

**ARIA** — Making Termux development faster, smarter, and more beautiful. 🚀

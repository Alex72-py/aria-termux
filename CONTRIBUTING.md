# Contributing to ARIA

Thank you for your interest in contributing to ARIA! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on the code, not the person
- Help others learn and grow

## Getting Started

### Prerequisites

- Python 3.8+
- Git
- Termux (for testing on actual device)

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/Alex72-py/aria-termux.git
cd aria-termux

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -r requirements.txt
pip install -e .
pip install pytest pytest-cov

# Run tests
pytest tests/
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Follow PEP 8 style guide
- Add docstrings to functions
- Add type hints where possible
- Keep functions focused and testable

### 3. Write Tests

- Add tests for new functionality
- Run tests: `pytest tests/`
- Aim for >80% code coverage

### 4. Commit Changes

```bash
git add .
git commit -m "feat: Add your feature description"
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

## Code Style

### Python Style Guide

- Follow PEP 8
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use meaningful variable names

### Example

```python
def analyze_error(self, error_output: str) -> dict:
    """
    Analyze error and provide suggestions.
    
    Args:
        error_output: Error output from shell
        
    Returns:
        Analysis dictionary with suggestions
    """
    # Implementation here
    pass
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_api_client.py

# Run with coverage
pytest --cov=aria tests/
```

### Writing Tests

```python
def test_feature_name():
    """Test description."""
    # Setup
    obj = MyClass()
    
    # Execute
    result = obj.method()
    
    # Assert
    assert result == expected_value
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings to all public functions
- Include examples in docstrings
- Update CHANGELOG.md for significant changes

## Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (no logic change)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Build, dependencies, etc.

### Example

```
feat: Add watch mode for auto-error detection

Implement real-time shell monitoring that detects errors
and suggests fixes from knowledge base.

Closes #123
```

## Pull Request Process

1. Update README.md with any new features
2. Update version number in setup.py
3. Ensure all tests pass
4. Request review from maintainers
5. Address feedback and re-request review
6. Merge after approval

## Reporting Bugs

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command...
2. See error...

**Expected behavior**
What should happen instead.

**Environment**
- OS: [e.g. Termux, Ubuntu]
- Python version: [e.g. 3.8, 3.11]
- ARIA version: [e.g. 1.0.0]
- Provider and model: [e.g. openrouter, gemma-4-31b-it]

**Additional context**
Any other relevant information.
```

## Feature Requests

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
Describe the problem.

**Describe the solution you'd like**
Clear description of the desired feature.

**Describe alternatives you've considered**
Other solutions or features you've considered.

**Additional context**
Any other relevant information.
```

## Project Structure

```
aria-termux/
├── aria/                  # Main package
│   ├── __init__.py
│   ├── main.py            # Main loop, command dispatch, setup wizard
│   ├── api_client.py      # Provider abstraction (Google, OpenRouter, NVIDIA NIM)
│   ├── command_system.py  # Slash command registry and parsing
│   ├── config.py          # JSON config (~/.aria/config.json)
│   ├── guardian.py        # Risk scoring and confirmation prompts
│   ├── knowledge_base.py  # Offline Termux troubleshooting data
│   ├── repair_agent.py    # Local-first fix planning
│   ├── watch_mode.py      # Cross-session error capture
│   ├── ui.py              # Terminal UI components
│   └── utils.py           # Utilities
├── tests/                 # Test suite
├── install.sh             # Installer
├── run_aria.py            # Run without installing
├── setup.py               # Package setup
├── ARCHITECTURE.md        # Design overview
├── CHANGELOG.md           # Notable changes
├── README.md              # User documentation
├── CONTRIBUTING.md        # This file
└── LICENSE                # MIT License
```

## Areas for Contribution

- **Knowledge Base**: Add more Termux error patterns and solutions
- **Commands**: Implement new slash commands
- **UI**: Improve terminal UI and animations
- **Performance**: Optimize API calls and response times
- **Documentation**: Improve guides and examples
- **Testing**: Increase test coverage
- **Platforms**: Test and fix issues on different Android versions
- **Providers**: Make the Google provider work without `google-generativeai` (see [#2](https://github.com/Alex72-py/aria-termux/issues/2))

## Questions?

- Check [existing issues](https://github.com/Alex72-py/aria-termux/issues)
- Open a new issue if yours isn't covered
- Review ARCHITECTURE.md and the code comments

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to ARIA! 🚀

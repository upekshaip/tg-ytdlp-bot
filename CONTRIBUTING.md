# 🤝 Contributing to tg-ytdlp-bot

Thank you for your interest in contributing to tg-ytdlp-bot! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#-code-of-conduct)
- [Getting Started](#-getting-started)
- [Development Setup](#-development-setup)
- [Contributing Guidelines](#-contributing-guidelines)
- [Pull Request Process](#-pull-request-process)
- [Issue Guidelines](#-issue-guidelines)
- [Code Style](#-code-style)
- [Testing](#-testing)
- [Documentation](#-documentation)
- [Release Process](#-release-process)

## 🤝 Code of Conduct

This project and everyone participating in it is governed by our commitment to creating a welcoming and inclusive environment. By participating, you agree to:

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on what's best for the community
- Show empathy towards other community members
- Accept constructive criticism gracefully
- Use welcoming and inclusive language

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** installed
- **Git** installed
- **Telegram Bot Token** (for testing)
- **Basic understanding** of Python, Pyrogram, and yt-dlp
- **Familiarity** with Telegram Bot API

### Areas Where We Need Help

- 🐛 **Bug fixes** and issue resolution
- ✨ **New features** and enhancements
- 📚 **Documentation** improvements
- 🧪 **Testing** and quality assurance
- 🌍 **Internationalization** (i18n)
- 🎨 **UI/UX** improvements
- 🔧 **Performance** optimizations

## 🛠️ Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/tg-ytdlp-bot.git
cd tg-ytdlp-bot

# Add upstream remote
git remote add upstream https://github.com/chelaxian/tg-ytdlp-bot.git
```

### 2. Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # If available
```

### 3. Configuration

```bash
# Copy configuration template
cp CONFIG/_config.py CONFIG/config.py

# Edit configuration with your test bot credentials
nano CONFIG/config.py
```

### 4. Test Your Setup

```bash
# Run the bot to ensure everything works
python3 magic.py
```

## 📝 Contributing Guidelines

### Types of Contributions

#### 🐛 Bug Reports

When reporting bugs, please include:

- **Clear description** of the issue
- **Steps to reproduce** the problem
- **Expected behavior** vs actual behavior
- **Environment details** (OS, Python version, etc.)
- **Relevant logs** and error messages
- **Screenshots** if applicable

#### ✨ Feature Requests

For new features, please provide:

- **Clear description** of the proposed feature
- **Use case** and motivation
- **Proposed implementation** approach
- **Potential impact** on existing functionality
- **Backward compatibility** considerations

#### 🔧 Code Contributions

- **Small, focused changes** are preferred
- **One feature/fix per pull request**
- **Follow existing code style** and patterns
- **Add tests** for new functionality
- **Update documentation** as needed

### Development Workflow

#### 1. Create a Branch

```bash
# Update your fork
git fetch upstream
git checkout main
git merge upstream/main

# Create a new branch for your feature
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

#### 2. Make Changes

- Write clean, readable code
- Follow the existing code style
- Add comments for complex logic
- Test your changes thoroughly

#### 3. Commit Changes

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "Add: New feature for user authentication"
# or
git commit -m "Fix: Resolve issue with video download timeout"
```

**Commit Message Format:**
- `Add:` for new features
- `Fix:` for bug fixes
- `Update:` for improvements
- `Remove:` for deletions
- `Refactor:` for code refactoring
- `Docs:` for documentation changes

#### 4. Push and Create PR

```bash
# Push your branch
git push origin feature/your-feature-name

# Create a Pull Request on GitHub
```

## 🔄 Pull Request Process

### Before Submitting

- [ ] **Test your changes** thoroughly
- [ ] **Update documentation** if needed
- [ ] **Add tests** for new functionality
- [ ] **Check code style** and formatting
- [ ] **Ensure no conflicts** with main branch
- [ ] **Update CHANGELOG.md** if applicable

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tested locally
- [ ] Added unit tests
- [ ] Tested with real bot

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)

## Screenshots (if applicable)
Add screenshots to help explain your changes

## Additional Notes
Any additional information for reviewers
```

### Review Process

1. **Automated checks** must pass
2. **Code review** by maintainers
3. **Testing** by maintainers
4. **Approval** and merge

## 🐛 Issue Guidelines

### Before Creating an Issue

1. **Search existing issues** to avoid duplicates
2. **Check if it's already fixed** in the latest version
3. **Gather relevant information** about the problem

### Issue Templates

#### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g. Ubuntu 20.04]
- Python version: [e.g. 3.10.0]
- Bot version: [e.g. 1.0.0]

**Additional context**
Any other context about the problem.
```

#### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Additional context**
Any other context or screenshots about the feature request.
```

## 🎨 Code Style

### Python Style Guide

- Follow **PEP 8** guidelines
- Use **type hints** where appropriate
- Write **docstrings** for functions and classes
- Use **meaningful variable names**
- Keep **functions small** and focused

### Example Code Style

```python
def download_video(url: str, user_id: int, quality: str = "best") -> bool:
    """
    Download video from URL with specified quality.
    
    Args:
        url: Video URL to download
        user_id: Telegram user ID
        quality: Video quality preference
        
    Returns:
        bool: True if download successful, False otherwise
        
    Raises:
        ValueError: If URL is invalid
        ConnectionError: If download fails
    """
    if not url or not url.startswith(('http://', 'https://')):
        raise ValueError("Invalid URL provided")
    
    try:
        # Implementation here
        return True
    except Exception as e:
        logger.error(f"Download failed for user {user_id}: {e}")
        return False
```

### File Organization

```
tg-ytdlp-bot/
├── COMMANDS/          # Bot command handlers
├── CONFIG/           # Configuration files
├── DOWN_AND_UP/      # Download and upload logic
├── HELPERS/          # Utility functions
├── URL_PARSERS/      # URL parsing and extraction
├── magic.py          # Main bot file
├── requirements.txt  # Dependencies
└── README.md         # Documentation
```

## 🧪 Testing

### Testing Guidelines

- **Write tests** for new functionality
- **Test edge cases** and error conditions
- **Mock external dependencies** when possible
- **Test with real data** when safe

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_commands.py

# Run with coverage
python -m pytest --cov=.
```

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch
from COMMANDS.args_cmd import get_user_ytdlp_args

class TestArgsCommand:
    def test_get_user_ytdlp_args_success(self):
        """Test successful retrieval of user yt-dlp arguments."""
        user_id = 12345
        url = "https://youtube.com/watch?v=test"
        
        result = get_user_ytdlp_args(user_id, url)
        
        assert isinstance(result, dict)
        assert "format" in result
    
    def test_get_user_ytdlp_args_invalid_user(self):
        """Test handling of invalid user ID."""
        with pytest.raises(ValueError):
            get_user_ytdlp_args(-1, "https://example.com")
```

## 📚 Documentation

### Documentation Standards

- **Update README.md** for user-facing changes
- **Add docstrings** to new functions and classes
- **Update inline comments** for complex logic
- **Create examples** for new features

### Documentation Types

1. **User Documentation** (README.md)
2. **API Documentation** (docstrings)
3. **Developer Documentation** (this file)
4. **Configuration Documentation** (config comments)

## 🚀 Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality (backward compatible)
- **PATCH** version for bug fixes (backward compatible)

### Release Checklist

- [ ] **Update version** in config files
- [ ] **Update CHANGELOG.md** with new features/fixes
- [ ] **Run full test suite**
- [ ] **Update documentation**
- [ ] **Create release notes**
- [ ] **Tag release** in Git

## 🆘 Getting Help

### Communication Channels

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Telegram**: [@tg_ytdlp](https://t.me/tg_ytdlp) for community support

### Resources

- **PyroTGFork Documentation**: https://telegramplayground.github.io/pyrogram/
- **yt-dlp Documentation**: https://github.com/yt-dlp/yt-dlp
- **Telegram Bot API**: https://core.telegram.org/bots/api

## 🙏 Recognition

Contributors will be recognized in:

- **README.md** acknowledgments
- **Release notes** for significant contributions
- **GitHub contributors** page

## 📄 License

By contributing to tg-ytdlp-bot, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

**Thank you for contributing to tg-ytdlp-bot! 🎉**

Your contributions help make this project better for everyone. If you have any questions about contributing, please don't hesitate to ask!

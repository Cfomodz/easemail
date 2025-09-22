# Contributing to Email Triage System

Thank you for your interest in contributing to the Email Triage System! This document provides guidelines for contributing to the project.

## 🚀 Quick Start for Contributors

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/email-triage-system.git
   cd email-triage-system
   ```
3. **Set up development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## 🛠️ Development Setup

### Prerequisites
- Python 3.8+
- Gmail account with API access
- OpenAI API key
- ElevenLabs API key (optional)

### Configuration
1. Copy `triage_data/config.json.example` to `triage_data/config.json`
2. Add your API keys to the config file
3. Follow `docs/gmail_oauth_setup.md` for Gmail setup

### Running Tests
```bash
# Test TTS functionality
python tests/test_async_tts.py

# Test interruption system
python tests/test_interruption.py

# Run the main system
python run_triage.py
```

## 📝 Code Style

### Python Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings for all public functions and classes
- Keep functions focused and small (< 50 lines when possible)

### Naming Conventions
- Classes: `PascalCase` (e.g., `EmailTriageSystem`)
- Functions/variables: `snake_case` (e.g., `get_user_decision`)
- Constants: `UPPER_CASE` (e.g., `MAX_BATCH_SIZE`)
- Private methods: `_snake_case` (e.g., `_handle_opt_out`)

### Documentation
- Update README.md for user-facing changes
- Update CHANGELOG.md for all changes
- Add inline comments for complex logic
- Update docstrings when changing function signatures

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment information**:
   - Python version
   - Operating system
   - Relevant package versions

2. **Steps to reproduce**:
   - Clear, numbered steps
   - Expected vs actual behavior
   - Any error messages or logs

3. **Configuration** (sanitized):
   - Relevant config.json settings
   - Any custom modifications

## ✨ Feature Requests

For new features, please:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** clearly
3. **Explain the expected behavior**
4. **Consider implementation complexity**
5. **Discuss breaking changes** if any

## 🔧 Pull Request Process

### Before Submitting
1. **Test your changes** thoroughly
2. **Update documentation** as needed
3. **Add tests** for new functionality
4. **Check code style** and formatting
5. **Update CHANGELOG.md**

### Pull Request Guidelines
1. **Create a feature branch** from `main`
2. **Use descriptive commit messages**:
   ```
   feat: add bulk archive functionality for same sender/subject
   fix: resolve TTS interruption timing issue
   docs: update installation instructions
   ```
3. **Keep PRs focused** - one feature/fix per PR
4. **Include tests** for new functionality
5. **Update documentation** for user-facing changes

### Commit Message Format
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

## 🏗️ Architecture Overview

### Core Components
- **`email_triage_system.py`**: Main triage logic and user interface
- **`gmail_oauth_client.py`**: Gmail API integration
- **`tts_manager.py`**: Text-to-speech handling
- **`opt_out_manager.py`**: Opt-out request management

### Key Design Principles
1. **Single Responsibility**: Each module has a clear, focused purpose
2. **Loose Coupling**: Components interact through well-defined interfaces
3. **User Experience**: Prioritize efficiency and ease of use
4. **Extensibility**: Design for future enhancements

### Data Flow
1. Gmail API fetches emails
2. AI classifies emails using OpenAI
3. User reviews and makes decisions
4. Actions are applied back to Gmail
5. Preferences are stored for learning

## 🧪 Testing Guidelines

### Test Categories
1. **Unit Tests**: Individual function testing
2. **Integration Tests**: Component interaction testing
3. **User Interface Tests**: TTS and input handling
4. **API Tests**: Gmail and OpenAI integration

### Test Structure
```python
def test_function_name():
    # Arrange
    setup_test_data()
    
    # Act
    result = function_under_test()
    
    # Assert
    assert result == expected_value
```

## 📚 Documentation Standards

### Code Documentation
- Use clear, descriptive function names
- Add type hints for all parameters and return values
- Include docstrings with examples for complex functions
- Comment non-obvious logic and business rules

### User Documentation
- Keep README.md up to date
- Provide clear installation instructions
- Include usage examples
- Document configuration options

## 🚀 Release Process

1. **Update version** in relevant files
2. **Update CHANGELOG.md** with new features and fixes
3. **Create release branch** from `main`
4. **Test release candidate** thoroughly
5. **Create GitHub release** with release notes
6. **Merge to main** and tag release

## 🤝 Community Guidelines

### Be Respectful
- Use inclusive language
- Be patient with newcomers
- Provide constructive feedback
- Help others learn and grow

### Communication
- Use GitHub issues for bug reports and feature requests
- Use pull request discussions for code review
- Be clear and concise in communications
- Ask questions if something is unclear

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Documentation**: Check docs/ directory first
- **Code Examples**: See tests/ directory for usage examples

## 🏆 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- GitHub contributor graphs and statistics

Thank you for contributing to make email management better for everyone! 🎉

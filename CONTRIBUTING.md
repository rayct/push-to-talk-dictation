# Contributing to Push-to-Talk Dictation

Thank you for your interest in contributing! This guide will help you get started.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/push-to-talk-dictation.git
   cd push-to-talk-dictation
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b add/your-feature-name
   ```

## Development Setup

1. **Install dependencies**:
   ```bash
   ./install.sh
   source venv/bin/activate
   ```

2. **Run tests**:
   ```bash
   python3 test_components.py
   ```

3. **Check system requirements**:
   ```bash
   python3 sysinfo_check.py
   ```

## Code Style

- Use descriptive variable and function names
- Add docstrings to functions and classes
- Keep lines under 100 characters where practical
- Follow PEP 8 style guidelines

## Making Changes

### Core Implementation

If modifying core modules (`dictation_daemon.py`, `audio_capture.py`, etc.):
1. Update docstrings
2. Add error handling
3. Test thoroughly with `test_components.py`
4. Update relevant documentation

### Configuration

If changing `config.yaml`:
1. Ensure backward compatibility
2. Document new options in README.md
3. Add examples to config.yaml comments

### Documentation

If updating documentation:
1. Keep examples up to date
2. Verify all commands work as documented
3. Update table of contents if adding new sections

## Testing

Before submitting a PR:

```bash
# Run component tests
python3 test_components.py

# Check system requirements
python3 sysinfo_check.py

# Test installation script (in a test directory)
bash install.sh

# Verify manual daemon operation
~/.local/bin/push-to-talk-dict --list-windows
```

## Submitting a PR

1. **Push your branch** to your fork:
   ```bash
   git push origin add/your-feature-name
   ```

2. **Create a Pull Request** with:
   - Clear title describing the change
   - Description of what was changed and why
   - Reference to any related issues
   - Testing notes if applicable

3. **Include in your PR description**:
   - Problem being solved
   - How the solution works
   - Any breaking changes
   - Testing performed

## PR Guidelines

- Keep PRs focused on a single feature or fix
- Update documentation if user-facing changes
- Ensure .gitignore includes venv and cache files
- Reference issue numbers if applicable
- Be responsive to review feedback

## Code Review Process

- At least one review required before merge
- CI checks must pass (if enabled)
- Maintainers may request changes for:
  - Code quality
  - Documentation clarity
  - Test coverage
  - Breaking changes mitigation

## Issues

Found a bug? Have a feature request? Create an issue with:
- Clear title
- Description of the problem/request
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- System info (if relevant)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

## Questions?

Feel free to:
- Open an issue with your question
- Reference this guide in your discussions
- Check existing issues for similar questions

Thank you for contributing! 🎤✨

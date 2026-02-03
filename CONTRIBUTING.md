# Contributing to Open-ALO

Thank you for your interest in contributing to Open-ALO! 🎉

## Getting Started

1. **Fork the repository**
   ```bash
   git clone https://github.com/JonyBepary/Open-ALO.git
   cd Open-ALO
   ```

2. **Set up development environment**
   ```bash
   # Install system dependencies
   sudo apt install \
       python3-gi \
       python3-gi-cairo \
       gir1.2-gst-plugins-base-1.0 \
       gstreamer1.0-pipewire \
       xdg-desktop-portal \
       xdg-desktop-portal-gnome

   # Install package in development mode
   pip install -e .
   ```

3. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Code Style

- Follow **PEP 8** naming conventions
- Use **type hints** on all public APIs
- Add **docstrings** to all public classes/functions
- Keep functions focused and well-named

See [CODE_STANDARDS.md](CODE_STANDARDS.md) for details.

### Testing

```bash
# Run structure tests
cd tests
python test_structure.py

# Test imports
python -c "from open_alo_core import UnifiedRemoteDesktop; print('✅')"
```

### Building

```bash
python -m build
```

## Contribution Workflow

1. **Make your changes**
   - Write clean, documented code
   - Follow existing patterns
   - Add tests for new features

2. **Test locally**
   ```bash
   python test_structure.py
   python -m build
   ```

3. **Commit with clear messages**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

   Use conventional commits:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation
   - `refactor:` - Code refactoring
   - `test:` - Test updates

4. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub

## What to Contribute

### Good First Issues
- Documentation improvements
- Example scripts
- Bug fixes
- Test coverage

### Feature Ideas
- Support for more window managers
- Additional input methods
- Performance optimizations
- Platform-specific enhancements

## Code Review Process

1. CI/CD runs automatically on PRs
2. Maintainers review code
3. Address feedback
4. Once approved, PR is merged

## Questions?

- Open an [Issue](https://github.com/JonyBepary/Open-ALO/issues)
- Check existing [Discussions](https://github.com/JonyBepary/Open-ALO/discussions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

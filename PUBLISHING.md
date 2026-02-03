# Publishing Guide for open-alo-core

## Prerequisites

```bash
# Install build tools
pip install build twine
```

## Build Package

```bash
cd open_alo_core

# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build distribution
python -m build

# Verify build
ls -lh dist/
```

This creates:
- `dist/open-alo-core-0.1.0.tar.gz` - Source distribution
- `dist/open-alo-core-0.1.0-py3-none-any.whl` - Wheel distribution

## Test Package Locally

```bash
# Install in virtual environment
python -m venv test_env
source test_env/bin/activate
pip install dist/open-alo-core-0.1.0-py3-none-any.whl

# Test import
python -c "from open_alo_core import UnifiedRemoteDesktop; print('✅ Import successful')"

# Deactivate
deactivate
```

## Publish to TestPyPI (Recommended First)

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --no-deps open-alo-core

# If successful, proceed to production PyPI
```

## Publish to PyPI

```bash
# Upload to production PyPI
python -m twine upload dist/*

# Verify on PyPI
# https://pypi.org/project/open-alo-core/
```

## Post-Publication

```bash
# Install from PyPI
pip install open-alo-core

# Test
python -c "from open_alo_core import UnifiedRemoteDesktop; print('✅ PyPI package works')"
```

## Version Bumping

When releasing new version:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Update `__version__` in `src/open_alo_core/__init__.py`
4. Create git tag: `git tag v0.1.1`
5. Push tag: `git push origin v0.1.1`
6. Rebuild and publish

## PyPI Credentials

### Option 1: API Token (Recommended)

```bash
# Create token at https://pypi.org/manage/account/token/
# Add to ~/.pypirc

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcC...

[testpypi]
username = __token__
password = pypi-AgENdGVzdC5weXBpLm9yZ...
```

### Option 2: Username/Password

```bash
# Enter credentials when prompted by twine
python -m twine upload dist/*
# Username: your_username
# Password: your_password
```

## Checklist Before Publishing

- [ ] All tests pass
- [ ] README.md is up to date
- [ ] API_REFERENCE.md is complete
- [ ] CHANGELOG.md documents changes
- [ ] Version bumped in all locations
- [ ] LICENSE file included
- [ ] Built successfully: `python -m build`
- [ ] Tested locally from wheel
- [ ] Tested on TestPyPI
- [ ] Git tagged with version
- [ ] GitHub URLs updated (replace `yourusername`)

## Troubleshooting

### Build Fails

```bash
# Check pyproject.toml syntax
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"

# Verify package structure
tree src/
```

### Upload Fails

```bash
# Check credentials
cat ~/.pypirc

# Verify package name not taken
# https://pypi.org/project/open-alo-core/
```

### Import Fails After Install

```bash
# Check installed files
pip show -f open-alo-core

# Verify dependencies
pip install PyGObject>=3.40.0
```

## Important Notes

1. **Package name**: `open-alo-core` (with hyphens for PyPI)
2. **Import name**: `open_alo_core` (with underscores for Python)
3. **Minimum Python**: 3.10+
4. **System dependencies**: Must be installed separately (PyGObject, GStreamer, PipeWire)
5. **GitHub URLs**: Update before publishing!

## Resources

- PyPI: https://pypi.org/
- TestPyPI: https://test.pypi.org/
- Python Packaging Guide: https://packaging.python.org/
- Twine Documentation: https://twine.readthedocs.io/

# CI/CD Setup Guide for Open-ALO

## Overview

The project uses **GitHub Actions** for automated CI/CD:

- **CI**: Tests on every push/PR
- **TestPyPI**: Auto-publish on push to `main`
- **PyPI**: Auto-publish on tagged releases

## Setup Steps

### 1. Enable GitHub Actions (Already Done ✅)

GitHub Actions workflows are in `.github/workflows/`:
- `ci.yml` - Run tests on every push
- `publish.yml` - Build and publish to PyPI

### 2. Configure PyPI Publishing

#### Option A: Trusted Publishing (Recommended - No tokens needed!)

**For PyPI:**
1. Go to https://pypi.org/manage/account/publishing/
2. Add a new pending publisher:
   - **PyPI Project Name**: `open-alo-core`
   - **Owner**: `JonyBepary`
   - **Repository name**: `Open-ALO`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`
3. Click "Add"

**For TestPyPI:**
1. Go to https://test.pypi.org/manage/account/publishing/
2. Add pending publisher:
   - **PyPI Project Name**: `open-alo-core`
   - **Owner**: `JonyBepary`
   - **Repository name**: `Open-ALO`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `testpypi`

#### Option B: API Tokens (Alternative)

1. Create PyPI token: https://pypi.org/manage/account/token/
2. Add to GitHub Secrets:
   - Go to `https://github.com/JonyBepary/Open-ALO/settings/secrets/actions`
   - Add `PYPI_API_TOKEN` with your token
   - Add `TEST_PYPI_API_TOKEN` for TestPyPI

Then update `.github/workflows/publish.yml` to use tokens instead of OIDC.

### 3. Create GitHub Environments (Optional but Recommended)

1. Go to `https://github.com/JonyBepary/Open-ALO/settings/environments`
2. Create two environments:
   - **testpypi** - For test releases
   - **pypi** - For production releases
3. Add protection rules (optional):
   - Required reviewers
   - Wait timer
   - Deployment branches (main or tags only)

## Workflow Details

### CI Workflow (`ci.yml`)

**Triggers**: Push to main/develop, PRs

**Jobs**:
1. **Lint** - Code quality checks (black, isort, flake8)
2. **Test Matrix** - Test on Python 3.8-3.12
3. **Build Check** - Verify package builds correctly

### Publish Workflow (`publish.yml`)

**Triggers**:
- Push to `main` → TestPyPI
- Tagged release (`v*`) → PyPI

**Jobs**:
1. **Test** - Run tests
2. **Build** - Build distributions (wheel + sdist)
3. **Publish TestPyPI** - On push to main
4. **Publish PyPI** - On version tags
5. **Create Release** - GitHub release with artifacts

## Usage

### Development Workflow

```bash
# 1. Make changes
git checkout -b feature/my-feature
# ... make changes ...

# 2. Test locally
cd open_alo_core
python test_structure.py
python -m build

# 3. Commit and push
git add .
git commit -m "feat: add new feature"
git push origin feature/my-feature

# 4. Create PR
# CI runs automatically on PR
```

### Release Workflow

```bash
# 1. Update version
# Edit open_alo_core/pyproject.toml
# Edit open_alo_core/src/open_alo_core/__init__.py

# 2. Commit version bump
git add .
git commit -m "chore: bump version to 0.1.1"
git push origin main

# 3. Create and push tag
git tag v0.1.1
git push origin v0.1.1

# 4. GitHub Actions automatically:
#    - Runs tests
#    - Builds package
#    - Publishes to PyPI
#    - Creates GitHub Release
```

### Manual Testing Before Release

```bash
# Test on TestPyPI first
git push origin main

# Wait for GitHub Actions to publish to TestPyPI
# Then test installation:
pip install --index-url https://test.pypi.org/simple/ --no-deps open-alo-core

# If successful, create version tag for production release
```

## Monitoring

- **Actions**: https://github.com/JonyBepary/Open-ALO/actions
- **PyPI**: https://pypi.org/project/open-alo-core/
- **TestPyPI**: https://test.pypi.org/project/open-alo-core/

## Troubleshooting

### Publish Fails with "Permission Denied"

**Solution**: Set up Trusted Publishing (see Option A above) or add API tokens to secrets.

### Tests Fail in CI

**Solution**: Check workflow logs at https://github.com/JonyBepary/Open-ALO/actions

Common issues:
- Missing system dependencies
- Python version compatibility
- Import errors

### Package Already Exists on PyPI

**Solution**:
- You can't re-upload same version
- Bump version in `pyproject.toml`
- Create new tag: `git tag v0.1.1`

### TestPyPI Upload Succeeds but PyPI Fails

**Solution**: Check that you've set up PyPI publishing separately from TestPyPI.

## Security Notes

1. **Never commit tokens** to repository
2. Use **GitHub Secrets** for credentials
3. **Trusted Publishing** is more secure than tokens
4. Review all **dependency updates** before merging
5. Enable **branch protection** on main branch

## Quick Reference

```bash
# Rebuild package
cd open_alo_core && rm -rf dist/ build/ *.egg-info && python -m build

# Tag release
git tag v0.1.1 && git push origin v0.1.1

# View workflow runs
gh run list --repo JonyBepary/Open-ALO

# Cancel workflow
gh run cancel <run-id>
```

---

**Status**: ✅ CI/CD configured and ready!

**Next Steps**:
1. Set up PyPI Trusted Publishing (see Option A)
2. Push code to GitHub
3. Test workflow by pushing to main
4. Create first release with tag `v0.1.0`

# Release Guide

This document explains how to create a new release and publish to PyPI.

## Prerequisites

1. Make sure you have push access to the repository
2. Ensure all tests are passing on the main branch
3. Update the version number in `pyproject.toml`

## Creating a Release

### 1. Update Version

Edit `pyproject.toml` and update the version:

```toml
[tool.poetry]
name = "bdns-api"
version = "0.2.0"  # Update this
```

### 2. Create Release on GitHub

1. Go to the repository on GitHub
2. Click on "Releases" → "Create a new release"
3. Create a new tag (e.g., `v0.2.0`)
4. Set the release title (e.g., `v0.2.0`)
5. Add release notes describing changes
6. Click "Publish release"

### 3. Automatic Publishing

Once you create a GitHub release:

1. GitHub Actions will automatically run the CI/CD pipeline
2. All tests will be executed
3. The package will be built
4. If everything passes, it will be automatically published to PyPI

## Manual Publishing (if needed)

If you need to publish manually:

```bash
# Build the package
poetry build

# Publish to PyPI (requires PyPI token)
poetry publish
```

## PyPI Setup

The repository is configured for trusted publishing to PyPI. The workflow uses OpenID Connect (OIDC) for secure authentication without storing secrets.

If you need to set up PyPI publishing:

1. Go to [PyPI](https://pypi.org/manage/account/publishing/)
2. Add a new trusted publisher:
   - PyPI Project Name: `bdns-api`
   - Owner: `cruzlorite`
   - Repository name: `bdns-api`
   - Workflow name: `ci-cd.yml`
   - Environment name: `pypi`

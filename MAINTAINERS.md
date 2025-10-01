# Maintainer Guide

This document contains information for official maintainers of the Energy Dependency Inspector project.

## Publishing to PyPI

Official documentation: <https://packaging.python.org/en/latest/tutorials/packaging-projects/>

To publish a new version to PyPI, follow these steps:

1. **Bump the version** in `pyproject.toml`

2. **Build the package:**

   ```sh
   # Install/upgrade build tools
   python3 -m pip install --upgrade build

   # Build the distribution packages
   python3 -m build
   ```

3. **Upload to PyPI:**

   ```sh
   # Install/upgrade twine for uploading
   python3 -m pip install --upgrade twine

   # Upload to PyPI
   python3 -m twine upload dist/*
   ```

You will need a PyPI API token with maintainer access. Get one here: <https://pypi.org/manage/account/token/>

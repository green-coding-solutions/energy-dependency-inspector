# PIP Detector

## Purpose & Scope

The PIP detector identifies Python packages managed by `pip` with intelligent virtual environment detection. It automatically discovers and uses the appropriate Python environment while providing comprehensive dependency tracking for both system and project-specific installations.

## Key Features

### Virtual Environment Discovery

The detector discovers all pip-usable virtual environments instead of selecting only one:

1. **Explicit specification**: Manually provided virtual environment path is included first when valid
2. **Recursive scan**: Searches for all `pyvenv.cfg` files under `working_dir`
3. **Root fallback**: If no `working_dir` is provided, searches from `/`
4. **Pip validation**: Keeps only environments that also contain `bin/pip`
5. **System fallback**: System pip packages are added separately when available

### Environment Context Awareness

- **Project scan root**: Uses `working_dir` when provided
- **Default scan root**: Uses `/` when `working_dir` is not provided
- **Virtual environment indicator**: Uses `pyvenv.cfg` plus `bin/pip` as definitive markers

## Commands Used

- **Virtual environment detection**: `find` command to locate `pyvenv.cfg` files
- **Package listing**: `pip list --format=freeze` for clean `package==version` output
- **Location discovery**: `pip show pip` to determine installation location

## Search Paths

### Scan Scope

- Recursively scans the supplied `working_dir`
- Falls back to recursively scanning `/`
- Excludes nested `site-packages` and `dist-packages` paths from venv discovery

## Hash Generation

For project-scoped dependencies, generates location-based hashes by scanning the site-packages directory while excluding:

- Cache directories (`__pycache__`)
- Compiled Python files (`*.pyc`, `*.pyo`)
- Installation metadata (`INSTALLER`, `RECORD`)
- Core packaging tools that change frequently

## Output Format

**Single Location Detection:**

- **Project Scope** (single venv only): `scope: "project"`, installation location, and content hash
- **System Scope** (system only): `scope: "system"` with system-wide packages

**Multi-Location Detection:**

- **Mixed Scope** (multiple venvs and/or system): `scope: "mixed"` with nested `locations` structure
- Each location preserves its own scope, dependencies, and location-specific hash
- Enables tracking packages from multiple pip installations simultaneously

## Benefits

- **Environment-specific detection**: Captures packages from all discovered virtual environments
- **System isolation**: Distinguishes project dependencies from system packages
- **Automatic discovery**: Works without manual environment specification
- **Cross-platform support**: Handles both containerized and host environments
- **Fallback handling**: Gracefully falls back to system pip when no venv found

## Limitations

- **Python-specific**: Limited to Python package ecosystem
- **pip dependency**: Requires pip to be installed and functional
- **Basic information**: Only captures package name and version information

## Use Cases

- Python project dependency analysis
- Virtual environment comparison
- Containerized application dependency tracking
- CI/CD pipeline integration

# PIP Detector

## Purpose & Scope

The PIP detector identifies Python packages managed by `pip` with intelligent virtual environment detection. It automatically discovers and uses the appropriate Python environment while providing comprehensive dependency tracking for both system and project-specific installations.

## Key Features

### Smart Virtual Environment Detection

The detector uses a prioritized detection strategy:

1. **Explicit specification**: Manually provided virtual environment path
2. **Environment-aware detection**: `VIRTUAL_ENV` variable in Docker containers only
3. **Local project search**: Standard venv naming conventions (`./venv`, `./.venv`, `./env`, etc.)
4. **External environment search**: Common locations like `~/.virtualenvs/`, `~/.pyenv/versions/`
5. **System fallback**: System pip when no virtual environment detected

### Environment Context Awareness

- **Docker containers**: Uses `VIRTUAL_ENV` environment variable
- **Host systems**: Ignores `VIRTUAL_ENV` to avoid shell interference
- **Project directories**: Uses `pyvenv.cfg` files as definitive venv indicators

## Commands Used

- **Virtual environment detection**: `find` command to locate `pyvenv.cfg` files
- **Package listing**: `pip list --format=freeze` for clean `package==version` output
- **Location discovery**: `pip show pip` to determine installation location

## Search Paths

### Local Project Paths

- Current directory and common venv folder names (`./venv`, `./.venv`, `./env`, `./virtualenv`)

### External Environment Paths

- `~/.virtualenvs/{project_name}`
- `~/.local/share/virtualenvs/{project_name}`
- `~/.cache/pypoetry/virtualenvs/{project_name}`
- `~/.pyenv/versions/{project_name}`

## Hash Generation

For project-scoped dependencies, generates location-based hashes by scanning the site-packages directory while excluding:

- Cache directories (`__pycache__`)
- Compiled Python files (`*.pyc`, `*.pyo`)
- Installation metadata (`INSTALLER`, `RECORD`)
- Core packaging tools that change frequently

## Output Format

**Single Location Detection:**

- **Project Scope** (venv only): `scope: "project"`, installation location, and content hash
- **System Scope** (system only): `scope: "system"` with system-wide packages

**Multi-Location Detection:**

- **Mixed Scope** (venv + system): `scope: "mixed"` with nested `locations` structure
- Each location preserves its own scope, dependencies, and location-specific hash
- Enables tracking packages from multiple pip installations simultaneously

## Benefits

- **Environment-specific detection**: Captures packages from actual project environment
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

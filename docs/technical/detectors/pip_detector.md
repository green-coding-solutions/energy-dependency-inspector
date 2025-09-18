# PIP Detector

## Purpose & Scope

The PIP detector identifies Python packages managed by `pip` with intelligent virtual environment detection. It automatically discovers and uses the appropriate Python environment while providing comprehensive dependency tracking for both system and project-specific installations.

## Implementation Approach

### Package Manager Detection

Uses `pip list --format=freeze` for clean dependency information:

- **Clean format**: Simple `package==version` format without extraneous metadata
- **Machine readable**: Easy to parse programmatically with string splitting
- **Standard format**: Compatible with requirements.txt format, familiar to Python developers
- **Consistent output**: Stable format across different pip versions
- **Version precision**: Includes exact installed versions with proper operators

### Alternatives Considered

Several pip command options were evaluated:

- **`pip list --format=freeze`**: Chosen for clean package==version format
- **`pip list`**: Default human-readable format but inconsistent across versions
- **`pip list --format=json`**: JSON format with detailed metadata but more verbose
- **`pip freeze`**: Legacy freeze format command, superseded by `pip list --format=freeze`

**Decision rationale**: The freeze format provides the most suitable output for dependency tracking, offering clean `package==version` format that is machine-readable and compatible with requirements.txt format.

### Intelligent Virtual Environment Detection

Implements comprehensive virtual environment discovery with environment-aware strategy:

**Detection Priority (in order):**

1. **Explicit specification**: Manually provided virtual environment path
2. **Environment-aware detection**: `VIRTUAL_ENV` variable in Docker containers only
3. **Local project search**: Standard venv naming conventions in project directory
4. **External environment search**: Common external virtual environment locations
5. **System fallback**: System pip when no virtual environment detected

**Environment Context Awareness:**

- **Docker containers**: Uses `VIRTUAL_ENV` environment variable
- **Host systems**: Ignores `VIRTUAL_ENV` to avoid interference from current shell
- **Project directories**: Searches for `pyvenv.cfg` files as definitive venv indicators

## Command Used

### Virtual Environment Detection

```bash
# Batch search for pyvenv.cfg files across multiple paths
find {search_paths} -maxdepth 1 -name 'pyvenv.cfg' -type f 2>/dev/null | head -1
```

### Package Information Extraction

```bash
# Using detected virtual environment pip or system pip
{pip_command} list --format=freeze
```

**Output format example:**

```text
Django==4.2.1
requests==2.31.0
numpy==1.24.3
```

## Virtual Environment Discovery

### Search Path Strategy

**Local project paths:**

- Current directory (.)
- `./venv`, `./.venv`
- `./env`, `./.env`
- `./virtualenv`

**External environment paths (when working_dir specified):**

- `~/.virtualenvs/{project_name}`
- `~/.local/share/virtualenvs/{project_name}`
- `~/.cache/pypoetry/virtualenvs/{project_name}`
- `~/.pyenv/versions/{project_name}`

### Batch Virtual Environment Discovery

```python
def _find_venv_path(self, executor: EnvironmentExecutor, working_dir: str = None) -> Optional[str]:
    # Build prioritized search paths
    search_paths = [...]

    # Single batch find command
    escaped_paths = [f"'{path}'" for path in search_paths]
    find_cmd = f"find {' '.join(escaped_paths)} -maxdepth 1 -name 'pyvenv.cfg' -type f 2>/dev/null | head -1"

    stdout, _, exit_code = executor.execute_command(find_cmd)
    if exit_code == 0 and stdout.strip():
        pyvenv_cfg_path = stdout.strip()
        return os.path.dirname(pyvenv_cfg_path)

    return None
```

**Performance benefits:**

- **Single command**: Batch search across all paths simultaneously
- **Definitive identification**: Uses `pyvenv.cfg` as authoritative venv indicator
- **Caching**: Results cached to avoid repeated searches

### Environment-Aware Detection Logic

```python
# Docker containers: Use VIRTUAL_ENV
if not isinstance(executor, HostExecutor):
    stdout, _, exit_code = executor.execute_command("echo $VIRTUAL_ENV", working_dir)
    if exit_code == 0 and stdout.strip():
        search_paths.append(stdout.strip())

# Host systems: Skip VIRTUAL_ENV to avoid shell interference
```

## Package Information Parsing

Processes freeze format output:

```python
for line in stdout.strip().split("\n"):
    if line and "==" in line:
        package_name, version = line.split("==", 1)
        dependencies[package_name.strip()] = {
            "version": version.strip()
        }
```

**Benefits:**

- **Simple parsing**: Direct string splitting on "=="
- **No regex complexity**: Straightforward format processing
- **Version accuracy**: Captures exact installed versions

## Hash Generation

### Location-Based Hashing

Implements package manager location hashing for project-scoped dependencies:

**Hash generation for virtual environments:**

```bash
cd '{location}' && find . \
  -name '__pycache__' -prune -o \
  -name '__editable__*' -prune -o \
  -name 'pip*' -prune -o \
  -name 'setuptools*' -prune -o \
  -name 'pkg_resources' -prune -o \
  -name '*distutils*' -prune -o \
  -path '*/pip/_vendor' -prune -o \
  -not -name '*.pyc' \
  -not -name '*.pyo' \
  -not -name 'INSTALLER' \
  -not -name 'RECORD' \
  \( -type f -o -type l \) -printf '%s %p %l\n' | LC_COLLATE=C sort -n -k1,1 -k2,2
```

**Exclusions:**

- `__pycache__` - Python bytecode cache directories
- `__editable__*` - Editable install metadata
- `pip*`, `setuptools*` - Core packaging tools that change frequently
- `*.pyc`, `*.pyo` - Compiled Python files
- `INSTALLER`, `RECORD` - Package installation metadata

**Sort strategy:**

- Environment-independent sorting (LC_COLLATE=C)
- Primary: File size (numeric), Secondary: Path (lexicographic)
- Includes symbolic links with target paths

## Environment Detection

### Scope Determination

- **Project scope**: When virtual environment is detected
- **System scope**: When using system pip (no venv found)

### Location Resolution

```python
def _get_pip_location(self, executor: EnvironmentExecutor, working_dir: str = None) -> str:
    pip_command = self._get_pip_command(executor, working_dir)
    stdout, _, exit_code = executor.execute_command(f"{pip_command} show pip", working_dir)

    # Extract Location: field from pip show output
    for line in stdout.split("\n"):
        if line.startswith("Location:"):
            return line.split(":", 1)[1].strip()

    return "system"
```

## Output Format

The detector returns a tuple: `(packages, metadata)`

### Project Scope (with virtual environment)

**Packages:**

```json
[
  {
    "name": "Django",
    "version": "4.2.1",
    "type": "pip"
  },
  {
    "name": "requests",
    "version": "2.31.0",
    "type": "pip"
  }
]
```

**Metadata:**

```json
{
  "location": "/path/to/venv/lib/python3.9/site-packages",
  "hash": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890"
}
```

### System Scope (no virtual environment)

**Packages:**

```json
[
  {
    "name": "pip",
    "version": "23.1.2",
    "type": "pip"
  },
  {
    "name": "setuptools",
    "version": "67.8.0",
    "type": "pip"
  }
]
```

**Metadata:**

```json
{}
```

## Virtual Environment Detection Benefits

### Accuracy

- **Environment-specific dependencies**: Captures packages from actual project environment
- **Avoids system pollution**: Distinguishes project dependencies from system packages
- **Version precision**: Uses versions installed in specific environment

### Context Awareness

- **Docker container support**: Uses `VIRTUAL_ENV` in containerized environments
- **Host system safety**: Avoids false positives from shell environments
- **Project isolation**: Correctly identifies project-specific virtual environments

### Convenience

- **Automatic detection**: Works without manual environment specification
- **Standard conventions**: Supports common virtual environment naming patterns
- **Manual override**: Allows explicit virtual environment path specification

## Limitations & Constraints

- **Python-specific**: Limited to Python package ecosystem
- **Virtual environment dependency**: Requires `pyvenv.cfg` for definitive venv detection
- **pip availability**: Requires pip to be installed and functional
- **Freeze format limitation**: Only captures basic package name and version information
- **No individual hashes**: PyPI hashes not available locally (follows multi-tiered strategy)

## Error Handling

- **Virtual environment not found**: Gracefully falls back to system pip
- **Command failures**: Returns empty dependencies with appropriate scope/location
- **Path resolution errors**: Raises clear error messages for unresolvable paths
- **Hash generation failures**: Returns empty hash with debug output when enabled
- **Missing working directory**: Handles cases where specified working directory doesn't exist

## Use Cases

- **Python project analysis**: Track dependencies in virtual environments
- **Environment comparison**: Compare package versions across different environments
- **Development workflow**: Automatically detect project-specific dependencies
- **Containerized applications**: Correctly identify Python dependencies in Docker containers
- **CI/CD integration**: Reliable dependency detection across different execution contexts

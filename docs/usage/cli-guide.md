# Command Line Interface Guide

This guide covers all command line usage options for the energy-dependency-inspector.

## Basic Usage

```bash
# Analyze host system (default behavior)
python3 -m energy_dependency_inspector

# Explicitly specify host environment
python3 -m energy_dependency_inspector host

# Analyze Docker container by name
python3 -m energy_dependency_inspector docker nginx

# Analyze Docker container by ID
python3 -m energy_dependency_inspector docker a1b2c3d4e5f6
```

## Docker Container Analysis

```bash
# Get only container metadata (skip dependency detection)
python3 -m energy_dependency_inspector docker nginx --only-container-info
```

## Output Options

```bash
# Pretty print JSON output
python3 -m energy_dependency_inspector --pretty-print

# Enable debug output
python3 -m energy_dependency_inspector --debug
```

## Working Directory and Scope

```bash
# Set working directory for project-scoped package managers
python3 -m energy_dependency_inspector --working-dir /path/to/project

# Skip OS package managers like dpkg/apk (focus on project dependencies)
python3 -m energy_dependency_inspector --skip-os-packages

# Skip hash collection for improved performance
python3 -m energy_dependency_inspector --skip-hash-collection

# Select specific detectors to run
python3 -m energy_dependency_inspector --select-detectors "pip,dpkg"
```

## Detector Selection

Control which package managers are analyzed with the `--select-detectors` flag:

```bash
# Use only pip and dpkg detectors
python3 -m energy_dependency_inspector --select-detectors "pip,dpkg"

# Use only npm detector for Node.js projects
python3 -m energy_dependency_inspector --select-detectors "npm"

# Use multiple detectors with debug output
python3 -m energy_dependency_inspector --select-detectors "pip,npm,maven" --debug
```

**Available detectors:**

- `pip` - Python packages (pip/PyPI)
- `npm` - Node.js packages (npm/yarn)
- `dpkg` - Debian/Ubuntu system packages
- `apk` - Alpine Linux system packages
- `maven` - Java Maven dependencies
- `docker-info` - Docker container metadata

## Common Usage Patterns

### Analyzing a Specific Project

When analyzing project dependencies (like Python virtual environments or Node.js projects), specify the working directory:

```bash
# Analyze Python project with virtual environment
python3 -m energy_dependency_inspector --working-dir /path/to/python/project

# Analyze Node.js project
python3 -m energy_dependency_inspector --working-dir /path/to/nodejs/project

# Analyze only Python dependencies in a project
python3 -m energy_dependency_inspector --working-dir /path/to/python/project --select-detectors "pip"
```

### Comprehensive Docker Analysis

For comprehensive Docker container analysis:

```bash
# Full analysis including all package managers
python3 -m energy_dependency_inspector docker my-container --debug

# Container metadata only (faster)
python3 -m energy_dependency_inspector docker my-container --only-container-info
```

### Debugging and Development

```bash
# Enable verbose output for troubleshooting
python3 -m energy_dependency_inspector --debug

# Focus on project dependencies only
python3 -m energy_dependency_inspector --skip-os-packages --debug

# Fast analysis without hash collection
python3 -m energy_dependency_inspector --skip-hash-collection --debug
```

## Supported Environments

- **host** - Host system analysis (default)
- **docker** - Docker container analysis (requires container ID or name)

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Invalid arguments or usage

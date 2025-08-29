# Command Line Interface Guide

This guide covers all command line usage options for the dependency-resolver.

## Basic Usage

```bash
# Analyze host system (default behavior)
python3 -m dependency_resolver

# Explicitly specify host environment
python3 -m dependency_resolver host

# Analyze Docker container by name
python3 -m dependency_resolver docker nginx

# Analyze Docker container by ID
python3 -m dependency_resolver docker a1b2c3d4e5f6
```

## Docker Container Analysis

```bash
# Get only container metadata (skip dependency detection)
python3 -m dependency_resolver docker nginx --only-container-info
```

## Output Options

```bash
# Pretty print JSON output
python3 -m dependency_resolver --pretty-print

# Enable debug output
python3 -m dependency_resolver --debug
```

## Working Directory and Scope

```bash
# Set working directory for project-scoped package managers
python3 -m dependency_resolver --working-dir /path/to/project

# Skip system scope package managers (focus on project dependencies)
python3 -m dependency_resolver --skip-system-scope
```

## Common Usage Patterns

### Analyzing a Specific Project

When analyzing project dependencies (like Python virtual environments or Node.js projects), specify the working directory:

```bash
# Analyze Python project with virtual environment
python3 -m dependency_resolver --working-dir /path/to/python/project

# Analyze Node.js project
python3 -m dependency_resolver --working-dir /path/to/nodejs/project
```

### Comprehensive Docker Analysis

For comprehensive Docker container analysis:

```bash
# Full analysis including all package managers
python3 -m dependency_resolver docker my-container --debug

# Container metadata only (faster)
python3 -m dependency_resolver docker my-container --only-container-info
```

### Debugging and Development

```bash
# Enable verbose output for troubleshooting
python3 -m dependency_resolver --debug

# Focus on project dependencies only
python3 -m dependency_resolver --skip-system-scope --debug
```

## Supported Environments

- **host** - Host system analysis (default)
- **docker** - Docker container analysis (requires container ID or name)

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Invalid arguments or usage

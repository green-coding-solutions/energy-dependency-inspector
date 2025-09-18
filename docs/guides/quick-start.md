# Quick Start Guide

Get up and running with dependency-resolver in minutes.

## Installation

```bash
git clone https://github.com/green-coding-solutions/dependency-resolver
cd dependency-resolver
pip install .
```

## Basic Usage

### Analyze Host System

```bash
python3 -m dependency_resolver
```

This analyzes your current system and outputs a JSON report with packages organized by scope (project vs system).

### Analyze Docker Container

```bash
python3 -m dependency_resolver docker nginx
```

Replace `nginx` with any Docker container name or ID.

### Pretty Print Output

```bash
python3 -m dependency_resolver --pretty-print
```

## Understanding the Output

The tool outputs JSON with packages organized by scope:

```json
{
  "project": {
    "packages": [
      {
        "name": "flask",
        "version": "2.3.3",
        "type": "pip"
      }
    ],
    "package-management": {
      "pip": {
        "location": "/path/to/venv/lib/python3.12/site-packages",
        "hash": "abc123..."
      }
    }
  },
  "system": {
    "packages": [
      {
        "name": "package-name",
        "version": "1.2.3 amd64",
        "type": "dpkg",
        "hash": "def456..."
      }
    ]
  }
}
```

Packages are grouped into **project** (local dependencies) and **system** (system-wide packages), with metadata for each package manager stored separately.

## Common Use Cases

### Python Project Analysis

```bash
cd /path/to/your/python/project
python3 -m dependency_resolver --working-dir .
```

### Node.js Project Analysis

```bash
cd /path/to/your/nodejs/project
python3 -m dependency_resolver --working-dir .
```

### Debug Mode

```bash
python3 -m dependency_resolver --debug
```

Enables verbose output to troubleshoot detection issues.

## Next Steps

- **[CLI Guide](../usage/cli-guide.md)** - Complete command line reference
- **[Python API](../usage/programmatic-api.md)** - Use as a library
- **[Output Format](../usage/output-format.md)** - Understanding the results
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

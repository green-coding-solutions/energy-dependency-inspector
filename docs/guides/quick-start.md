# Quick Start Guide

Get up and running with energy-dependency-inspector in minutes.

## Installation

```bash
git clone https://github.com/green-coding-solutions/energy-dependency-inspector
cd energy-dependency-inspector
pip install .
```

## Basic Usage

### Analyze Host System

```bash
python3 -m energy_dependency_inspector
```

This analyzes your current system and outputs a JSON report of all detected package managers and their dependencies.

### Analyze Docker Container

```bash
python3 -m energy_dependency_inspector docker nginx
```

Replace `nginx` with any Docker container name or ID.

### Pretty Print Output

```bash
python3 -m energy_dependency_inspector --pretty-print
```

## Understanding the Output

The tool outputs JSON with detected package managers:

```json
{
  "dpkg": {
    "scope": "system",
    "dependencies": {
      "package-name": {
        "version": "1.2.3 amd64",
        "hash": "abc123..."
      }
    }
  }
}
```

Each section represents a package manager (dpkg, pip, npm, etc.) with its detected packages.

## Common Use Cases

### Python Project Analysis

```bash
cd /path/to/your/python/project
python3 -m energy_dependency_inspector --working-dir .
```

### Node.js Project Analysis

```bash
cd /path/to/your/nodejs/project
python3 -m energy_dependency_inspector --working-dir .
```

### Debug Mode

```bash
python3 -m energy_dependency_inspector --debug
```

Enables verbose output to troubleshoot detection issues.

## Next Steps

- **[CLI Guide](../usage/cli-guide.md)** - Complete command line reference
- **[Python API](../usage/programmatic-api.md)** - Use as a library
- **[Output Format](../usage/output-format.md)** - Understanding the results
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

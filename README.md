# Energy Dependency Inspector

[![PyPI](https://img.shields.io/pypi/v/energy-dependency-inspector)](https://pypi.org/project/energy-dependency-inspector/)

A tool for capturing dependency snapshots of running systems by querying their package managers directly. Unlike filesystem-scanning approaches, it inspects the actual installed state of packages as reported by the system's package management tools. Originally designed to reveal relevant changes when conducting energy measurements, it can also be used as a general-purpose dependency resolver. By tracking installed packages and their versions, you can identify whether changes in performance, energy consumption, or behavior are due to code modifications or dependency updates.

The tool provides both a command-line interface and a Python library for programmatic use. It supports dependency inspection of Docker containers and host systems, outputting structured JSON with package information, versions, and unique hash values.

## Installation

**From PyPI:**

```bash
pip install energy-dependency-inspector
```

**From source:**

```bash
git clone https://github.com/green-coding-solutions/energy-dependency-inspector
cd energy-dependency-inspector
pip install .
```

## Quick Start

```bash
# Analyze host system
python3 -m energy_dependency_inspector

# Analyze Docker container
python3 -m energy_dependency_inspector docker nginx

# Pretty print output
python3 -m energy_dependency_inspector --pretty-print

# Get help with all options
python3 -m energy_dependency_inspector -h
```

## Supported Package Managers

- **apt/dpkg** - System packages Ubuntu/Debian
- **apk** - System packages of Alpine
- **pip** - Python packages
- **npm** - Node.js packages
- **maven** - Java packages

Also captures **Docker container metadata** when analyzing containers.

## Usage Options

### Command Line Interface

For terminal usage with full control over options and environments.

### Programmatic Interface

Use as a Python library in other projects:

```python
import energy_dependency_inspector

# Analyze host system
deps = energy_dependency_inspector.resolve_host_dependencies()

# Analyze Docker container
docker_deps = energy_dependency_inspector.resolve_docker_dependencies("nginx")
```

## Documentation

- **[Quick Start Guide](./docs/guides/quick-start.md)** - Get up and running
- **[CLI Usage Guide](./docs/usage/cli-guide.md)** - Complete command line reference
- **[Python API Guide](./docs/usage/programmatic-api.md)** - Programmatic usage
- **[Output Format Guide](./docs/usage/output-format.md)** - Understanding the JSON results
- **[Troubleshooting](./docs/guides/troubleshooting.md)** - Common issues and solutions
- **[Technical Documentation](./docs/technical/)** - Architecture and implementation details

## Contributing

For development setup, contribution guidelines, and information about running tests and code quality checks, please see [CONTRIBUTING.md](./CONTRIBUTING.md).

## Requirements and Design

See the complete [SPECIFICATION.md](./SPECIFICATION.md) for detailed requirements and implementation constraints.

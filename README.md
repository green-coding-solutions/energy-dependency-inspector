# dependency-resolver

A tool for creating snapshots of installed packages on specified target environments. The project provides both a command-line interface and a Python library for programmatic use.

Its main focus is dependency resolving of Docker containers, but it also supports dependency resolving on the host system. The output is a structured JSON that includes information about all the installed packages from supported sources with their version and unique hash values.

## Installation

```bash
git clone https://github.com/green-coding-solutions/dependency-resolver
cd dependency-resolver
pip install .
```

## Quick Start

```bash
# Analyze host system
python3 -m dependency_resolver

# Analyze Docker container
python3 -m dependency_resolver docker nginx

# Pretty print output
python3 -m dependency_resolver --pretty-print

# Get help with all options
python3 -m dependency_resolver -h
```

## Supported Package Managers

- **apt/dpkg** - System packages Ubuntu/Debian
- **apk** - System packages of Alpine
- **pip** - Python packages
- **npm** - Node.js packages

Also captures **Docker container metadata** when analyzing containers.

## Usage Options

### Command Line Interface

For terminal usage with full control over options and environments.

### Programmatic Interface

Use as a Python library in other projects:

```python
import dependency_resolver

# Analyze host system
deps = dependency_resolver.resolve_host_dependencies()

# Analyze Docker container
docker_deps = dependency_resolver.resolve_docker_dependencies("nginx")
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

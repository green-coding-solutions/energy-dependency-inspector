# dependency-resolver

A tool for creating snapshots of installed packages on specified target environments. The project provides both a command-line interface and a Python library for programmatic use.
Its main focus is dependency resolving of Docker containers, but it also supports dependency resolving on the host system.
The output is a structured JSON that includes information about all the installed packages from supported sources with their version and unique hash values.

## Installation

```bash
# Clone and install
git clone https://github.com/green-coding-solutions/dependency-resolver
cd dependency-resolver
pip install .
```

## Usage

The dependency-resolver can be used in two ways:

1. **Command Line Interface (CLI)** - For direct terminal usage
2. **Programmatic Interface** - As a Python library in other projects

### Command Line Interface

```bash
# Analyze host system (default behavior)
python3 -m dependency_resolver

# Explicitly specify host environment
python3 -m dependency_resolver host

# Analyze Docker container by name
python3 -m dependency_resolver docker nginx

# Analyze Docker container by ID
python3 -m dependency_resolver docker a1b2c3d4e5f6

# Get only container metadata (skip dependency detection)
python3 -m dependency_resolver docker nginx --only-container-info

# Enable debug output
python3 -m dependency_resolver --debug

# Set working directory
python3 -m dependency_resolver --working-dir /path/to/project

# Skip system scope package managers
python3 -m dependency_resolver --skip-system-scope

# Pretty print JSON output
python3 -m dependency_resolver --pretty-print
```

### Programmatic Interface

The dependency-resolver can also be used as a Python library in other projects. Here are some examples:

```python
import dependency_resolver

# Simple host system analysis
deps_json = dependency_resolver.resolve_host_dependencies()

# Get results as Python dictionary for further processing
deps_dict = dependency_resolver.resolve_dependencies_as_dict(
    environment_type="host",
    skip_system_scope=True
)

# Docker container analysis
docker_deps = dependency_resolver.resolve_docker_dependencies(
    container_identifier="nginx",
    working_dir="/app"
)

# Advanced usage with direct access to core classes
from dependency_resolver import Orchestrator, HostExecutor, OutputFormatter

executor = HostExecutor()
orchestrator = Orchestrator(debug=True, skip_system_scope=True)
dependencies = orchestrator.resolve_dependencies(executor)
formatter = OutputFormatter()
json_output = formatter.format_json(dependencies, pretty_print=True)
```

**Available convenience functions:**

- `resolve_host_dependencies()` - Analyze host system, returns JSON string
- `resolve_docker_dependencies()` - Analyze Docker container, returns JSON string
- `resolve_docker_dependencies_as_dict()` - Analyze Docker container, returns Python dictionary
- `resolve_dependencies_as_dict()` - Generic analysis, returns Python dictionary

**Available classes for advanced usage:**

- `Orchestrator` - Main dependency resolution coordinator
- `HostExecutor`, `DockerExecutor` - Environment adapters
- `OutputFormatter` - JSON formatting utilities

### Supported Environments

- **host** - Host system analysis (default)
- **docker** - Docker container analysis (requires container ID or name)

### Supported Detectors

**Package Managers:**

- **apt/dpkg** - System packages Ubuntu/Debian
- **apk** - System packages of Alpine
- **pip** - Python packages
- **npm** - Node.js packages

**Container Information:**

- **docker-info** - Docker container metadata and base image details

### Output Format

The tool outputs JSON with the following structure:

```json
{
  "_container-info": {
    "name": "nginx-container",
    "image": "nginx:latest",
    "hash": "sha256:2cd1d97f893f..."
  },
  "dpkg": {
    "scope": "system",
    "dependencies": {
      "package-name": {
        "version": "1.2.3 amd64",
        "hash": "abc123..."
      }
    }
  },
  "pip": {
    "scope": "project",
    "location": "/path/to/venv/lib/python3.12/site-packages",
    "hash": "def456...",
    "dependencies": {
      "package-name": {
        "version": "1.2.3"
      }
    }
  }
}
```

## Documentation

### Architecture & Detector Documentation

For detailed information about architectural decisions and package manager implementations:

- **Architecture Decision Records**: See [docs/adr/](./docs/adr/) for architectural decisions
- **Detector Documentation**: See [docs/detectors/](./docs/detectors/) for detailed implementation information:
  - [APK Detector](./docs/detectors/apk_detector.md) - Alpine Linux package detection
  - [DPKG Detector](./docs/detectors/dpkg_detector.md) - Debian/Ubuntu package detection
  - [NPM Detector](./docs/detectors/npm_detector.md) - Node.js package detection
  - [PIP Detector](./docs/detectors/pip_detector.md) - Python package detection
  - [Docker Info Detector](./docs/detectors/docker_info_detector.md) - Individual container metadata

See the complete [SPECIFICATION.md](./SPECIFICATION.md) for detailed requirements and implementation constraints.

## Contributing

For development setup, contribution guidelines, and information about running tests and code quality checks, please see [CONTRIBUTING.md](./CONTRIBUTING.md).

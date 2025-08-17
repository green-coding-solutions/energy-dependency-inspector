# dependency-resolver

The purpose of this project is to create a snapshot of the installed packages on a specified target environment.
Its main focus is the dependency resolving of Docker containers.
The output is a structured JSON that includes information about all the installed packages from supported sources with their version and unique hash values.

## Installation

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# For Docker support (optional)
pip install -e ".[docker]"

# For Podman support (optional, not implemented yet)
pip install -e ".[podman]"
```

## Usage

### Basic Usage

```bash
# Analyze host system (default behavior)
python3 dependency_resolver.py

# Explicitly specify host environment
python3 dependency_resolver.py host

# Analyze Docker container by name
python3 dependency_resolver.py docker nginx

# Analyze Docker container by ID
python3 dependency_resolver.py docker a1b2c3d4e5f6

# Get only container metadata (skip dependency detection)
python3 dependency_resolver.py docker nginx --only-container-info

# Analyze Docker Compose stack
python3 dependency_resolver.py docker_compose my_app

# Enable debug output
python3 dependency_resolver.py --debug

# Set working directory
python3 dependency_resolver.py --working-dir /path/to/project

# Skip system scope package managers
python3 dependency_resolver.py --skip-system-scope

# Pretty print JSON output
python3 dependency_resolver.py --pretty-print
```

### Supported Environments

- **host** - Host system analysis (default)
- **docker** - Docker container analysis (requires container ID or name)
- **docker_compose** - Docker Compose stack analysis (requires stack/project name)

### Supported Package Managers

Currently supported:

- **apt/dpkg** - System packages Ubuntu/Debian
- **apk** - System packages of Alpine
- **pip** - Python packages
- **npm** - Node.js packages
- **docker-compose** - Container images from Docker Compose stacks
- **docker-info** - Individual Docker container metadata

### Output Format

The tool outputs JSON with the following structure:

```json
{
  "_container-info": {
    "name": "nginx-container",
    "image": "nginx:latest",
    "hash": "sha256:2cd1d97f893f..."
  },
  "docker-compose": {
    "scope": "compose",
    "dependencies": {
      "web": {
        "version": "django_app-web:latest",
        "hash": "sha256:3e4def6e2af8..."
      },
      "db": {
        "version": "postgres:13",
        "hash": "sha256:54706ca98cd5..."
      }
    }
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
  - [Docker Compose Detector](./docs/detectors/docker_compose_detector.md) - Container image detection
  - [Docker Info Detector](./docs/detectors/docker_info_detector.md) - Individual container metadata

See the complete [SPECIFICATION.md](./SPECIFICATION.md) for detailed requirements and implementation constraints.

## Contributing

For development setup, contribution guidelines, and information about running tests and code quality checks, please see [CONTRIBUTING.md](./CONTRIBUTING.md).

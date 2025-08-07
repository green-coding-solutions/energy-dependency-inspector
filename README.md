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

# Analyze Docker Compose stack
python3 dependency_resolver.py docker_compose my_app

# Enable debug output
python3 dependency_resolver.py --debug

# Set working directory
python3 dependency_resolver.py --working-dir /path/to/project

# Skip global package manager detections
python3 dependency_resolver.py --skip-global
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
- **docker-compose** - Container orchestration dependencies

Future support planned:

- **npm** - Node.js packages

### Output Format

The tool outputs JSON with the following structure:

```json
{
  "docker-compose": {
    "location": "global",
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
  "apt": {
    "location": "global",
    "dependencies": {
      "package-name": {
        "version": "1.2.3 amd64",
        "hash": "abc123..."
      }
    }
  },
  "pip": {
    "location": "/usr/lib/python3/dist-packages",
    "dependencies": {
      "package-name": {
        "version": "1.2.3",
        "hash": "def456..."
      }
    }
  }
}
```

## Documentation

### Architecture Decision Records (ADRs)

For detailed information about architectural decisions and design rationale, see the [Architecture Decision Records](./docs/adr/) directory. Key decisions include:

- [ADR-0001: Runtime Snapshot Approach](./docs/adr/0001-runtime-snapshot-approach.md) - Why we analyze running environments instead of source files
- [ADR-0002: Modular Detector Architecture](./docs/adr/0002-modular-detector-architecture.md) - The extensible architecture for package manager detection
- [ADR-0005: Hash Generation Strategy](./docs/adr/0005-hash-generation-strategy.md) - Multi-tiered hash generation approach

See the complete [SPECIFICATION.md](./SPECIFICATION.md) for detailed requirements and implementation constraints.

## Contributing

For development setup, contribution guidelines, and information about running tests and code quality checks, please see [CONTRIBUTING.md](./CONTRIBUTING.md).

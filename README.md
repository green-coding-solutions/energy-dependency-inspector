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

# Enable debug output
python3 dependency_resolver.py --debug

# Set working directory
python3 dependency_resolver.py --working-dir /path/to/project
```

### Supported Environments

- **host** - Host system analysis (default)
- **docker** - Docker container analysis (requires container ID or name)

### Supported Package Managers

Currently supported:

- **apt/dpkg** - System packages Ubuntu/Debian
- **apk** - System packages of Alpine
- **pip** - Python packages

Future support planned:

- **npm** - Node.js packages
- **docker-compose** - Container orchestration

### Output Format

The tool outputs JSON with the following structure:

```json
{
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

## Contributing

For development setup, contribution guidelines, and information about running tests and code quality checks, please see [CONTRIBUTING.md](./CONTRIBUTING.md).

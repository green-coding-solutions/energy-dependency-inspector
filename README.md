# dependency-resolver

The purpose of this project is to create a snapshot of the installed packages on a specified target environment.
Its main focus is the dependency resolving of Docker containers.
The output is a structured JSON that includes information about all the installed packages from supported sources with their version and unique hash values.

## Installation

### Development Setup

```bash
# Clone the repository
git clone https://github.com/green-coding-solutions/dependency-resolver
cd dependency-resolver

# Install development dependencies
pip install -r requirements-dev.txt

# Or using pyproject.toml (recommended)
pip install -e ".[dev]"
```

### Production Installation

```bash
# Basic installation (host environment only)
pip install -e .

# With Docker support (future)
pip install -e ".[docker]"

# With Podman support (future)
pip install -e ".[podman]"
```

## Usage

### Basic Usage

```bash
# Analyze host system (default behavior)
python3 dependency_resolver.py

# Explicitly specify host environment
python3 dependency_resolver.py host

# Enable debug output
python3 dependency_resolver.py --debug

# Set working directory
python3 dependency_resolver.py --working-dir /path/to/project
```

### Supported Package Managers

Currently supported:

- **pip** - Python packages
- **apt/dpkg** - System packages (Ubuntu/Debian)

Future support planned:

- **npm** - Node.js packages
- **docker** - Container images
- **docker-compose** - Container orchestration

### Output Format

The tool outputs JSON with the following structure:

```json
{
  "system": {
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

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=dependency_resolver

# Run specific test file
pytest tests/test_pip_detector.py
```

### Code Quality

```bash
# Run pylint (as specified in project guidelines)
pylint core/ detectors/ utils/ dependency_resolver.py

# Run type checking
mypy core/ detectors/ utils/ dependency_resolver.py

# Format code
black core/ detectors/ utils/ dependency_resolver.py
```

### Project Structure

```plain
dependency_resolver/
├── dependency_resolver.py    # CLI entry point
├── core/
│   ├── interfaces.py         # Abstract base classes
│   ├── executor.py           # Environment executors
│   └── resolver.py           # Main orchestrator
├── detectors/
│   ├── pip_detector.py       # Python packages
│   └── apt_detector.py       # System packages
├── utils/                    # Utility modules (future)
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
└── pyproject.toml           # Project configuration
```

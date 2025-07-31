# Project Specification

## Problem Statement

The Green Metrics Tool (GMT) currently cannot detect dependency changes because while repositories are fixed via git hash, source/package manager files without version pinning appear unchanged to GMT even when actual installed versions differ over time.

## Core Requirements

### Functional Requirements

1. Dependency Detection: Build a standalone dependency resolver that can export JSON with all project dependencies
2. Version/Hash Output: Each dependency should include a preferably semantic versioning and, if available, a hash value
3. Multi-Package Manager Support: Support various package managers and OS package systems
4. Modular Architecture: Implement as modular add-ons for different systems and package managers
5. Runtime Analysis: Analyze running environments (containers) rather than source files to capture actual installed packages

### Target Package Managers (Initial Set)

- Programming Languages with their common package managers: Python, JavaScript
- Operating Systems with their common package managers: Ubuntu/Debian, Alpine Linux
- Container images: Docker and Podman (with hash + tags methodology)

### Environment Support

- Primary: Docker containers (using container hash/ID or name)
- Secondary: Host system analysis
- Future: Podman containers, Docker/Podman Compose stacks

## Design Approach

### Architecture Decisions

**Runtime Snapshot vs. Source File Parsing**: See [ADR-0001](docs/adr/0001-runtime-snapshot-approach.md) for the decision to analyze running environments rather than parsing source files.

**Modular Architecture**: See [ADR-0002](docs/adr/0002-modular-detector-architecture.md) for the modular detector architecture with abstract base classes and auto-discovery.

### Command Interface

```sh
dependency_resolver.py <environment_type> <environment_identifier> <options>
```

- **environment_type**: The type of environment you want to inspect. Supported environments: `host`, `docker` (additional ones in the future, not included in the initial set: `podman`, `docker_compose` and `podman_compose`)
- **environment_identifier**: An identifier of the environment. For `docker` and `podman` the container run id (short or full) and the container name are allowed, for `docker_compose` and `podman_compose` the name of the compose stack is allowed (specified or auto-generated project name). For `host` no identifier is required.
- **options**: Possibility to provide multiple options parameter (see below)

All parameters are optional. If no `environment_type` and `environment_identifier` is provided, the host system will be analyzed.
If a container should be analyzed, all the checks will be executed inside the container.

Available options:

- `--working-dir <working-dir>`: uses the path as the working directory in the target environment and executes all checks from there
- `--debug`: prints debug statements

Examples:

- `dependency_resolver.py` (host system, no parameters)
- `dependency_resolver.py docker a1b2c3d4e5f6` (Docker container by id)
- `dependency_resolver.py docker nginx` (Docker container by name)
- `dependency_resolver.py docker_compose my_app` (Docker compose stack)
- `dependency_resolver.py --working-dir /tmp/repo` (sets the working directory on the target environment, here the host system)

### Execution Method

- Modular check/dump routines for each package manager
  - abstraction layer is used to separate the check/dump logic from the environment specific execution (e.g. using the docker library to run the checks inside containers)
- `docker` Python library is used to execute commands in containers

### Modular Architecture Details

#### Core Components

1. **Abstract Base Classes**
   - `PackageManagerDetector`: Interface for all package manager implementations
     - `meets_requirements(executor)`: Check if pre-requirements are met (OS compatibility, etc.)
     - `is_available(executor)`: Check if package manager exists in environment
     - `get_dependencies(executor, working_dir)`: Extract dependencies with versions/hashes
     - `get_name()`: Return package manager identifier
   - `EnvironmentExecutor`: Interface for command execution in different environments
     - `execute_command(command, working_dir)`: Run commands in target environment
     - `file_exists(path)`: Check file existence in target environment

2. **Environment Executors**
   - `HostExecutor`: Execute commands on host system using subprocess
   - `DockerExecutor`: Execute commands inside Docker containers using docker library
   - `PodmanExecutor`: Execute commands inside Podman containers using podman-py

3. **Package Manager Detectors**
   - `PipDetector`: Python packages via `pip list --format=freeze` (see [ADR-0006](docs/adr/0006-pip-list-for-python-packages.md))
     - No OS requirements (works on any system with Python)
     - Automatically detects and uses virtual environments (see [ADR-0007](docs/adr/0007-python-virtual-environment-detection.md))
     - Uses the virtual environment's pip executable when available
   - `NpmDetector`: Node.js packages via `npm list --json --depth=0`
   - `AptDetector`: Debian/Ubuntu system packages via `dpkg-query` (see [ADR-0003](docs/adr/0003-dpkg-query-for-package-information.md))
     - **Pre-requirement**: Must be running on Debian/Ubuntu systems (checks `/etc/os-release` and `/etc/debian_version`)
     - **Availability check**: Verifies that `dpkg-query` command exists
   - `ApkDetector`: Alpine Linux system packages via `apk info` (see [ADR-0004](docs/adr/0004-apk-info-for-alpine-packages.md))
     - **Pre-requirement**: Must be running on Alpine Linux systems (checks `/etc/os-release` and `/etc/alpine-release`)
     - **Availability check**: Verifies that `apk` command exists
   - `DockerComposeDetector`: Container orchestration dependencies (which container images are used?)

4. **Main Orchestrator**
   - `DependencyResolver`: Coordinates detection and extraction
   - Auto-discovers available package managers
   - Executes detectors in isolation with error handling
   - Aggregates results into unified JSON output

#### Directory Structure

```plain
dependency_resolver/
├── main.py                   # CLI entry point
├── core/
│   ├── interfaces.py         # Abstract base classes
│   ├── executor.py           # Environment executors
│   └── resolver.py           # Main orchestrator
└── detectors/
    ├── pip_detector.py
    ├── npm_detector.py
    ├── apt_detector.py
    ├── apk_detector.py
    └── docker_compose_detector.py
```

#### Detection Strategy

- **Pre-Requirements Check**: Each detector first checks if its requirements are met (OS compatibility, etc.)
- **Auto-Discovery**: Available detectors check if their package manager exists in the environment
- **Error Isolation**: Failed detectors don't affect others (catch all exceptions)
- **Priority Order**: System packages → Language-specific → Container orchestration
- **Working Directory**: All detectors respect `--working-dir` parameter

The detection process follows this sequence:

1. Check pre-requirements via `meets_requirements(executor)`
2. If requirements are met, check availability via `is_available(executor)`
3. If available, extract dependencies via `get_dependencies(executor, working_dir)`

### JSON Output Schema

Schema with example values (incomplete):

```json
{
  "docker-compose": {
    "location": "global",
    "dependencies": {
      "backend": {
          "version": "latest",
          "hash": "a1b2c3d4e5f6"
      }
    },
    // ...
  },
  "system": {
    "location": "global",
    "dependencies": {
      "zip": {
        "version": "3.0-13ubuntu0.2 amd64",
        "hash": "das7892234890sad890fa0s98903284092"
       },
       "curl": {
        "version": "7.81.0-1ubuntu1.18 amd64"
       },
       // ...
    }
  },
  "pip": {
      "location": "/home/user/venv",
      "hash": "a1b2c3d4e5f6789012345678901234ab",
      "dependencies": {
      "numpy": {
          "version": "1.3.3"
      }
    },
    // ...
  },
  "npm": {
    "location": "/app/frontend",
    "hash": "b2c3d4e5f67890123456789012345bcd",
    "dependencies": {
      "react": {
        "version": "18.2.0"
      },
      "lodash": {
        "version": "4.17.21"
      }
    },
    // ...
  },
  // ...
}
```

## Implementation Constraints

### Technical Constraints

1. **Read-Only Operations**: See [ADR-0009](docs/adr/0009-read-only-operations.md) for the complete read-only constraint policy
2. **Unix-Based Systems**: See [ADR-0010](docs/adr/0010-unix-only-support.md) for platform support scope

### Hash Handling Strategy

See [ADR-0005](docs/adr/0005-hash-generation-strategy.md) for the complete multi-tiered hash generation strategy.

**Key Points**:

- Individual package hashes only if retrievable from package manager
- Location-based hashes for package manager installations
- APT MD5 extraction approach (see [ADR-0008](docs/adr/0008-apt-md5-hash-extraction.md))
- SHA256 format truncated to 32 characters

### Logging Strategy

- Print debug statements about the availability of package managers if the option `--debug` is provided

### Error Handling Strategy

- If the provided input parameters are invalid or the environment is not available, exit with an error message and the exit code 1
- Errors while checking for packages should always be caught

## Future plans

See [TODOS.md](TODOS.md).

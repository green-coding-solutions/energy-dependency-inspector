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
- Container metadata: Individual Docker container information (name, image, hash)

### Environment Support

- Primary: Docker containers (using container hash/ID or name)
- Docker Compose stacks (using stack/project name)
- Secondary: Host system analysis
- Future: Podman containers, Podman Compose stacks

## Design Approach

### Architecture Decisions

**Runtime Snapshot vs. Source File Parsing**: See [ADR-0001](docs/adr/0001-runtime-snapshot-approach.md) for the decision to analyze running environments rather than parsing source files.

**Modular Architecture**: See [ADR-0002](docs/adr/0002-modular-detector-architecture.md) for the modular detector architecture with abstract base classes and auto-discovery.

**Dependency Hash Strategy**: See [ADR-0005](docs/adr/0005-dependency-hash-strategy.md) for the multi-tiered approach to change detection and integrity verification.

### Command Interface

```sh
python3 -m dependency_resolver <environment_type> <environment_identifier> <options>
```

- **environment_type**: The type of environment you want to inspect. Supported environments: `host`, `docker`, `docker_compose` (additional ones in the future: `podman`, `podman_compose`)
- **environment_identifier**: An identifier of the environment. For `docker` and `podman` the container run id (short or full) and the container name are allowed, for `docker_compose` and `podman_compose` the name of the compose stack is allowed (specified or auto-generated project name). For `host` no identifier is required.
- **options**: Possibility to provide multiple options parameter (see below)

All parameters are optional. If no `environment_type` and `environment_identifier` is provided, the host system will be analyzed.
If a container should be analyzed, all the checks will be executed inside the container and container metadata will be included.
If a Docker Compose stack should be analyzed, only the container images themselves are analyzed (no commands executed inside containers).

Available options:

- `--working-dir <working-dir>`: uses the path as the working directory in the target environment and executes all checks from there
- `--debug`: prints debug statements
- `--skip-system-scope`: skips system scope package managers (system packages or globally installed Python packages)
- `--venv-path <venv-path>`: explicit virtual environment path for pip detector
- `--only-container-info`: for docker environment, only analyze container metadata (skip dependency detection)

Examples:

- `python3 -m dependency_resolver` (host system, no parameters)
- `python3 -m dependency_resolver docker a1b2c3d4e5f6` (Docker container by id)
- `python3 -m dependency_resolver docker nginx` (Docker container by name)
- `python3 -m dependency_resolver docker nginx --only-container-info` (Docker container metadata only)
- `python3 -m dependency_resolver docker_compose my_app` (Docker compose stack)
- `python3 -m dependency_resolver --working-dir /tmp/repo` (sets the working directory on the target environment, here the host system)

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
   - `DockerComposeExecutor`: Manage Docker Compose stacks and extract container image metadata
   - `PodmanExecutor`: Execute commands inside Podman containers using podman-py

3. **Package Manager Detectors**
   - `PipDetector`: Python packages via `pip list --format=freeze` (see [docs/detectors/pip_detector.md](docs/detectors/pip_detector.md))
     - No OS requirements (works on any system with Python)
     - Automatically detects and uses virtual environments
     - Uses the virtual environment's pip executable when available
   - `NpmDetector`: Node.js packages via `npm list --json --depth=0`
   - `DpkgDetector`: Debian/Ubuntu system packages via `dpkg-query` (see [docs/detectors/dpkg_detector.md](docs/detectors/dpkg_detector.md))
     - **Pre-requirement**: Must be running on Debian/Ubuntu systems (checks `/etc/os-release` and `/etc/debian_version`)
     - **Availability check**: Verifies that `dpkg-query` command exists
   - `ApkDetector`: Alpine Linux system packages via `apk list --installed` (see [docs/detectors/apk_detector.md](docs/detectors/apk_detector.md))
     - **Pre-requirement**: Must be running on Alpine Linux systems (checks `/etc/os-release` and `/etc/alpine-release`)
     - **Availability check**: Verifies that `apk` command exists
   - `DockerComposeDetector`: Container orchestration dependencies (extracts container images with full SHA256 hashes)
     - **Usage**: Only activated for `DockerComposeExecutor` environments
     - **Output**: Service names mapped to image tags and full SHA256 hashes (including `sha256:` prefix)
     - **No command execution**: Does not execute commands inside containers, only analyzes container metadata
   - `DockerInfoDetector`: Individual Docker container metadata (extracts container name, image name, and SHA256 hash)
     - **Usage**: Automatically included in `DockerExecutor` environments
     - **Output**: Container metadata in simplified `_container-info` format
     - **Modes**: Works in both full analysis and container-info-only modes

4. **Main Orchestrator**
   - `Orchestrator`: Coordinates detection and extraction
   - Auto-discovers available package managers
   - Executes detectors in isolation with error handling
   - Aggregates results into unified JSON output

#### Directory Structure

```plain
dependency_resolver/
├── __main__.py                       # CLI entry point
├── core/
│   ├── interfaces.py         # Abstract base classes
│   └── orchestrator.py       # Main orchestrator
├── executors/
│   ├── host_executor.py
│   ├── docker_executor.py
│   └── docker_compose_executor.py
└── detectors/
    ├── pip_detector.py
    ├── npm_detector.py
    ├── dpkg_detector.py
    ├── apk_detector.py
    ├── docker_compose_detector.py
    └── docker_info_detector.py
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
  "_container-info": {
    "name": "nginx-container",
    "image": "nginx:latest",
    "hash": "sha256:2cd1d97f893f70cee86a38b7160c30e5750f3ed6ad86c598884ca9c6a563a501"
  },
  "docker-compose": {
    "scope": "compose",
    "dependencies": {
      "backend": {
          "version": "latest",
          "hash": "a1b2c3d4e5f6"
      }
    },
    // ...
  },
  "dpkg": {
    "scope": "system",
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
      "scope": "project",
      "location": "/home/user/venv/lib/python3.12/site-packages",
      "hash": "a1b2c3d4e5f6789012345678901234ab",
      "dependencies": {
      "numpy": {
          "version": "1.3.3"
      }
    },
    // ...
  },
  "npm": {
    "scope": "project",
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

### Schema Field Definitions

#### Scope Field

All package manager outputs include a `scope` field indicating the installation scope:

- **`"system"`**: System-wide packages (apt/dpkg, apk, globally installed pip/npm)
- **`"project"`**: Project-specific packages (virtual environments, local node_modules)
- **`"compose"`**: Container orchestration images (Docker Compose, Podman Compose)
- **`"container"`**: Individual container metadata (transformed to `_container-info` format in output)

#### Location Field

The `location` field is only present when `scope` is `"project"`, providing the specific path to the project-local installation directory.

#### Hash Field

- **Individual package hashes**: Included when retrievable from package manager (e.g., dpkg md5sums, Docker image hashes)
- **Location-based hashes**: Generated for project scope installations to detect directory changes
- **System scope**: No location-based hashes (individual package hashes only where available)

#### Container Info Format

For Docker environments, container metadata is automatically included in a simplified format:

```json
{
  "_container-info": {
    "name": "container-name",
    "image": "nginx:latest",
    "hash": "sha256:2cd1d97f893f70cee86a38b7160c30e5750f3ed6ad86c598884ca9c6a563a501"
  }
}
```

**Key characteristics:**

- **Always included**: Container info is present by default in Docker analysis
- **Simplified format**: Uses flattened structure, not standard detector format
- **Underscore prefix**: `_container-info` distinguishes it from package managers
- **Container-only mode**: Use `--only-container-info` for metadata-only extraction

## Implementation Constraints

### Technical Constraints

1. **Read-Only Operations**: See [ADR-0003](docs/adr/0003-read-only-operations.md) for the complete read-only constraint policy
2. **Unix-Based Systems**: See [ADR-0004](docs/adr/0004-unix-only-support.md) for platform support scope

### Hash Handling Strategy

The dependency resolver uses a multi-tiered hash generation strategy for change detection and integrity verification. See [ADR-0005](docs/adr/0005-dependency-hash-strategy.md) for the complete rationale and individual detector documentation for implementation details.

**Key Points**:

- Individual package hashes only if retrievable from package manager
- Location-based hashes for package manager installations
- APT MD5 extraction approach (see [docs/detectors/dpkg_detector.md](docs/detectors/dpkg_detector.md))
- SHA256 format using full 64-character hashes

### Logging Strategy

- Print debug statements about the availability of package managers if the option `--debug` is provided

### Error Handling Strategy

- If the provided input parameters are invalid or the environment is not available, exit with an error message and the exit code 1
- Errors while checking for packages should always be caught

## Future plans

See [TODOS.md](TODOS.md).

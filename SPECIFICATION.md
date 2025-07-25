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
- Operating Systems with their common package managers: Ubuntu/Debian
- Container images: Docker and Podman (with hash + tags methodology)

### Environment Support

- Primary: Docker containers (using container hash/ID or name)
- Secondary: Host system analysis
- Future: Podman containers, Docker/Podman Compose stacks

## Design Approach

### Architecture Decision

Runtime Snapshot vs. Source File Parsing: The team decided on a runtime snapshot approach where the resolver analyzes running environments rather than parsing source files. This captures:

- Actually installed packages (not just declared ones)
- Runtime-loaded dependencies
- System-specific variations (ARM vs x64, firewall restrictions, etc.)

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
   - `PipDetector`: Python packages via `pip list --format=freeze`
     - Automatically detects and uses virtual environments by searching for `pyvenv.cfg` files
     - Searches common venv directory names: `venv`, `.venv`, `env`, `.env`, `virtualenv`
     - Uses the virtual environment's pip executable when available
   - `NpmDetector`: Node.js packages via `npm list --json --depth=0`
   - `AptDetector`: System packages via `dpkg-query`
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
├── detectors/
│   ├── pip_detector.py
│   ├── npm_detector.py
│   ├── apt_detector.py
│   └── docker_compose_detector.py
└── utils/
    ├── hash_utils.py         # Hash generation utilities
    └── command_utils.py      # Command execution helpers
```

#### Detection Strategy

- **Auto-Discovery**: Each detector checks availability before execution
- **Error Isolation**: Failed detectors don't affect others (catch all exceptions)
- **Priority Order**: System packages → Language-specific → Container orchestration
- **Working Directory**: All detectors respect `--working-dir` parameter

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
       // ...
    }
  },
  "pip": {
      "location": "/home/user/venv",
      "dependencies": {
      "numpy": {
          "version": "1.3.3",
          "hash": "d7d87d66d767s5d67as8789a7s89d7as98d"
      }
    },
    // ...
  },
  "npm": {
    "location": "/app/frontend",
    "dependencies": {
      "react": {
        "version": "18.2.0",
        "hash": "e7a2e5c8f4b0a1c9d3e2f1b8a7c6d9e2"
      },
      "lodash": {
        "version": "4.17.21",
        "hash": "f1c8b9a2d4e7c5b3e9f2a1b8c7d6e4f3"
      }
    },
    // ...
  },
  // ...
}
```

## Implementation Constraints

### Technical Constraints

1. No Downloads: Avoid downloading files from internet
2. No Installations: Avoid installing additional tools on target systems
3. Read-Only Operations: All operations should be read-only on target environment
4. Unix-Based Systems: It's sufficient to target Linux/Unix-based systems only

### Hash Handling Strategy

- The goal is to get unique identifiers for each package
- Check first if hashes can be retrieved locally from the package manager
- If that's not possible and the package manager reuses filenames for same versions a fallback mechanism is required: directory-based hashing
  - example Python: PyPI doesn't reuse filenames for same versions -> version numbers are sufficient

### Logging Strategy

- Print debug statements about the availability of package managers if the option `--debug` is provided

### Error Handling Strategy

- If the provided input parameters are invalid or the environment is not available, exit with an error message and the exit code 1
- Errors while checking for packages should always be caught

## Future plans

- Support for Podman, Docker Compose, Podman Compose
- Extend the set of supported package managers with the common ones for Go, PHP and Java
- Support more operating systems: RedHat Linux, openSUSE
- Add extraction of some relevant environment variables
- Handle containers without shells or removed package managers
  - Parse available log files (e.g. /var/lib/dpkg/status)
- Add configuration file
  - use Dependabot configuration as an inspiration (<https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference>)
  - Configure which package management systems should be checked
  - Configurable paths for package managers (like a path for venv resolution)
  - Override default commands (e.g., change from `pip list --format=freeze`)
  - Make it configurable, if the JSON output is pretty-printed or not (at the start pretty-print is default)
  - Add different log levels

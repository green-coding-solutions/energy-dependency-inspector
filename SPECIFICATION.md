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

- Programming Languages with their common package managers: Python, JavaScript, Go, PHP, Java
- Operating Systems with their common package managers: Ubuntu/Debian, RedHat Linux, openSUSE
- Container images: Docker and Podman (with hash + tags methodology)

### Environment Support

- Primary: Docker containers (using container hash/ID)
- Secondary: Host system analysis
- Future: Podman containers, Docker Compose stacks

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

- **environment_type**: The type of environment you want to inspect. Can be either `docker` or `podman`
- **environment_identifier**: The unique identifier of the environment. For `docker` and `podman` it is the container run id (short or full)
- **options**:
  - `--working-dir <working-dir>`: executes the checks inside the given working directory

Examples:

- `dependency_resolver.py docker a1b2c3d4e5f6` (Docker container)
- `dependency_resolver.py` (host system, no parameters)
- `dependency_resolver.py --working-dir /tmp/repo` (setting working directory)

### Execution Method

- Modular check/dump routines for each package manager
  - abstraction layer is required to separate the check/dump logic from the environment specific execution (e.g. using the docker library to run the checks inside containers)
- `docker` Python library is used

### JSON Output Schema

```json
{
  "docker-compose": {
      "location": "global",
      "dependencies": {
      "ubuntu": {
          "version": "latest",
          "hash": "das7892234890sad890fa0s98903284092"
      }
    },
    // ...
  },
  "system": {
    "location:": "global",
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

- Python: Version numbers sufficient (PyPI doesn't reuse filenames for same versions)
- Other Managers: May need hash resolution from package registries
- Fallback: Directory-based hashing if needed

## Future plans

- Handle containers without shells or removed package managers
- Add possible for configuration
  - Configurable paths for package managers (like a path for venv resolution), use Dependabot configuration as an inspiration (<https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference>)
  - Override default commands (e.g., change from `pip list --format=freeze`)

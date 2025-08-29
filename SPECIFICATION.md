# Project Specification

## Problem Statement

The [Green Metrics Tool](https://github.com/green-coding-solutions/green-metrics-tool) (GMT) currently cannot detect dependency changes because while repositories are fixed via git hash, source/package manager files without version pinning appear unchanged to GMT even when actual installed versions differ over time.

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
- Secondary: Host system analysis
- Future: Podman containers

## Design Approach

### Architecture Decisions

**Runtime Snapshot vs. Source File Parsing**: See [ADR-0001](docs/technical/architecture/adr/0001-runtime-snapshot-approach.md) for the decision to analyze running environments rather than parsing source files.

**Modular Architecture**: See [ADR-0002](docs/technical/architecture/adr/0002-modular-detector-architecture.md) for the modular detector architecture with abstract base classes and auto-discovery.

**Dependency Hash Strategy**: See [ADR-0005](docs/technical/architecture/adr/0005-dependency-hash-strategy.md) for the multi-tiered approach to change detection and integrity verification.

### Command Interface

```sh
python3 -m dependency_resolver <environment_type> <environment_identifier> <options>
```

Basic usage:

- **Host system**: `python3 -m dependency_resolver`
- **Docker container**: `python3 -m dependency_resolver docker nginx`

Supported environments: `host`, `docker` (future: `podman`)

For complete CLI usage, options, and examples, see [docs/usage/cli-guide.md](docs/usage/cli-guide.md).

### Architecture Overview

The system uses a modular architecture with detector-based package manager detection, environment-agnostic executors, and coordinated orchestration.

For complete architecture documentation, see [docs/technical/architecture/overview.md](docs/technical/architecture/overview.md) and [docs/technical/adding-new-detectors.md](docs/technical/adding-new-detectors.md).

### JSON Output Schema

The tool outputs structured JSON with detected package managers and their dependencies:

```json
{
  "_container-info": { "name": "nginx-container", "image": "nginx:latest", "hash": "sha256:..." },
  "dpkg": { "scope": "system", "dependencies": { "curl": { "version": "7.81.0-1ubuntu1.18 amd64" } } },
  "pip": { "scope": "project", "location": "/app/venv/lib/python3.12/site-packages", "dependencies": { "numpy": { "version": "1.3.3" } } }
}
```

For complete JSON schema documentation, field definitions, and examples, see [docs/usage/output-format.md](docs/usage/output-format.md).

### Key Schema Concepts

- **Scope**: `"system"` (system-wide packages) or `"project"` (project-specific packages)
- **Location**: Path to project-local installations (project scope only)
- **Hash**: Dependency integrity verification when available
- **Container Info**: Docker metadata included as `_container-info`

## Implementation Constraints

### Technical Constraints

1. **Read-Only Operations**: See [ADR-0003](docs/technical/architecture/adr/0003-read-only-operations.md) for the complete read-only constraint policy
2. **Unix-Based Systems**: See [ADR-0004](docs/technical/architecture/adr/0004-unix-only-support.md) for platform support scope

### Hash Strategy

Hashes are used for dependency change detection and integrity verification. See [ADR-0005](docs/technical/architecture/adr/0005-dependency-hash-strategy.md) for the complete multi-tiered strategy.

### Logging Strategy

- Print debug statements about the availability of package managers if the option `--debug` is provided

### Error Handling Strategy

- If the provided input parameters are invalid or the environment is not available, exit with an error message and the exit code 1
- Errors while checking for packages should always be caught

## Future plans

See [TODOS.md](TODOS.md).

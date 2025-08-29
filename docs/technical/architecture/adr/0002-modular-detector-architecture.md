# ADR-0002: Modular Detector Architecture

## Status

Accepted

## Context

The dependency resolver needs to support multiple package managers across different environments. Architecture options considered:

1. Monolithic approach with hardcoded package manager logic
2. Plugin-based system with dynamic loading
3. Modular architecture with abstract base classes and auto-discovery

## Decision

We will implement a modular architecture using abstract base classes with auto-discovery and error isolation:

**Core Components**:

- `PackageManagerDetector`: Abstract interface for all package manager implementations
- `EnvironmentExecutor`: Abstract interface for command execution in different environments
- `Orchestrator`: Main orchestrator that coordinates detection and extraction

**Detection Flow**:

1. Check usability (combines OS compatibility and package manager availability)
2. Extract dependencies
3. Check system scope (for efficient scope determination)

## Rationale

This modular approach provides extensibility while maintaining reliability through systematic validation and error isolation.

**Key Design Principles**:

- **Auto-Discovery**: Available detectors automatically check if their package manager exists
- **Combined Validation**: Each detector validates both OS compatibility and tool availability in single `is_usable()` check
- **Error Isolation**: Failed detectors don't affect others (comprehensive exception handling)
- **Priority Ordering**: Container orchestration → System packages → Language-specific packages
- **Working Directory Respect**: All detectors honor `working_dir` parameter
- **Scope Efficiency**: Separate `has_system_scope()` method for efficient scope checking

**Current Detector Implementations**:

- `DpkgDetector`: Debian/Ubuntu system packages (system scope)
- `ApkDetector`: Alpine Linux system packages (system scope)
- `PipDetector`: Python packages with virtual environment detection (project/system scope)
- `NpmDetector`: Node.js packages with intelligent package manager detection (project/system scope)

**Interface Contracts**:

- `PackageManagerDetector.is_usable()`: Combined OS compatibility and package manager availability check
- `PackageManagerDetector.get_dependencies()`: Dependency extraction with error handling
- `PackageManagerDetector.has_system_scope()`: Efficient system scope determination
- `EnvironmentExecutor.execute_command()`: Environment-agnostic command execution
- `EnvironmentExecutor.path_exists()`: Cross-environment path existence checking

## Consequences

**Positive**:

- Easy to add new package managers without modifying existing code
- Systematic validation prevents runtime failures
- Error isolation ensures partial results even with some detector failures
- Clear separation of concerns between detection and execution
- Efficient scope checking prevents unnecessary dependency extraction
- Cross-environment compatibility through executor abstraction
- Intelligent package manager conflict avoidance (e.g., npm vs yarn detection)

**Negative**:

- Additional complexity compared to monolithic approach
- More abstract classes and interfaces to maintain
- Potential performance overhead from systematic validation (mitigated by efficient scope checking)

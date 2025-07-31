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
- `DependencyResolver`: Main orchestrator that coordinates detection and extraction

**Detection Flow**:

1. Check pre-requirements
2. Check availability
3. Extract dependencies

## Rationale

This modular approach provides extensibility while maintaining reliability through systematic validation and error isolation.

**Key Design Principles**:

- **Auto-Discovery**: Available detectors automatically check if their package manager exists
- **Pre-Requirements Validation**: Each detector validates OS compatibility before attempting detection
- **Error Isolation**: Failed detectors don't affect others (comprehensive exception handling)
- **Priority Ordering**: System packages → Language-specific → Container orchestration
- **Working Directory Respect**: All detectors honor `--working-dir` parameter

**Interface Contracts**:

- `PackageManagerDetector.meets_requirements()`: OS compatibility checks
- `PackageManagerDetector.is_available()`: Package manager existence validation
- `PackageManagerDetector.get_dependencies()`: Dependency extraction with error handling
- `EnvironmentExecutor.execute_command()`: Environment-agnostic command execution

## Consequences

- **Positive**: Easy to add new package managers without modifying existing code
- **Positive**: Systematic validation prevents runtime failures
- **Positive**: Error isolation ensures partial results even with some detector failures
- **Positive**: Clear separation of concerns between detection and execution
- **Negative**: Additional complexity compared to monolithic approach
- **Negative**: More abstract classes and interfaces to maintain
- **Negative**: Potential performance overhead from systematic validation

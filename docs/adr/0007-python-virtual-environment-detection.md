# ADR-0007: Python Virtual Environment Detection Strategy

## Status

Proposed

## Context

Python projects often use virtual environments to isolate dependencies. The dependency resolver needs to detect and use the correct Python environment. Options considered:

1. Always use system pip
2. Require manual specification of virtual environment path
3. Automatic virtual environment detection with fallback to system pip

## Decision

We will implement automatic virtual environment detection using the following strategy:

**Detection Priority**:

1. **Explicit specification**: Use manually specified virtual environment path when provided
2. **Environment-aware detection**: Use `VIRTUAL_ENV` environment variable in containerized environments (Docker), but not on host systems to avoid interference from the current shell's environment
3. **Local project search**: Search for virtual environments within the project directory using standard naming conventions
4. **External environment search**: Search common external virtual environment locations when analyzing projects with working directories
5. **System fallback**: Use system pip if no virtual environment is detected

**Virtual Environment Identification**: Uses `pyvenv.cfg` files as the definitive indicator of Python virtual environments

## Rationale

Automatic detection ensures the dependency resolver captures the actual Python environment being used by the project, which is critical for accurate dependency tracking.

**Key Benefits**:

- **Accuracy**: Captures dependencies from the actual environment being used by the project
- **Context Awareness**: Distinguishes between host and containerized execution environments
- **Convenience**: Automatic detection for standard setups, manual override when needed
- **Flexibility**: Supports various virtual environment tools and naming conventions
- **Reliability**: Uses `pyvenv.cfg` as the definitive virtual environment indicator
- **Non-Interference**: Avoids false positives from host shell environments when analyzing external projects

## Consequences

- **Positive**: Environment-aware detection prevents interference from host shell environments
- **Positive**: Supports both local and externally managed virtual environments
- **Positive**: Manual override capability for non-standard setups
- **Positive**: Works correctly in containerized environments (Docker)
- **Positive**: Captures project-specific dependencies rather than system-wide packages
- **Negative**: Additional complexity in environment detection logic
- **Negative**: May require manual specification for non-standard virtual environment setups

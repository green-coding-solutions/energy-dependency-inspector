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

**Detection Method**:

- Search for `pyvenv.cfg` files to identify virtual environments
- Search common virtual environment directory names: `venv`, `.venv`, `env`, `.env`, `virtualenv`
- Use the virtual environment's pip executable when available
- Fallback to system pip if no virtual environment is detected

## Rationale

Automatic detection ensures the dependency resolver captures the actual Python environment being used by the project, which is critical for accurate dependency tracking.

**Key Benefits**:

- **Accuracy**: Captures dependencies from the actual environment being used
- **Convenience**: No manual configuration required for standard setups
- **Flexibility**: Supports various virtual environment naming conventions
- **Reliability**: `pyvenv.cfg` is the definitive indicator of Python virtual environments
- **Fallback Safety**: Gracefully falls back to system pip when no venv is found

**Search Strategy**:

1. Look for `pyvenv.cfg` files in working directory and subdirectories
2. Check standard virtual environment directory names
3. Verify pip executable exists in detected virtual environment
4. Use virtual environment pip if found, otherwise use system pip

## Consequences

- **Positive**: Automatic detection works with most Python project setups
- **Positive**: Captures project-specific dependencies rather than system-wide packages
- **Positive**: Supports multiple virtual environment naming conventions
- **Positive**: Reliable detection using `pyvenv.cfg` standard
- **Negative**: May not detect non-standard virtual environment setups
- **Negative**: Additional complexity in environment detection logic
- **Negative**: Potential for false positives in directories with multiple virtual environments

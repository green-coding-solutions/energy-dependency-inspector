# Adding New Package Manager Detectors

This guide provides a comprehensive plan for adding new package manager detectors to the energy-dependency-inspector system.

## Overview

The energy-dependency-inspector uses a modular detector architecture where each package manager has its own detector class that implements the `PackageManagerDetector` interface. This design allows for easy extensibility while maintaining consistent behavior across all detectors.

## Prerequisites

Before adding a new detector, ensure you understand:

1. **Architecture Decision Records (ADRs)**: Review `/docs/technical/architecture/adr/` for design principles
2. **Existing Detectors**: Study `/energy_dependency_inspector/detectors/` implementations
3. **Interface Contracts**: Understand `PackageManagerDetector` in `/energy_dependency_inspector/core/interfaces.py`
4. **Testing Patterns**: Review `/tests/detectors/` structure

## Step 1: Implement the Detector Class

### 1.1 Create the Detector File

Create `/energy_dependency_inspector/detectors/{package_manager}_detector.py` implementing the `PackageManagerDetector` interface with these required methods:

- `__init__(self, debug: bool = False)`: Initialize detector with debug flag
- `is_usable()`: Check if package manager is available in the environment
- `get_dependencies()`: Extract package dependencies with versions and metadata
- `is_os_package_manager()`: Determine if detector manages OS-level packages
- `get_name()`: Return the detector name (inherited from base class)

### 1.2 Key Implementation Considerations

**Scope Determination**:

- `system`: System-wide packages (dpkg, apk, yum, etc.)
- `project`: Project-specific packages (npm, pip with venv, etc.)

**Working Directory Handling**:

- Always respect the `working_dir` parameter
- Use it for package manager commands when appropriate
- For project-scoped detectors, check for project files in `working_dir`

**Hash Implementation** (see ADR-0005):

- **Tier 1**: Use authentic hashes from package managers when available
- **Tier 2**: Generate location-based hashes for project scope
- **Tier 3**: Skip hashes when not feasible

**Error Handling**:

- Always handle command execution failures gracefully
- Return empty dependencies dict on errors, not exceptions
- Log debug information when `self.debug` is True

**Read-Only Constraint** (see ADR-0003):

- No downloads, installations, or system modifications
- Use only existing tools and metadata
- Work with current environment state as-is

## Step 2: Register the Detector

### 2.1 Update the Orchestrator

Add your detector to the detectors list in `/energy_dependency_inspector/core/orchestrator.py` following the priority order:

**Priority Ordering**:

1. Container information (docker-info)
2. System packages (dpkg, apk, yum, etc.)
3. Language-specific packages (pip, npm, etc.)

Reference existing detectors like `DpkgDetector`, `ApkDetector`, `PipDetector`, and `NpmDetector` for import and initialization patterns.

### 2.2 Update Package Imports

Add to `/energy_dependency_inspector/detectors/__init__.py` if needed.

## Step 3: Create Documentation

### 3.1 Detector Documentation

Create `/docs/technical/detectors/{package_manager}_detector.md` with the following structure:

**Required Sections:**

- **Overview**: Brief description of the package manager and detector purpose
- **Scope**: Document system/project scope and target environments
- **Detection Logic**: Explain usability checks and dependency extraction
- **Hash Strategy**: Document which tier is implemented (Tier 1/Authentic, Tier 2/Location-based, or Tier 3/None)
- **Limitations**: Known limitations or edge cases
- **Example Output**: JSON sample showing expected output format

**Expected JSON Output Format:**

Standard output includes `scope`, `dependencies` dict with package names and versions, and optional `hash` and `location` fields. Reference existing detector documentation for specific examples.

## Step 4: Implement Tests

### 4.1 Test Directory Structure

Create `/tests/detectors/{package_manager}/` with:

- `__init__.py`
- `README.md`
- `test_{package_manager}_docker_detection.py`

### 4.2 Docker Test Implementation

Create a test class inheriting from `DockerTestBase` in `/tests/common/docker_test_base.py`. Key components:

- Choose appropriate Docker image containing your package manager
- Use `DockerExecutor` to run tests in containerized environment
- Test via `Orchestrator` to ensure integration works correctly
- Validate expected output format and required fields
- Include proper cleanup and error handling

Reference existing detector tests in `/tests/detectors/` for implementation patterns.

### 4.3 Test README

Create `/tests/detectors/{package_manager}/README.md` documenting:

**Content Structure:**

- **Docker Test**: Description of Docker-based testing approach
- **Image Used**: Document the Docker image used for testing
- **Test Commands**: List the commands tested
- **Running Tests**: Instructions for executing the tests

**Test Execution Patterns:**

Reference pytest command patterns from existing detector test READMEs for running individual tests, verbose output, and full test suites.

## Step 5: Integration and Testing

### 5.1 Manual Testing

**Basic Testing Steps:**

1. **Activate environment**: Use virtual environment activation
2. **Test detector directly**: Import and run your detector with `debug=True`
3. **Test via CLI**: Use debug mode to see detailed output
4. **Test in target environment**: Use appropriate executor (host/docker) for your use case

### 5.2 Run Test Suite

Run detector-specific tests, full test suite, and linting checks. Reference CLAUDE.md for specific commands and patterns.

## Step 6: Documentation and Performance

### 6.1 Update Documentation

- Add your detector to `/README.md` in the supported package managers section

### 6.2 Performance Testing (Optional)

If a `performance-analysis/` directory exists, add a benchmark script following the existing patterns in that directory. This is typically added later if performance analysis is needed.

## Common Implementation Patterns

### System-Wide Detectors

Reference `DpkgDetector` and `ApkDetector` implementations:

- Always return `True` for `is_os_package_manager()`
- Extract from system package database
- Usually ignore `working_dir` for system packages
- Return `{"scope": "system", "dependencies": {}}`

### Project-Scoped Detectors

Reference `PipDetector` and `NpmDetector` implementations:

- Check for project files in `working_dir` to determine scope
- Extract project dependencies when project files found
- Fall back to system scope when no project context
- Return appropriate scope with location for project dependencies

## Debugging Tips

1. **Use Debug Mode**: Always test with `debug=True` during development
2. **Check Command Output**: Verify package manager commands work in target environment
3. **Test Edge Cases**: Empty environments, permission issues, missing tools
4. **Validate JSON Output**: Ensure output follows expected schema
5. **Test Both Scopes**: If supporting both project and system scope

Use `python3 -m energy_dependency_inspector --debug` to see detailed execution flow.

## Quality Checklist

Before submitting your detector:

- [ ] Implements all required interface methods
- [ ] Handles errors gracefully (no exceptions in normal operation)
- [ ] Respects read-only constraint (ADR-0003)
- [ ] Implements appropriate hash strategy (ADR-0005)
- [ ] Has comprehensive tests with Docker environment
- [ ] Follows existing code style and patterns
- [ ] Has complete documentation
- [ ] Added to orchestrator registration
- [ ] Passes all linting checks
- [ ] Manual testing in target environments
- [ ] Performance considerations documented

## Support and References

**Key Reference Files:**

- `/energy_dependency_inspector/detectors/` - Existing detector implementations
- `/energy_dependency_inspector/core/interfaces.py` - PackageManagerDetector interface
- `/energy_dependency_inspector/core/orchestrator.py` - Detector registration
- `/docs/technical/architecture/adr/` - Architecture decision records
- `/tests/detectors/` - Test patterns and examples
- `/tests/common/docker_test_base.py` - Docker testing base class

**Debug Commands:**

- `python3 -m energy_dependency_inspector --debug` - Full debug output
- `source venv/bin/activate` - Activate development environment
- `pre-commit run --files $(git diff --name-only --diff-filter=ACMR HEAD)` - Run linting

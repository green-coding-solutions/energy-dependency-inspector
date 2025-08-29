# Adding New Package Manager Detectors

This guide provides a comprehensive plan for adding new package manager detectors to the dependency resolver system.

## Overview

The dependency resolver uses a modular detector architecture where each package manager has its own detector class that implements the `PackageManagerDetector` interface. This design allows for easy extensibility while maintaining consistent behavior across all detectors.

## Prerequisites

Before adding a new detector, ensure you understand:

1. **Architecture Decision Records (ADRs)**: Review `/docs/adr/` for design principles
2. **Existing Detectors**: Study `/dependency_resolver/detectors/` implementations
3. **Interface Contracts**: Understand `PackageManagerDetector` in `/dependency_resolver/core/interfaces.py`
4. **Testing Patterns**: Review `/tests/detectors/` structure

## Step 1: Implement the Detector Class

### 1.1 Create the Detector File

Create `/dependency_resolver/detectors/{package_manager}_detector.py`:

```python
from typing import Optional, Any
from ..core.interfaces import EnvironmentExecutor, PackageManagerDetector


class {PackageManager}Detector(PackageManagerDetector):
    """Detector for {Package Manager Description}."""

    NAME = "{package_manager}"

    def __init__(self, debug: bool = False):
        self.debug = debug

    def is_usable(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """Check if {package_manager} is usable in the environment."""
        # Implement OS compatibility check if needed
        # Check if package manager tool is available
        _, _, exit_code = executor.execute_command("{package_manager} --version", working_dir)
        return exit_code == 0

    def get_dependencies(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> dict[str, Any]:
        """Extract {package_manager} dependencies with versions."""
        # Implement dependency extraction logic
        # Return format: {"scope": "system|project", "location": "path", "dependencies": {}, "hash": "sha256"}
        pass

    def has_system_scope(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
        """Check if this detector operates at system scope."""
        # Return True for system-wide package managers (dpkg, apk)
        # Return False or implement logic for project-scoped managers (pip, npm)
        pass
```

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

Add your detector to `/dependency_resolver/core/orchestrator.py`:

```python
from ..detectors.{package_manager}_detector import {PackageManager}Detector

class Orchestrator:
    def __init__(self, ...):
        # Add to detectors list in priority order
        self.detectors: list[PackageManagerDetector] = [
            DockerInfoDetector(),
            DpkgDetector(),
            ApkDetector(),
            {PackageManager}Detector(debug=debug),  # Add here
            PipDetector(venv_path=venv_path, debug=debug),
            NpmDetector(debug=debug),
        ]
```

**Priority Ordering**:

1. Container information (docker-info)
2. System packages (dpkg, apk, yum, etc.)
3. Language-specific packages (pip, npm, etc.)

### 2.2 Update Package Imports

Add to `/dependency_resolver/detectors/__init__.py` if needed.

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

**Example JSON Output Format:**

```json
{
  "scope": "system",
  "dependencies": {
    "package1": {"version": "1.0.0", "hash": "sha256..."},
    "package2": {"version": "2.0.0", "hash": "sha256..."}
  },
  "hash": "sha256..."
}
```

## Step 4: Implement Tests

### 4.1 Test Directory Structure

Create `/tests/detectors/{package_manager}/`:

```plain
tests/detectors/{package_manager}/
├── __init__.py
├── README.md
└── test_{package_manager}_docker_detection.py
```

### 4.2 Docker Test Implementation

Create `/tests/detectors/{package_manager}/test_{package_manager}_docker_detection.py`:

```python
"""Test {package_manager} Docker container dependency detection."""

import os
import sys
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from dependency_resolver.executors import DockerExecutor
from dependency_resolver.core.orchestrator import Orchestrator
from tests.common.docker_test_base import DockerTestBase

try:
    import docker
except ImportError:
    docker = None  # type: ignore


class Test{PackageManager}DockerDetection(DockerTestBase):
    """Test {package_manager} dependency detection using Docker container environment."""

    # Choose appropriate Docker image that has your package manager
    TEST_IMAGE = "appropriate/docker-image"

    @pytest.mark.skipif(docker is None, reason="Docker not available")
    def test_{package_manager}_docker_container_detection(self, request: pytest.FixtureRequest) -> None:
        """Test {package_manager} dependency detection inside a Docker container."""

        verbose_output = self.setup_verbose_output(request)
        container_id = None

        try:
            container_id = self.start_container(self.TEST_IMAGE, additional_args=[])
            self.wait_for_container_ready(container_id, "{package_manager} --version", max_wait=60)

            executor = DockerExecutor(container_id)
            orchestrator = Orchestrator(debug=False, skip_system_scope=False)

            result = orchestrator.resolve_dependencies(executor)

            if verbose_output:
                self.print_verbose_results("DEPENDENCY RESOLVER OUTPUT:", result)

            self._validate_{package_manager}_dependencies(result)

        finally:
            if container_id:
                self.cleanup_container(container_id)

    def _validate_{package_manager}_dependencies(self, result: Dict[str, Any]) -> None:
        """Validate {package_manager} dependencies in the result."""
        assert "{package_manager}" in result

        {package_manager}_result = result["{package_manager}"]
        assert "scope" in {package_manager}_result
        assert "dependencies" in {package_manager}_result

        # Add specific validations for your package manager
        dependencies = {package_manager}_result["dependencies"]
        assert isinstance(dependencies, dict)

        # Validate expected packages if known
        # assert "expected-package" in dependencies
```

### 4.3 Test README

Create `/tests/detectors/{package_manager}/README.md` with:

**Content Structure:**

- **Docker Test**: Description of Docker-based testing approach
- **Image Used**: Document the Docker image used for testing
- **Test Commands**: List the commands tested (e.g., `{package_manager} --version`)
- **Running Tests**: Instructions for executing the tests

**Test Execution Commands:**

- Run all tests: `pytest tests/detectors/{package_manager}/`
- Verbose output: `pytest tests/detectors/{package_manager}/ --verbose-resolver`
- Specific test: `pytest tests/detectors/{package_manager}/test_{package_manager}_docker_detection.py::Test{PackageManager}DockerDetection::test_{package_manager}_docker_container_detection`

## Step 5: Integration and Testing

### 5.1 Manual Testing

**Basic Testing Steps:**

1. **Activate environment**: `source venv/bin/activate`
2. **Test detector directly**: Import and run your detector with `debug=True`
3. **Test via CLI**: `python3 -m dependency_resolver --debug`
4. **Test in target environment**: Use appropriate executor (host/docker) for your use case

### 5.2 Run Test Suite

```bash
# Run your detector tests
pytest tests/detectors/{package_manager}/

# Run all tests
pytest

# Run linting
pre-commit run --files $(git diff --name-only --diff-filter=ACMR HEAD)
```

## Step 6: Documentation and Performance

### 6.1 Update Documentation

- Add your detector to `/README.md` in the supported package managers section

### 6.2 Performance Testing (Optional)

If a `performance-analysis/` directory exists, add a benchmark script following the existing patterns in that directory. This is typically added later if performance analysis is needed.

## Common Implementation Patterns

### System-Wide Detectors (dpkg, apk style)

```python
def has_system_scope(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
    return True  # Always system scope

def get_dependencies(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> dict[str, Any]:
    # Extract from system package database
    # Usually ignore working_dir for system packages
    result = {"scope": "system", "dependencies": {}}
```

### Project-Scoped Detectors (pip, npm style)

```python
def has_system_scope(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> bool:
    if working_dir:
        # Check for project files in working_dir
        return not self._has_project_files(executor, working_dir)
    return True  # Default to system if no working_dir

def get_dependencies(self, executor: EnvironmentExecutor, working_dir: Optional[str] = None) -> dict[str, Any]:
    if working_dir and self._has_project_files(executor, working_dir):
        # Extract project dependencies
        location = self._resolve_absolute_path(executor, working_dir)
        return {"scope": "project", "location": location, "dependencies": {}}
    else:
        # Extract system dependencies
        return {"scope": "system", "dependencies": {}}
```

## Debugging Tips

1. **Use Debug Mode**: Always test with `debug=True` during development
2. **Check Command Output**: Verify package manager commands work in target environment
3. **Test Edge Cases**: Empty environments, permission issues, missing tools
4. **Validate JSON Output**: Ensure output follows expected schema
5. **Test Both Scopes**: If supporting both project and system scope

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

## Support

For questions or assistance:

1. Review existing detector implementations in `/dependency_resolver/detectors/`
2. Check ADRs in `/docs/adr/` for architectural decisions
3. Examine test patterns in `/tests/detectors/`
4. Follow the debug output with `python3 -m dependency_resolver --debug`

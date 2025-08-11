# Dependency Resolver Development Guide

## Quick Start

```bash
source venv/bin/activate
python3 dependency_resolver.py --debug
```

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run specific detectors for testing
python3 dependency_resolver.py docker <container_name>
python3 dependency_resolver.py host --skip-system-scope

# Execute linting and formatting
pre-commit run --files $(git diff --name-only --diff-filter=ACMR HEAD)
```

## Tech Stack

Python with venv, pip, and pytest (Unix-only)

## Code Principles

**Write self-documenting code:**

- Use descriptive variable and function names
- Structure code to reveal intent
- Add comments only when code doesn't speak for itself (explain WHY, not WHAT)

**Keep it simple:**

- Choose the simplest solution that works
- Avoid abstractions until duplication becomes painful
- Minimize external dependencies

**Be explicit:**

- Use type annotations
- Validate inputs early
- Surface clear error messages

## Debugging

```bash
# Debug specific detector issues
python3 dependency_resolver.py --debug

# Test individual detectors (modify main temporarily)
python3 -c "from detectors.dpkg_detector import DpkgDetector; print(DpkgDetector().get_name())"
```

## Style & Workflow

- **Follow PEP8**
- **Activate venv first**: `source venv/bin/activate` at the beginning of a new session
- **Lint after each task** - always ensure good code quality
- **Commit frequently**
- **Add tests for new functionality**

## Key Directories

- `detectors/` - Package manager detection implementations
- `executors/` - Environment execution adapters
- `core/` - Base interfaces and orchestrator
- `tests/` - Test suites organized by detector
- `docs/adr/` - Architecture decision records

## Project Files

- [SPECIFICATION.md](./SPECIFICATION.md) - Requirements and constraints
- [README.md](./README.md) - Update after adding features

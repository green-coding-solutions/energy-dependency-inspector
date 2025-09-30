# Energy Dependency Inspector Development Guide

## Quick Start

```bash
source venv/bin/activate
python3 -m energy_dependency_inspector --debug
```

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run specific detectors for testing
python3 -m energy_dependency_inspector docker <container_name>
python3 -m energy_dependency_inspector host --skip-os-packages --skip-hash-generation

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
python3 -m energy_dependency_inspector --debug

# Test individual detectors (modify main temporarily)
python3 -c "from energy_dependency_inspector.detectors.dpkg_detector import DpkgDetector; print(DpkgDetector().get_name())"
```

## Style & Workflow

- **Follow PEP8**
- **Activate venv first**: `source venv/bin/activate` at the beginning of a new session
- **Lint after each task** - always ensure good code quality
- **Commit frequently**
- **Add tests for new functionality**
- **If you do measurements, persist the used scripts / commands** - measurements should be repeatable

## Key Directories

- `energy_dependency_inspector/detectors/` - Package manager detection implementations
- `energy_dependency_inspector/executors/` - Environment execution adapters
- `energy_dependency_inspector/core/` - Base interfaces and orchestrator
- `tests/` - Test suites organized by component (detectors, executors, integration, specialized)
- `docs/guides/` - User guides (quick start, troubleshooting)
- `docs/usage/` - Detailed usage documentation (CLI, API, output format)
- `docs/technical/` - Technical documentation including:
  - `docs/technical/architecture/adr/` - Architecture decision records
  - `docs/technical/detectors/` - Individual detector documentation
  - `docs/technical/architecture/` - System architecture documentation
  - `docs/technical/adding-new-detectors.md` - Guide for implementing new package manager detectors

## Project Files

- [README.md](./README.md) - Overview with links to detailed docs
- [SPECIFICATION.md](./SPECIFICATION.md) - Requirements and constraints

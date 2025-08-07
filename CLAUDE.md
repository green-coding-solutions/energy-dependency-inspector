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

## Style & Workflow

- **Follow PEP8**
- **Activate venv first**: `source venv/bin/activate` at the beginning of a new task
- **Lint after each task** - always ensure good code quality
- **Commit frequently**

## Project Files

- [SPECIFICATION.md](./SPECIFICATION.md) - Requirements and constraints
- [./docs/adr/](./docs/adr/) - Architecture decisions (add new ADRs for significant changes)
- [README.md](./README.md) - Update after adding features

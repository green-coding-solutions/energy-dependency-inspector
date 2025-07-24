# Dependency Resolver Development Guide

## Tech Stack

- Python
  - venv for an isolated environment
  - pip for dependency management
  - pytest for test execution

## Guidelines

- **Simplicity first** – Prefer the simplest data structures and APIs that work
- **Avoid needless abstractions** – Refactor only when duplication hurts
- **Minimize dependencies** – Before adding a dependency, ask "Can we do this with what we already have?"
- **Consistency wins** – Follow existing naming and file-layout patterns; if you must diverge, document why
- **Explicit over implicit** – Favor clear, descriptive names and type annotations over clever tricks
- **Fail fast** – Validate inputs, throw early, and surface actionable errors
- **Let the code speak** – If you need to write a comment, explain WHY the code does something instead of WHAT it does. If you need a multi-paragraph comment, refactor until intent is obvious.

## Code style

- adhere to the standard PEP8 python conventions
- rules for quotes:
  - use `'` for fixed constant strings
  - use `"` for modifiable and format strings
  - break this rule if needed to avoid escaping

## Workflow

- commit often
- use pylint to check for clean code before commit code
- prefer running single tests, not the whole test suite, for performance

## Instructions for Claude

- see the file [SPECIFICATION](./SPECIFICATION.md) for important project requirements, design approaches and implementation constraints
- use the file [TASKS](./TASKS.md) to track your done work and the progress of ongoing tasks

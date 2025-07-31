# Dependency Resolver Development Guide

## Bash Commands

- `source venv/bin/activate` to activate Python venv. Execute it before you ran a pip or Python related command.
- `source venv/bin/activate && python3 dependency_resolver.py --debug` to start the tool in debug mode (analyzes the host system, prints out debug statements and an excerpt of the resulting JSON)
- `source venv/bin/activate && pre-commit run --files $(git diff --name-only --diff-filter=ACMR)` to check for linting errors

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

## Workflow

- commit often
- prefer running single tests, not the whole test suite, for performance

## Compatibility

- support is only needed for Unix-based systems

## Instructions for Claude

- see the file [SPECIFICATION](./SPECIFICATION.md) for important project requirements, design approaches and implementation constraints
- in the folder [./docs/adr/](./docs/adr/) you can find architecture decision records. Add a new record if there is a new significant architecture decision.
- don't forget to update [README.md](./README.md) after new features were added

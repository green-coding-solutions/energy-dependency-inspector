# Contributing to energy-dependency-inspector

Thank you for your interest in contributing to the energy-dependency-inspector project! This guide will help you get started with development and understand our contribution process.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/green-coding-solutions/energy-dependency-inspector
cd energy-dependency-inspector

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install for development (includes dev dependencies)
pip install -e ".[dev]"
```

The `-e` flag installs the package in editable mode, allowing you to make changes to the code and test them without reinstalling the package.

## Pre-commit Hooks

We use pre-commit hooks to ensure code quality and consistency. All Python files are automatically linted and formatted before each commit.

### Installing Pre-commit Hooks

```bash
# Activate virtual environment first
source venv/bin/activate

# Install pre-commit hooks (this is done automatically if you installed dev dependencies)
pre-commit install

# Test the hooks on the changed files (optional)
pre-commit run --files $(git diff --name-only --diff-filter=ACMR)

# Test the hooks on all files (optional)
pre-commit run --all-files
```

### What the Hooks Do

Our pre-commit configuration includes:

- **Black** - Code formatting with 120 character line length
- **Pylint** - Code quality checks and linting
- **MyPy** - Type checking
- **General hooks** - Trailing whitespace removal, end-of-file fixes, etc.

The hooks will automatically run when you commit changes. If any hook fails, the commit will be blocked until you fix the issues.

## Development Workflow

### Running Tests

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=energy_dependency_inspector

# Run specific test file
pytest tests/detectors/pip/test_pip_docker_detection.py
```

### Code Quality Checks

While pre-commit hooks will run automatically, you can also run these tools manually:

```bash
# Activate virtual environment first
source venv/bin/activate

# Run pylint (as specified in project guidelines)
pylint energy_dependency_inspector/

# Run type checking
mypy energy_dependency_inspector/

# Format code
black energy_dependency_inspector/
```

### Project Structure

```plain
energy-dependency-inspector/
├── pyproject.toml
├── requirements*.txt
├── energy_dependency_inspector/             # Main package
│   ├── __main__.py                  # CLI entry point
│   ├── core/                        # Orchestration and interfaces
│   ├── detectors/                   # Package manager detectors
│   └── executors/                   # Environment executors
├── tests/
├── docs/
└── venv/
```

## Development Guidelines

Please refer to the [CLAUDE.md](./CLAUDE.md) file for detailed development guidelines, including:

- **Simplicity first** – Prefer the simplest data structures and APIs that work
- **Avoid needless abstractions** – Refactor only when duplication hurts
- **Minimize dependencies** – Before adding a dependency, ask "Can we do this with what we already have?"
- **Consistency wins** – Follow existing naming and file-layout patterns
- **Explicit over implicit** – Favor clear, descriptive names and type annotations
- **Fail fast** – Validate inputs, throw early, and surface actionable errors

### Code Style

- Adhere to standard PEP8 Python conventions
- Use single quotes (`'`) for fixed constant strings
- Use double quotes (`"`) for modifiable and format strings
- Break the quote rule if needed to avoid escaping

## Contribution Process

1. **Fork the repository** and create a feature branch
2. **Make your changes** following the development guidelines
3. **Run tests** to ensure your changes don't break existing functionality
4. **Commit your changes** (pre-commit hooks will run automatically)
5. **Push to your fork** and create a pull request
6. **Address any feedback** from code review

## Adding New Package Manager Detectors

To add support for a new package manager, follow the comprehensive guide in [docs/technical/adding-new-detectors.md](./docs/technical/adding-new-detectors.md). This guide covers:

- Implementation patterns and interface requirements
- Testing strategies with Docker environments
- Documentation standards
- Integration with the orchestrator system

## Getting Help

If you have questions or need help:

- Check the [SPECIFICATION.md](./SPECIFICATION.md) for project requirements and design approaches
- Review [docs/technical/adding-new-detectors.md](./docs/technical/adding-new-detectors.md) for detector implementation guidance
- Check [docs/technical/](./docs/technical/) for architecture documentation and ADRs
- Review existing code for patterns and conventions
- Open an issue for discussion if you're unsure about an approach

## Thank You

Your contributions help make energy-dependency-inspector better for everyone. We appreciate your time and effort!

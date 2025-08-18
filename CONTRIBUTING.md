# Contributing to dependency-resolver

Thank you for your interest in contributing to the dependency-resolver project! This guide will help you get started with development and understand our contribution process.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/green-coding-solutions/dependency-resolver
cd dependency-resolver

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install for development (includes dev dependencies)
pip install -e ".[dev]"

# For Docker support (optional)
pip install -e ".[docker]"

# For Podman support (optional, not implemented yet)
pip install -e ".[podman]"
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

- **Black** - Code formatting with 100 character line length
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
pytest --cov=dependency_resolver

# Run specific test file
pytest tests/test_pip_detector.py
```

### Code Quality Checks

While pre-commit hooks will run automatically, you can also run these tools manually:

```bash
# Activate virtual environment first
source venv/bin/activate

# Run pylint (as specified in project guidelines)
pylint dependency_resolver/

# Run type checking
mypy dependency_resolver/ --ignore-missing-imports --no-strict-optional

# Format code
black dependency_resolver/
```

### Project Structure

```plain
dependency-resolver/
├── pyproject.toml
├── requirements*.txt
├── dependency_resolver/             # Main package
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

## Getting Help

If you have questions or need help:

- Check the [SPECIFICATION.md](./SPECIFICATION.md) for project requirements and design approaches
- Review existing code for patterns and conventions
- Open an issue for discussion if you're unsure about an approach

## Thank You

Your contributions help make dependency-resolver better for everyone. We appreciate your time and effort!

# pip Detector Tests

Tests pip dependency detection in Docker containers and virtual environments.

## Running Tests

```bash
pytest tests/detectors/pip/
```

## Requirements

- Docker running
- `python:3.11-slim` container

## Test Coverage

- Container pip package detection
- Virtual environment discovery (venv paths, environment variables)
- Package installation validation

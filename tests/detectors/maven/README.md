# Maven Detector Tests

Tests Maven dependency detection using Docker containers with Maven CLI and pom.xml parsing.

## Running Tests

```bash
pytest tests/detectors/maven/
```

## Requirements

- Docker running
- `maven:3.9-eclipse-temurin-17` and `eclipse-temurin:17-jre` images

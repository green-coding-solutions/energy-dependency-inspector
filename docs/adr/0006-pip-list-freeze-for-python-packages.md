# ADR-0006: Use pip list --format=freeze for Python Package Detection

## Status

Accepted

## Context

The dependency resolver needs to extract Python package information. Several pip command options were considered:

- `pip list`: Default human-readable format
- `pip list --format=json`: JSON format with detailed metadata
- `pip list --format=freeze`: Requirements.txt compatible format
- `pip freeze`: Legacy freeze format command

## Decision

We will use `pip list --format=freeze` to retrieve Python package dependencies.

## Rationale

The freeze format provides the most suitable output for dependency tracking in our use case, offering a clean package==version format that is both machine-readable and widely recognized.

Key advantages:

- **Clean format**: Simple `package==version` format without extraneous metadata
- **Machine readable**: Easy to parse programmatically with regex or string splitting
- **Standard format**: Compatible with requirements.txt format, familiar to Python developers
- **Consistent output**: Stable format across different pip versions
- **Minimal overhead**: Faster than JSON format with detailed metadata
- **Version precision**: Includes exact installed versions with proper operators

## Consequences

- **Positive**: Simple, reliable parsing of Python package information
- **Positive**: Output format familiar to Python developers
- **Positive**: Compatible with standard Python tooling expectations
- **Positive**: Minimal performance overhead compared to verbose formats
- **Negative**: Limited to basic package name and version information
- **Negative**: No additional metadata like installation location or dependencies

# ADR-0001: Runtime Snapshot vs Source File Parsing

## Status

Accepted

## Context

The energy-dependency-inspector needs to analyze project dependencies. Two approaches were considered:

1. **Source File Parsing**: Analyze package manager files (requirements.txt, package.json, etc.)
2. **Runtime Snapshot**: Analyze running environments to capture actually installed packages

## Decision

We will use a runtime snapshot approach where the resolver analyzes running environments rather than parsing source files.

## Rationale

Runtime snapshot analysis provides more accurate dependency information by capturing what is actually installed and loaded in the target environment, rather than what is declared in source files.

Key advantages:

- **Actually installed packages**: Captures packages that are installed but not declared, or versions that differ from declarations
- **Runtime-loaded dependencies**: Detects dynamically loaded or conditional dependencies
- **System-specific variations**: Accounts for architecture differences (ARM vs x64), network restrictions, and environment-specific installations
- **Real-world accuracy**: Reflects the actual runtime state rather than intended state
- **Complete picture**: Includes system packages, language packages, and container dependencies together

## Consequences

- **Positive**: More accurate dependency detection reflecting real runtime state
- **Positive**: Captures implicit and conditional dependencies
- **Positive**: Detects version drift between declarations and actual installations
- **Negative**: Requires access to running environments (containers or host systems)
- **Negative**: Cannot analyze dependencies without executing/running the environment
- **Negative**: More complex implementation than simple file parsing

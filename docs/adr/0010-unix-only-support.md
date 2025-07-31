# ADR-0010: Unix-Only System Support

## Status

Proposed

## Context

The dependency resolver needs to define its target platform scope. Platform support options considered:

1. Cross-platform support including Windows, macOS, and Linux
2. Unix-based systems only (Linux, macOS, BSD variants)
3. Linux-only support

## Decision

We will limit support to Unix-based systems only, including Linux distributions, macOS, and BSD variants.

## Rationale

Focusing on Unix-based systems allows for simpler implementation while covering the primary use cases for containerized and server environments where the Green Metrics Tool operates.
The Green Metrics Tool is the main purpose of this project.

**Scope Definition**:

- **Supported**: Linux distributions (Ubuntu, Debian, Alpine, CentOS, etc.)
- **Supported**: macOS (for development environments)
- **Supported**: BSD variants (FreeBSD, OpenBSD, etc.)
- **Not Supported**: Windows systems

**Implementation Benefits**:

- **Consistent command interface**: Unix systems share similar command-line tools and patterns
- **Container focus**: Aligns with containerized deployment patterns (Docker/Podman primarily run on Unix)
- **Simplified path handling**: Unix path conventions are consistent across supported platforms
- **Standard package managers**: Unix systems have established package management patterns

**Technical Justification**:

- Green Metrics Tool primarily targets server and containerized environments
- Container orchestration platforms predominantly run on Unix-based systems
- Package managers targeted (apt, apk, pip, npm) have consistent behavior on Unix systems

## Consequences

- **Positive**: Simplified implementation without Windows-specific code paths
- **Positive**: Consistent command execution patterns across supported platforms
- **Positive**: Reduced testing matrix and maintenance overhead
- **Positive**: Focus on primary deployment environments
- **Negative**: Excludes Windows development environments
- **Negative**: Cannot analyze Windows containers or systems
- **Negative**: May limit adoption in mixed-platform organizations

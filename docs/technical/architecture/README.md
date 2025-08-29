# Architecture Documentation

This section contains comprehensive architecture documentation including system design and architectural decisions.

## System Architecture

- **[Architecture Overview](overview.md)** - High-level system design, component relationships, and data flow

## Architectural Decisions

Architecture Decision Records (ADRs) document the key decisions made during the development of this system:

- **[ADR-0001: Runtime Snapshot Approach](adr/0001-runtime-snapshot-approach.md)** - Decision to analyze running environments rather than source files
- **[ADR-0002: Modular Detector Architecture](adr/0002-modular-detector-architecture.md)** - Pluggable detector design with abstract interfaces
- **[ADR-0003: Read-Only Operations](adr/0003-read-only-operations.md)** - Constraint to never modify target environments
- **[ADR-0004: Unix-Only Support](adr/0004-unix-only-support.md)** - Platform support scope and rationale
- **[ADR-0005: Dependency Hash Strategy](adr/0005-dependency-hash-strategy.md)** - Multi-tiered approach to change detection and integrity verification

## Key Architectural Principles

1. **Runtime Snapshot Approach** - Analyze actual installed packages rather than configuration files
2. **Modular Design** - Package manager detectors as independent, pluggable components
3. **Environment Abstraction** - Support multiple execution environments (host, Docker) through unified interface
4. **Read-Only Constraint** - Never modify the target environment during analysis
5. **Graceful Degradation** - Failed detectors don't prevent other detectors from working
6. **Multi-Tiered Integrity** - Use best available hash strategy for each package manager

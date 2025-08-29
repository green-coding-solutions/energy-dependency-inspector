# Technical Documentation

This section contains technical documentation for developers and contributors.

## Architecture

- **[Architecture Documentation](architecture/)** - System design, component relationships, and architectural decisions

## Implementation Details

- **[Detector Documentation](detectors/)** - Package manager detector implementations
- **[Implementation Analyses](analyses/)** - Detailed analysis of implementation decisions

## Development

- **[Adding New Detectors](adding-new-detectors.md)** - Guide for implementing new package manager detectors

## Directory Structure

```plain
technical/
├── README.md                   # This file
├── adding-new-detectors.md     # Guide for implementing new detectors
├── architecture/               # System architecture documentation
│   ├── overview.md             # High-level architecture overview
│   └── adr/                    # Architecture Decision Records
│       ├── 0001-runtime-snapshot-approach.md
│       ├── 0002-modular-detector-architecture.md
│       ├── 0003-read-only-operations.md
│       ├── 0004-unix-only-support.md
│       └── 0005-dependency-hash-strategy.md
├── analyses/                   # Implementation analysis documents
│   └── npm_hash_implementation_analysis.md
└── detectors/                  # Detector-specific documentation
    ├── apk_detector.md
    ├── docker_info_detector.md
    ├── dpkg_detector.md
    ├── npm_detector.md
    └── pip_detector.md
```

## Key Design Principles

Based on our Architecture Decision Records:

1. **Runtime Snapshot Approach** - Analyze current state without installations
2. **Modular Detector Architecture** - Pluggable package manager detectors
3. **Read-Only Operations** - Never modify the target environment
4. **Unix-Only Support** - Focus on Unix-like systems for simplicity
5. **Tiered Hash Strategy** - Use best available hash method per package manager

## For Contributors

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for development setup and contribution guidelines.

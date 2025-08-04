# ADR-0005: Multi-Tiered Hash Generation Strategy

## Status

Proposed

## Context

The dependency resolver needs to generate hashes for dependency tracking and change detection. Different approaches were considered:

1. Generate synthetic hashes for all packages
2. Only use hashes provided by package managers
3. Multi-tiered approach combining package-specific and location-based hashes

## Decision

We will implement a multi-tiered hash generation strategy with the following rules:

- **Individual Package Hashes**: Only include if retrievable directly from package manager
- **Package Manager Location Hashes**: Generate one hash per package manager based on installation location
- **Skip Global Location Hashes**: No location hash for system-wide installations
- **SHA256 Format**: All hashes use full 64-character SHA256 format

## Rationale

This approach balances accuracy with practicality by leveraging native package manager capabilities while providing consistent change detection through location-based hashing.

**Individual Package Hash Rules**:

- **APT/dpkg**: Extract MD5 hashes from `/var/lib/dpkg/info/{package}.md5sums`, combine into SHA256
- **APK**: No individual hashes (not provided by APK)
- **pip**: No individual hashes (not available locally from PyPI)
- **npm**: No individual hashes implemented

**Location Hash Rules**:

- **Actual Directory Paths**: Hash directory contents (e.g., `find {location} -type f -name '*.py' | sort`)
- **Global Locations**: Skip hash generation for system-wide installations
- **Fallback**: Use location string hash if directory listing fails

## Consequences

- **Positive**: Leverages native package manager capabilities for maximum accuracy
- **Positive**: Provides consistent change detection through location hashing
- **Positive**: Avoids synthetic hashes that might not reflect actual package state
- **Positive**: Optimizes by skipping hashes for stable global installations
- **Negative**: Inconsistent hash availability across different package managers
- **Negative**: Additional complexity in hash generation logic
- **Negative**: Location hashing may be slow for large directories

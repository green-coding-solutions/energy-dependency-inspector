# ADR-0004: Use apk list --installed for Alpine Package Information

## Status

Accepted

## Context

The dependency resolver needs to query installed packages on Alpine Linux systems. Several options exist:

- `apk list --installed`: Shows detailed package information including architecture, license, and status
- `apk info -v`: Displays simple package-version pairs for installed packages
- `apk info` (without -v): Shows only package names without versions

## Decision

We will use `apk list --installed` to retrieve package information from Alpine Linux systems.

## Rationale

`apk list --installed` provides comprehensive package information including architecture details that are essential for dependency resolution. While the output includes additional metadata (license, status), the architecture information is crucial for cross-platform compatibility and aligns with our approach in other package managers like dpkg.

Key advantages:

- **Architecture information**: Includes package architecture for cross-platform compatibility
- **Comprehensive data**: Package name, version, and architecture in consistent format
- **Consistent approach**: Aligns with dpkg detector's inclusion of architecture information
- **Future-proof**: Additional metadata available if needed for future features
- **Reliability**: Direct query of installed package database

## Consequences

- **Positive**: Includes architecture information for better dependency resolution
- **Positive**: Consistent with dpkg detector approach for cross-platform compatibility
- **Positive**: Reliable package information without dependency on repository state
- **Positive**: Additional metadata available for future enhancement
- **Negative**: Alpine Linux specific (not portable to other package managers)
- **Negative**: More verbose output requires additional parsing compared to `apk info -v`

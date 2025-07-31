# ADR-0004: Use apk info -v for Alpine Package Information

## Status

Accepted

## Context

The dependency resolver needs to query installed packages on Alpine Linux systems. Several options exist:

- `apk list --installed`: Shows detailed package information including architecture, license, and status
- `apk info -v`: Displays simple package-version pairs for installed packages
- `apk info` (without -v): Shows only package names without versions

## Decision

We will use `apk info -v` to retrieve package information from Alpine Linux systems.

## Rationale

`apk info -v` provides the cleanest and most parseable output format for installed packages on Alpine systems, displaying simple `package-version` pairs without extraneous metadata. Unlike `apk list --installed` (which includes architecture, license, and status information), `apk info -v` offers consistent formatting ideal for automated parsing and reliable system snapshots.

Key advantages:

- **Clean output**: Simple `package-version` format without extra metadata
- **Consistent parsing**: Predictable output structure for automated processing
- **Performance**: Minimal overhead compared to verbose listing commands
- **Focused data**: Only essential package and version information
- **Reliability**: Direct query of installed package database

## Consequences

- **Positive**: Simple, consistent output format perfect for automated parsing
- **Positive**: Fast execution with minimal system overhead
- **Positive**: Reliable package information without dependency on repository state
- **Negative**: Alpine Linux specific (not portable to other package managers)
- **Negative**: Limited to basic package-version information (no architecture, licenses, etc.)

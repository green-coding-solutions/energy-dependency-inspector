# ADR-0003: Use dpkg-query -W -f for Debian/Ubuntu Package Information

## Status

Accepted

## Context

The dependency resolver needs to query installed packages on Debian/Ubuntu systems. Several options exist:

- `dpkg -l`: Lists packages in human-readable format
- `apt list --installed`: Shows packages from APT cache/repository perspective
- `dpkg-query -W -f`: Queries the dpkg database with customizable output format

## Decision

We will use `dpkg-query -W -f` to retrieve package information from Debian/Ubuntu systems.

## Rationale

`dpkg-query` provides the most reliable and scriptable interface to the authoritative package database. Unlike `dpkg -l` (fixed human-readable format) or `apt list --installed` (repository-dependent cache), `dpkg-query` offers customizable output formatting perfect for automated parsing while querying the definitive source of installed package information.

Key advantages:

- **Authoritative source**: Queries the actual dpkg database, not repository cache
- **Scriptable output**: Custom format strings allow precise control over output structure
- **Performance**: Direct database access without formatting overhead
- **Reliability**: Not dependent on repository state or network connectivity
- **Consistency**: Output format remains stable across different system configurations

## Consequences

- **Positive**: Reliable, fast, and easily parseable package information
- **Positive**: No dependency on APT repository state or network access
- **Positive**: Consistent behavior across different Debian/Ubuntu versions
- **Negative**: Debian/Ubuntu specific (not portable to other package managers)
- **Negative**: Requires understanding of dpkg-query format strings for maintenance

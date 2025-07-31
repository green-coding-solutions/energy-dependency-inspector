# ADR-0008: APT MD5 Hash Extraction from Package Files

## Status

Accepted

## Context

The dependency resolver needs to generate hashes for APT/dpkg packages to detect changes. Several approaches were considered:

1. Generate synthetic hashes based on package name and version
2. Use package file modification times
3. Extract existing MD5 hashes from package metadata files
4. Skip individual package hashes for APT packages

## Decision

We will extract MD5 hashes from `/var/lib/dpkg/info/{package_name}.md5sums` files and combine them into a single SHA256 hash for each package.

## Rationale

This approach leverages the existing package integrity metadata that dpkg maintains, providing authentic hash information rather than synthetic values.

**Implementation Details**:

- Read MD5 hash values from `/var/lib/dpkg/info/{package}.md5sums` files
- Combine all file MD5 hashes from the package into a single string
- Generate SHA256 hash from the combined MD5 values
- Only include hash field if the md5sums file exists and is readable
- Skip hash generation if md5sums file is missing or inaccessible

**Key Advantages**:

- **Authentic hashes**: Uses dpkg's own integrity checking metadata
- **File-level accuracy**: Reflects actual installed file contents
- **Change detection**: Sensitive to any file modifications within the package
- **Standard approach**: Leverages existing dpkg infrastructure

## Consequences

- **Positive**: Provides authentic package integrity information
- **Positive**: Detects changes at the file level within packages
- **Positive**: Uses existing dpkg metadata without additional system load
- **Positive**: Graceful degradation when md5sums files are unavailable
- **Negative**: Hash availability depends on dpkg metadata file existence
- **Negative**: Additional I/O operations to read md5sums files
- **Negative**: APT-specific approach not portable to other package managers

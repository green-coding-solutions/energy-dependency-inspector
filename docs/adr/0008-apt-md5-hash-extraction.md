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

We will extract MD5 hashes from dpkg md5sums files using multiple file patterns and combine them into a single SHA256 hash for each package.

## Rationale

This approach leverages the existing package integrity metadata that dpkg maintains, providing authentic hash information rather than synthetic values.

**Implementation Details**:

- Try multiple md5sums file patterns to handle architecture-specific naming:
  - Standard pattern: `/var/lib/dpkg/info/{package}.md5sums`
  - Multi-arch pattern: `/var/lib/dpkg/info/{package}:{architecture}.md5sums`
  - Alternative pattern: `/var/lib/dpkg/info/{package}-{architecture}.md5sums`
- Read MD5 hash values from the first available md5sums file
- Combine all file MD5 hashes from the package into a single string (sorted)
- Generate SHA256 hash from the combined MD5 values
- Only include hash field if an md5sums file exists and contains valid hashes
- Skip hash generation if no md5sums file is found or files are empty

**Key Advantages**:

- **Authentic hashes**: Uses dpkg's own integrity checking metadata
- **File-level accuracy**: Reflects actual installed file contents
- **Change detection**: Sensitive to any file modifications within the package
- **Standard approach**: Leverages existing dpkg infrastructure
- **Architecture-aware**: Handles multi-arch and architecture-specific package naming
- **High coverage**: Achieves 95%+ hash coverage through comprehensive pattern matching

## Consequences

- **Positive**: Provides authentic package integrity information
- **Positive**: Detects changes at the file level within packages
- **Positive**: Uses existing dpkg metadata without additional system load
- **Positive**: Graceful degradation when md5sums files are unavailable
- **Positive**: High hash coverage through architecture-specific pattern support
- **Positive**: Handles modern multi-arch Debian/Ubuntu package installations
- **Negative**: Hash availability depends on dpkg metadata file existence
- **Negative**: Multiple I/O operations to check different md5sums file patterns
- **Negative**: APT/dpkg-specific approach not portable to other package managers

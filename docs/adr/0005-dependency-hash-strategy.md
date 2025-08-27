# ADR-0005: Dependency Hash Strategy

## Status

Accepted

## Context

The dependency resolver needs to track changes in software dependencies across different environments and time periods. Several approaches exist for detecting when dependencies have changed:

1. **No change detection**: Only track package names and versions
2. **Timestamp-based detection**: Use modification times to detect changes
3. **Hash-based detection**: Generate cryptographic hashes to detect changes
4. **External signature verification**: Rely on package manager signatures only

## Decision

We will implement a multi-tiered hash-based strategy for dependency change detection and integrity verification:

**Tier 1 - Individual Package Hashes**: Use authentic hashes from package managers when available
**Tier 2 - Location-Based Hashes**: Generate hashes based on installation directory contents when individual hashes unavailable
**Tier 3 - No Hash**: Skip hash generation for packages where neither approach is feasible

## Rationale

### Why Hash-Based Detection

**Change Detection Accuracy**: Hashes provide precise change detection that version numbers alone cannot. Two installations with identical package versions can have different actual contents due to:

- Different package manager cache states
- Partial installations or corrupted files
- Security patches applied to same version
- Different build variants of the same version

**Environment Comparison**: Enables reliable comparison of dependency states across development, staging, and production environments.

**Build Reproducibility**: Supports reproducible builds by detecting when the actual dependency environment differs from expected state.

**Security Benefits**: Provides integrity verification to detect tampering or corruption.

### Why Multi-Tiered Approach

**Package Manager Limitations**: Not all package managers provide individual package hashes:

- **APT/DPKG**: Provides MD5 hashes via `/var/lib/dpkg/info/*.md5sums` files
- **APK**: No individual package hashes available
- **PIP**: PyPI hashes not stored locally after installation
- **NPM**: Provides SHA-512 integrity hashes in package-lock.json files but parsing adds complexity (see [NPM Hash Analysis](../analyses/npm_hash_implementation_analysis.md))

**Authentic vs Synthetic Hashes**: We prefer authentic hashes from package managers over self-generated ones because:

- **Authoritative**: Package managers maintain these for integrity checking
- **Standard**: Uses existing infrastructure rather than custom solutions
- **Reliable**: Reflects actual installed file contents as verified by package manager
- **Performance**: Avoids expensive file-by-file hashing of large packages

### Why Location-Based Hashing

When individual package hashes are unavailable, location-based hashing provides:

**Fallback Change Detection**: Still detects changes in the overall dependency environment
**Directory-Level Integrity**: Captures the complete state of package installation directories
**Cross-Package Changes**: Detects modifications affecting multiple packages in shared locations
**Virtual Environment Tracking**: Essential for Python virtual environments where pip doesn't provide individual hashes

**Location Hash Implementation**:

- Hash directory structure and file metadata (size, path, symlink targets)
- Exclude volatile files (cache, logs, temporary files, compiled bytecode)
- Use environment-independent sorting for consistent results
- Focus on package files while excluding packaging metadata that changes frequently

### Why We Don't Generate Individual Package Hashes

**Performance Cost**: Hashing large packages (especially system packages) would be computationally expensive
**Storage Overhead**: Individual file hashing would require significant I/O and storage
**Redundancy**: Package managers already perform integrity checking where needed
**Maintenance Burden**: Custom hashing would require handling edge cases across different package formats
**False Precision**: Self-generated hashes might give false confidence when package managers don't validate them

## Hash Generation Rules

### Individual Package Hashes

- **DPKG**: Extract MD5 hashes from `*.md5sums` files, combine into SHA256
- **APK**: Not available (skip individual hashes)
- **PIP**: Not available locally (skip individual hashes)
- **NPM**: Available via package-lock.json/node_modules/.package-lock.json but not currently implemented
- **Docker Images**: Use Docker image ID as authentic hash

### Location-Based Hashes

- **Project Scope**: Generate for virtual environments, project directories
- **System Scope**: Skip for system-wide installations (stable and large)
- **Hash Format**: SHA256 of sorted directory contents metadata
- **Exclusions**: Cache files, logs, temporary files, compiled bytecode

### Hash Format

- All hashes use SHA256 format (64-character hexadecimal)
- Consistent hashing across different environments and platforms

## Alternatives Considered

### No Change Detection

**Pros**: Simple, no computational overhead
**Cons**: Cannot detect environment drift, corruption, or configuration changes

### Timestamp-Based Detection

**Pros**: Low computational cost, built into filesystems
**Cons**: Unreliable across environments, affected by deployment processes, time synchronization issues

### External Signature Verification Only

**Pros**: Leverages existing package manager security
**Cons**: Not all package managers provide signatures, doesn't detect local modifications

### Universal Individual Package Hashing

**Pros**: Maximum precision for change detection
**Cons**: Prohibitive performance cost, redundant with package manager integrity checking

## Consequences

**Positive**:

- Accurate change detection beyond version numbers
- Leverages authentic package manager integrity metadata where available
- Efficient fallback strategy for environments without individual hashes
- Supports reproducible builds and environment comparison
- Avoids performance penalties of universal package hashing

**Negative**:

- Inconsistent hash availability across different package managers
- Additional complexity in hash generation logic
- Location hashing may be slower for large directories
- Hash interpretation requires understanding the multi-tiered strategy

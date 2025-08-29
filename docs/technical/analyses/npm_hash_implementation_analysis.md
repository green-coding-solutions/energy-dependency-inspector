# NPM Hash Implementation Analysis

**Date**: August 27, 2025

## Executive Summary

This analysis evaluates whether implementing individual package hash retrieval for the `npm_detector` is feasible and aligns with the dependency resolver's principles. **Recommendation: No, do not implement individual package hashing at this time** due to npm's version immutability making the implementation cost unjustified for the common use case.

## Current State

The `npm_detector` (`npm_detector.py:87-72`) currently uses a location-based hashing strategy that hashes directory contents rather than individual package integrity hashes. This approach generates a SHA-256 hash of the sorted directory structure and file metadata, excluding volatile files like cache and logs.

## Available Hash Sources Analysis

### 1. NPM CLI Commands

#### Result: No viable option for installed package hashes

- `npm list --json --depth=0`: Provides package versions but no integrity hashes
- `npm view <package>`: Shows registry hashes but only for remote packages, not installed state
- `npm explain <package>`: Provides dependency tree information but no hash data

### 2. Package Lock Files

#### Result: Excellent source of authentic SHA-512 integrity hashes

Modern npm (v3+ lockfileVersion) provides integrity hashes in two locations:

- **Root level**: `package-lock.json` with complete dependency tree and integrity fields
- **Node modules level**: `node_modules/.package-lock.json` with installed package hashes

Example structure:

```json
{
  "packages": {
    "node_modules/lodash": {
      "version": "4.17.21",
      "resolved": "https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz",
      "integrity": "sha512-v2kDEe57lecTulaDIuNTPy3Ry4gLGJ6Z1O3vE1krgXZNrsQ+LFTGHVxVjcXPs17LhbZVGedAJv8XZ1tvj5FvSg==",
      "license": "MIT"
    }
  }
}
```

## NPM Version Immutability Analysis

### Registry-Level Immutability

#### Finding: NPM packages have conditional immutability with important exceptions

**Current npm Policy (2025):**

- **72-Hour Unpublish Window**: Packages can be unpublished within 72 hours if no other packages depend on them
- **Extended Unpublish**: Packages older than 72 hours can be unpublished if they meet specific criteria (no dependents)
- **Version Reuse Prohibition**: Once package@version is used, that version number can **never be reused**, even after unpublishing
- **Force Publishing**: `npm publish --force` flag was permanently removed
- **Private Registries**: May have different policies allowing overwrites

**Key Implication**: While you cannot directly overwrite a published version, the unpublish-then-publish cycle within 72 hours creates a window where **different content could theoretically exist for the same version number** during the transition period.

### Potential Content Variation Scenarios

Same-version-different-content scenarios can occur through several mechanisms:

#### 1. **Unpublish-Republish Window (72 Hours)**

- **Scenario**: Package unpublished within 72 hours, then different content published with new version
- **Risk**: Cached installations vs. new installations could have different content
- **Timeline**: Only possible within 72-hour window for new packages
- **Detection**: Integrity hash comparison would identify discrepancy

#### 2. **Private Registry Overwrites**

- **Scenario**: Private registries (Nexus, Artifactory, npm Enterprise) may allow version overwrites
- **Result**: Same version number with different content depending on registry configuration
- **Detection**: Hash comparison essential for private registry environments

#### 3. **Cache Corruption (Historical Issue)**

- **Legacy npm versions**: Local cache could become corrupted during failed downloads
- **Modern npm (5+)**: Self-healing cache with integrity verification reduces this issue
- **Current impact**: Minimal risk with modern npm installations

#### 4. **Git vs Registry Mismatch**

- **Scenario**: Package installed from git repository, later attempted from npm registry
- **Result**: Same version number but different source content
- **Detection**: Hash comparison would identify this discrepancy

#### 5. **Registry Source Differences**

- **Scenario**: Different registries serving same package version
- **Result**: Potentially different tarball contents
- **Detection**: Integrity hashes differ between registries

#### 6. **Local Development Overrides**

- **Scenario**: `npm link` or file path dependencies
- **Result**: Same version but locally modified content
- **Detection**: Hash comparison identifies modifications

#### 7. **Pre-release Version Overwrites**

- **Scenario**: Some registries allow overwriting pre-release versions (e.g., 1.0.0-beta.1)
- **Result**: Same pre-release version with different content
- **Detection**: Hash verification catches these changes

### Why Individual Hashes Matter

These scenarios demonstrate that **version numbers alone are insufficient** for dependency integrity verification. Hash-based detection provides:

1. **Corruption Detection**: Identifies corrupted or incomplete installations
2. **Source Verification**: Ensures packages match expected registry sources
3. **Tampering Detection**: Identifies unauthorized modifications
4. **Environment Consistency**: Verifies identical dependency states across environments

## Implementation Approaches Comparison

### Approach 1: Parse package-lock.json for Individual Hashes

**Pros:**

- ✅ Provides authentic npm-maintained SHA-512 integrity hashes (Tier 1 strategy per ADR-0005)
- ✅ More precise change detection than location-based hashing
- ✅ Consistent with `dpkg_detector`'s approach of using authentic package manager hashes
- ✅ Detects git/registry mismatches and cache corruption scenarios
- ✅ Lock files represent dependency "snapshot" state updated by npm commands
- ✅ Available in both root and node_modules locations for reliability

**Cons:**

- ❌ Requires file parsing instead of pure CLI commands
- ❌ Additional parsing complexity
- ❌ May not exist if project installed without package-lock generation

**Implementation Strategy:**

```python
def _get_npm_package_hashes(self, executor, working_dir):
    """Extract individual package hashes from package-lock.json"""
    search_dir = working_dir or "."

    # Try both possible locations (prioritize installed version)
    lock_files = [
        f"{search_dir}/node_modules/.package-lock.json",  # Installed state
        f"{search_dir}/package-lock.json"                 # Project root
    ]

    for lock_file in lock_files:
        if executor.path_exists(lock_file):
            stdout, _, exit_code = executor.execute_command(f"cat '{lock_file}'")
            if exit_code == 0:
                return self._parse_package_lock_hashes(stdout)
    return {}
```

### Approach 2: Enhanced CLI Command

**Pros:**

- ✅ Maintains pure CLI/snapshot consistency
- ✅ Uses live package manager state

**Cons:**

- ❌ No npm CLI command provides installed package hashes
- ❌ Would require complex combination of multiple commands
- ❌ Less reliable than direct lock file access

### Approach 3: Keep Current Location-Based Hashing

**Pros:**

- ✅ Already implemented and functional
- ✅ Detects changes in overall dependency environment
- ✅ Pure CLI approach

**Cons:**

- ❌ Less precise than individual package hashes
- ❌ Cannot detect git/registry mismatches or specific package corruption
- ❌ Doesn't leverage available authentic hashes
- ❌ Inconsistent with `dpkg_detector` individual hash strategy

## Alignment with Project Principles

### Multi-Tiered Hash Strategy (ADR-0005)

- **Tier 1**: ✅ Use authentic hashes from package managers when available
- **Tier 2**: ✅ Fallback to location-based hashing when individual hashes unavailable
- **Tier 3**: ✅ No hash when neither approach feasible

**npm_detector Status**: Currently implements Tier 2 only, despite Tier 1 being available

### Snapshot-Based Approach

- **Lock files represent npm's snapshot state**: Updated by npm commands, not manual edits
- **Parsing justification**: Similar to `dpkg_detector` parsing `*.md5sums` files
- **Authentic source**: Lock files are npm's authoritative record of installed state

### Consistency with Existing Detectors

- **`dpkg_detector`**: Parses files (`*.md5sums`) for individual package hashes
- **Docker detector**: Uses image IDs as authentic hashes
- **Precedent established**: File parsing for authentic hashes is acceptable

## Updated Recommendation: Deprioritize Individual Package Hashing

**Decision: Do not implement individual package hash parsing at this time.**

Based on npm's version immutability guarantee, the cost-benefit analysis does not support implementing individual package hashes for the common use case:

### Rationale for Deprioritization

**Version Immutability Reduces Value:**

- Public npm registry enforces permanent version immutability
- Once `package@version` is published, that version can never be reused
- Version numbers effectively serve as content identifiers for public registry packages
- **Key insight**: For public registry usage, `version === hash` correlation eliminates the primary benefit

**Cost vs. Benefit:**

- **Implementation cost**: Package-lock.json parsing, error handling, format conversion complexity
- **Maintenance cost**: Handling different lockfile versions, edge cases, file existence checks
- **Benefit**: Minimal for the dominant use case (public npm registry)

**Current Location-Based Hashing Suffices:**

- Detects environment changes, corruption, and local modifications
- Simpler implementation already in place and working
- Adequate for detecting the scenarios that actually occur in practice

### Limited Scope Where Individual Hashes Add Value

Individual package hashing would only provide significant benefit in these scenarios:

1. **Private registries** that allow version overwrites (organizational edge case)
2. **Mixed registry environments** (development complexity)
3. **Local development** with `npm link` (development-only scenario)

### Alternative Implementation Strategy

Instead of universal individual hash parsing, consider this conditional approach for future implementation:

**Phase 1** (current): Location-based hashing for all cases
**Phase 2** (if needed): Registry detection to identify private registry usage
**Phase 3** (if justified): Conditional individual hash parsing only for private registries

## Conclusion

**Individual package hash implementation for npm_detector is not recommended at this time** due to npm's version immutability making version numbers effectively equivalent to content hashes for the primary use case (public registry).

The current location-based hashing approach provides adequate change detection for practical scenarios while maintaining implementation simplicity. Future implementation could be reconsidered if private registry usage becomes a significant use case requiring individual package integrity verification.

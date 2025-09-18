# APK Detector

## Purpose & Scope

The APK detector identifies system packages managed by Alpine Linux's `apk` package manager. It provides comprehensive package information including architecture details for cross-platform dependency tracking.

## Implementation Approach

### Package Manager Detection

Uses `apk list --installed` to retrieve detailed package information including:

- Package name and version
- Architecture information (essential for cross-platform compatibility)
- Additional metadata (license, status) available for future enhancement

### Alternatives Considered

Several apk command options were evaluated:

- **`apk list --installed`**: Chosen for comprehensive package information including architecture
- **`apk info -v`**: Simple package-version pairs but lacks architecture details
- **`apk info`** (without -v): Only package names without versions

**Decision rationale**: `apk list --installed` provides comprehensive package information including architecture details essential for cross-platform compatibility, aligning with the dpkg detector's approach.

### OS Compatibility

Validates Alpine Linux environment by:

1. Checking `/etc/os-release` for "alpine" identifier
2. Fallback: checking for `/etc/alpine-release` file existence
3. Verifying `apk --version` command availability

### Architecture Inclusion Rationale

Including architecture information provides several advantages:

- **Cross-platform compatibility**: Essential for multi-arch environments
- **Consistency**: Aligns with dpkg detector approach
- **Future-proofing**: Additional metadata supports future enhancements
- **Reliability**: Direct query of installed package database

## Command Used

```bash
apk list --installed
```

**Output format example:**

```text
bash-5.2.15-r5 x86_64 {bash} (GPL-3.0-or-later)
musl-1.2.3-r2 x86_64 {musl} (MIT)
```

## Package Information Parsing

The detector parses the output format: `package-name-version [architecture] {status} (license)`

**Parsing logic:**

1. Split line on spaces to separate components
2. Extract package name and version from first component using `rsplit("-", 2)`
3. Architecture is the second component (if present)
4. Combine version and architecture: `version architecture`

**Example parsing:**

- Input: `bash-5.2.15-r5 x86_64 {bash} (GPL-3.0-or-later)`
- Package: `bash`
- Version: `5.2.15-r5 x86_64`

## Hash Generation

APK packages do not provide individual package hashes. The detector follows the multi-tiered hash generation strategy by:

- **Individual Package Hashes**: Not available (APK limitation)
- **Location Hashes**: Not applicable (system-wide packages)

## Environment Detection

### System Scope

APK always operates with system scope as it manages system-wide Alpine packages.

### Availability Check

The detector is usable when:

1. Running on Alpine Linux (OS validation)
2. `apk` command is available and functional

## Output Format

The detector returns a tuple: `(packages, metadata)`

**Packages:**

```json
[
  {
    "name": "bash",
    "version": "5.2.15-r5 x86_64",
    "type": "apk"
  },
  {
    "name": "musl",
    "version": "1.2.3-r2 x86_64",
    "type": "apk"
  }
]
```

**Metadata:**

```json
{}
```

Note: System-scoped packages have empty metadata as they don't have project-specific locations.

## Limitations & Constraints

- **Alpine Linux specific**: Not portable to other package managers
- **Verbose output**: Requires additional parsing compared to simple `apk info -v`
- **No individual hashes**: APK does not provide package integrity hashes
- **Architecture dependency**: Parsing depends on consistent architecture information format

## Error Handling

- Graceful degradation when `apk list --installed` fails
- Skips malformed lines and warning messages
- Continues processing remaining packages if individual package parsing fails
- Returns empty dependencies on command failure rather than throwing exceptions

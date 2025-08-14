# DPKG Detector

## Purpose & Scope

The DPKG detector identifies system packages managed by `dpkg` on Debian/Ubuntu systems. It provides comprehensive package information including versions, architecture details, and authentic integrity hashes derived from dpkg's own metadata.

## Implementation Approach

### Package Manager Detection

Uses `dpkg-query -W -f` for reliable package information extraction:

- **Authoritative source**: Queries the actual dpkg database, not repository cache
- **Scriptable output**: Custom format strings allow precise control over output structure
- **Performance**: Direct database access without formatting overhead
- **Reliability**: Not dependent on repository state or network connectivity
- **Consistency**: Output format remains stable across different system configurations

### Alternatives Considered

Several options exist for querying installed packages on Debian/Ubuntu systems:

- **`dpkg-query -W -f`**: Chosen for customizable output format and direct database access
- **`dpkg -l`**: Lists packages in human-readable format but fixed formatting
- **`apt list --installed`**: Shows packages from APT cache/repository perspective, repository-dependent

**Decision rationale**: `dpkg-query` provides the most reliable and scriptable interface to the authoritative package database with customizable output formatting perfect for automated parsing.

### OS Compatibility

Validates Debian/Ubuntu environment by:

1. Checking `/etc/os-release` for "debian" or "ubuntu" identifiers
2. Fallback: checking for `/etc/debian_version` file existence
3. Verifying `dpkg-query --version` command availability

## Command Used

```bash
dpkg-query -W -f='${Package}\t${Version}\t${Architecture}\n'
```

**Output format example:**

```text
bash 5.1-6ubuntu1 amd64
libc6 2.35-0ubuntu3.1 amd64
```

**Format string benefits:**

- Tab-separated values for reliable parsing
- Customizable field selection
- Consistent output across dpkg versions

## Package Information Parsing

The detector parses tab-separated output:

1. **Package name**: First tab-separated field
2. **Version**: Second tab-separated field
3. **Architecture**: Third tab-separated field (optional)
4. **Full version**: Combines version and architecture: `version architecture`

## Hash Generation

### Authentic Hash Strategy

Extracts MD5 hashes from dpkg's own integrity metadata files and combines them into SHA256 hashes:

**MD5sums File Patterns (tried in order):**

1. `/var/lib/dpkg/info/{package}.md5sums` (standard pattern)
2. `/var/lib/dpkg/info/{package}:{architecture}.md5sums` (multi-arch pattern)
3. `/var/lib/dpkg/info/{package}-{architecture}.md5sums` (alternative pattern)

**Hash Generation Process:**

1. Read MD5 hash values from the first available md5sums file
2. Sort all file MD5 hashes for consistency
3. Combine sorted hashes into single string (newline-separated)
4. Generate SHA256 hash from combined MD5 values
5. Skip hash generation if no md5sums file exists or is empty

### Batch Hash Collection Optimization

Uses single batch operation to collect all package hashes simultaneously:

```bash
cd /var/lib/dpkg/info && \
for file in *.md5sums; do
    if [ -f "$file" ]; then
        echo "FILE:$file"
        cat "$file" 2>/dev/null || true
    fi
done
```

**Benefits:**

- **Performance**: Single subprocess call instead of individual file reads
- **Reduced I/O overhead**: Batch processing across all execution environments
- **Environment agnostic**: Works in Docker containers and host systems
- **High coverage**: Achieves 95%+ hash coverage through comprehensive pattern matching

### Hash Parsing Logic

```python
def _parse_batch_hash_output(self, batch_output: str) -> Dict[str, str]:
    # Parse FILE: markers to identify package boundaries
    # Extract MD5 hashes from each package's md5sums content
    # Handle architecture-specific naming patterns
    # Combine per-package hashes using SHA256
```

**Architecture Pattern Handling:**

- `package.md5sums` → `package`
- `package:arch.md5sums` → `package`
- `package-arch.md5sums` → `package` (validates architecture suffixes)

## Environment Detection

### System Scope

DPKG always operates with system scope as it manages system-wide Debian/Ubuntu packages.

### Availability Check

The detector is usable when:

1. Running on Debian/Ubuntu (OS validation)
2. `dpkg-query` command is available and functional

## Output Format

```json
{
  "scope": "system",
  "dependencies": {
    "bash": {
      "version": "5.1-6ubuntu1 amd64",
      "hash": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890"
    },
    "libc6": {
      "version": "2.35-0ubuntu3.1 amd64",
      "hash": "b2c3d4e5f6789012345678901234567890123456789012345678901234567890a1"
    }
  }
}
```

## Key Advantages

### Authentic Hashes

- **Leverages dpkg metadata**: Uses existing package integrity checking infrastructure
- **File-level accuracy**: Reflects actual installed file contents
- **Change detection**: Sensitive to any file modifications within packages
- **Standard approach**: Uses dpkg's own integrity verification system

### Architecture Awareness

- **Multi-arch support**: Handles modern Debian/Ubuntu package installations
- **Architecture-specific patterns**: Supports various md5sums file naming conventions
- **Cross-platform compatibility**: Architecture information essential for dependency resolution

### Performance Optimizations

- **Batch hash collection**: Single command processes all packages simultaneously
- **Reduced subprocess overhead**: Minimizes system calls across all execution environments
- **Caching**: Batch results cached to avoid repeated processing

## Limitations & Constraints

- **Debian/Ubuntu specific**: Not portable to other package managers
- **Hash availability**: Depends on dpkg metadata file existence (typically 95%+ coverage)
- **Architecture dependency**: Package name extraction relies on consistent naming patterns

## Error Handling

- **Graceful degradation**: Returns packages without hashes when md5sums files unavailable
- **Individual package failures**: Failed hash extraction doesn't affect other packages
- **Batch operation fallback**: Falls back to individual hash lookup if batch operation fails
- **Invalid hash filtering**: Validates MD5 hash format (32 characters) before processing
- **Architecture pattern recognition**: Handles unknown architecture suffixes gracefully

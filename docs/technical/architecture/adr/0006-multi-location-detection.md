# ADR-0006: Multi-Location Detection for Package Managers

## Status

Accepted

## Context

Package managers can have dependencies installed in multiple locations simultaneously. For example, pip can have packages installed in both a virtual environment and the system Python installation. The original detector architecture assumed each detector would return dependencies from a single location, missing packages in other locations.

**Problem**: The pip detector prioritized virtual environments over system installations, so when both existed, only virtual environment packages were detected. This prevented comprehensive dependency analysis in mixed environments.

**Alternatives Considered**:

1. **Split into separate detectors**: Create `pip-venv` and `pip-system` detectors
   - ❌ Breaks existing API expectations
   - ❌ Requires orchestrator changes
   - ❌ Confusing output with multiple pip entries

2. **Always merge dependencies**: Combine all packages into single result
   - ❌ Loses location information for each package
   - ❌ Cannot track location-specific hashes
   - ❌ Reduces traceability

3. **Universal nested structure**: Change all detectors to use locations format
   - ❌ Major breaking change
   - ❌ Unnecessary complexity for single-location detectors
   - ❌ Verbose output when most detectors have only one location
   - ❌ Inconsistent with the principle of simple structures for simple cases

4. **Conditional output structure**: Single location uses existing format, multiple locations use nested format
   - ✅ Preserves backward compatibility
   - ✅ Simple structure for simple cases
   - ✅ Maintains location-specific metadata
   - ✅ Clear semantic distinction
   - ✅ Efficient output format

## Decision

We will implement **conditional output structure** for multi-location detection:

### Single Location (Existing Format)

```json
{
  "pip": {
    "scope": "project",
    "location": "/path/to/venv",
    "hash": "abc123...",
    "dependencies": {...}
  }
}
```

### Multiple Locations (New Format)

```json
{
  "pip": {
    "scope": "mixed",
    "locations": {
      "/path/to/venv": {
        "scope": "project",
        "hash": "abc123...",
        "dependencies": {...}
      },
      "/usr/lib/python3/dist-packages": {
        "scope": "system",
        "hash": "def456...",
        "dependencies": {...}
      }
    }
  }
}
```

### Implementation Approach

1. **Detector Interface**: No changes to `PackageManagerDetector` interface
2. **Conditional Logic**: Detectors return nested structure only when multiple locations exist
3. **Orchestrator Support**: Enhanced to recognize `scope: "mixed"` pattern
4. **Generalized Pattern**: Any detector can implement multi-location detection

## Consequences

### Positive

- ✅ **Backward Compatible**: Existing code continues to work unchanged
- ✅ **Location Transparency**: Each package's source location is preserved
- ✅ **Hash Preservation**: Location-specific hashes maintained
- ✅ **Extensible**: Pattern available for future detectors (npm, maven, etc.)
- ✅ **Self-Documenting**: Output structure indicates single vs. multi-location
- ✅ **Efficient**: Simple structure for simple cases, complex structure only when needed

### Negative

- ❌ **Complexity**: Consumers must handle two different output formats
- ❌ **Testing Overhead**: Additional test scenarios for mixed-scope handling

### Neutral

- **New Scope Value**: Introduces `"mixed"` as third scope option alongside `"system"` and `"project"`

## Implementation Notes

- **pip detector**: First implementation targeting venv + system detection
- **Test Infrastructure**: Updated to handle both output formats generically
- **Documentation**: Updated to explain conditional structure behavior
- **Future Detectors**: npm could implement similar pattern for global vs. local node_modules

This approach solves the multi-location problem while minimizing breaking changes and maintaining clear traceability of package origins.

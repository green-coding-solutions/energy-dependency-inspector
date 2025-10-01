# NPM Detector

## Purpose & Scope

The NPM detector identifies Node.js packages managed by `npm` in both project and system environments. It supports multi-location detection to capture project dependencies and globally installed packages simultaneously.

## Key Features

### Multi-Location Detection

Detects npm packages in multiple locations:

- **Local dependencies**: Project-level packages via `npm list --json --depth=0`
- **Global packages**: System-level packages via `npm list -g --json --depth=0`
- **Mixed output**: Returns both when present in same environment

### Smart Package Manager Detection

For local projects, avoids conflicts with other Node.js package managers:

**Exclusion checks:**

- `yarn.lock` exists → Skip local detection (defer to yarn)
- `pnpm-lock.yaml` exists → Skip local detection (defer to pnpm)
- `bun.lockb` exists → Skip local detection (defer to bun)

**Inclusion checks:**

- `package.json`, `node_modules`, or `package-lock.json` exists
- No conflicting lock files present

## Commands Used

- **Local packages**: `npm list --json --depth=0`
- **Global packages**: `npm list -g --json --depth=0`

## Hash Generation

### Individual Package Hashes

Individual package-level hashes are **not implemented** for npm dependencies. This design decision is based on npm's public registry immutability:

- **Version immutability**: Public npm registry prevents version reuse - each `package@version` maps to exactly one content hash
- **Version-hash correlation**: Version numbers effectively serve as content identifiers for public packages
- **Implementation cost**: Parsing package-lock.json adds complexity without significant benefit
- **Location-based fallback**: Directory-level hashing still detects environment changes

### Directory Content Hashing

Generates location-based hashes for both project and system locations while excluding:

- npm cache directories (`node_modules/.cache`)
- Log files (`*.log`)
- npm configuration (`.npm`)
- Temporary files (`*.tmp`, `*.temp`)

## Output Format

**Single Location** (project or system):

```json
{
  "scope": "project" | "system",
  "location": "/path/to/location",
  "hash": "abc123...",
  "dependencies": {...}
}
```

**Mixed Locations** (both project and global):

```json
{
  "scope": "mixed",
  "locations": {
    "/path/to/project": {
      "scope": "project",
      "hash": "abc123...",
      "dependencies": {...}
    },
    "/usr/lib/node_modules": {
      "scope": "system",
      "hash": "def456...",
      "dependencies": {...}
    }
  }
}
```

## Benefits

- **Complete visibility**: Captures both project and global npm packages
- **Conflict avoidance**: Prevents npm from running in yarn/pnpm/bun projects
- **Multi-location support**: Follows pip_detector pattern for consistency
- **Structured data**: JSON output provides reliable programmatic parsing
- **Direct dependencies focus**: Captures only direct dependencies (depth=0)

## Limitations

- **Direct dependencies only**: Excludes transitive dependencies
- **npm dependency**: Requires npm to be installed and functional
- **Global detection**: Only detects packages via `npm list -g` (not manual installations)

## Use Cases

- Node.js project dependency analysis in containers with global tools
- Package manager conflict avoidance in multi-tool environments
- Direct dependency tracking across project and system scopes
- Build reproducibility through location hashing

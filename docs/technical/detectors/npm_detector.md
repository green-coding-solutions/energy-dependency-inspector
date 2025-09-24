# NPM Detector

## Purpose & Scope

The NPM detector identifies Node.js packages managed by `npm` in project environments. It provides structured package information with intelligent package manager detection to avoid conflicts with other Node.js package managers (yarn, pnpm, bun).

## Key Features

### Smart Package Manager Detection

The detector avoids conflicts with other Node.js package managers by checking for lock files:

**Exclusion checks:**

- `yarn.lock` exists → Skip (defer to yarn)
- `pnpm-lock.yaml` exists → Skip (defer to pnpm)
- `bun.lockb` exists → Skip (defer to bun)

**Inclusion checks:**

- `package.json` or `package-lock.json` exists
- No conflicting lock files present

### Project Context Detection

Determines scope based on project indicators:

- **Project scope**: When `package.json` or `node_modules` exists
- **System scope**: When no project indicators found

## Command Used

- **Package listing**: `npm list --json --depth=0` for structured JSON output of direct dependencies only

## Hash Generation

### Individual Package Hashes

Individual package-level hashes are **not implemented** for npm dependencies. This design decision is based on npm's public registry immutability:

- **Version immutability**: Public npm registry prevents version reuse - each `package@version` maps to exactly one content hash
- **Version-hash correlation**: Version numbers effectively serve as content identifiers for public packages
- **Implementation cost**: Parsing package-lock.json adds complexity without significant benefit
- **Location-based fallback**: Directory-level hashing still detects environment changes

### Directory Content Hashing

For project-scoped dependencies, generates location-based hashes by scanning the project directory while excluding:

- npm cache directories (`node_modules/.cache`)
- Log files (`*.log`)
- npm configuration (`.npm`)
- Temporary files (`*.tmp`, `*.temp`)

## Output Format

**Project Scope** (with location hash):

- Includes `scope: "project"`, project location, and content hash
- Contains only direct dependencies from the project

**System Scope** (no location/hash):

- Includes `scope: "system"`
- Contains system-wide npm packages

## Benefits

- **Conflict avoidance**: Prevents npm from running in yarn/pnpm/bun projects
- **Project isolation**: Distinguishes project dependencies from system packages
- **Structured data**: JSON output provides reliable programmatic parsing
- **Direct dependencies focus**: Captures only project's direct dependencies

## Limitations

- **npm-specific**: Limited to npm package manager only
- **Direct dependencies only**: Excludes transitive dependencies
- **npm dependency**: Requires npm to be installed and functional

## Use Cases

- Node.js project dependency analysis
- Package manager conflict avoidance in multi-tool environments
- Direct dependency tracking and version monitoring
- Build reproducibility through location hashing

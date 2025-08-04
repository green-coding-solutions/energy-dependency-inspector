# ADR-0011: Use npm list --json --depth=0 for Node.js Package Detection

## Status

Accepted

## Context

The dependency resolver needs to extract Node.js package information. Several npm command options were considered:

- `npm list`: Default human-readable tree format
- `npm list --json`: JSON format with structured metadata
- `npm list --json --depth=0`: JSON format limited to direct dependencies
- `npm list --parseable`: Simple flat list format
- `npm ls`: Alias for npm list with same options

## Decision

We will use `npm list --json --depth=0` to retrieve Node.js package dependencies, with intelligent detection to avoid conflicts with other Node.js package managers.

## Rationale

The JSON format with depth limitation provides the most suitable output for dependency tracking in our use case, offering structured data that is both machine-readable and focused on direct dependencies.

Key advantages:

- **Structured format**: JSON output enables reliable programmatic parsing
- **Direct dependencies only**: `--depth=0` limits output to project's direct dependencies, avoiding deep dependency trees
- **Machine readable**: Native JSON parsing eliminates custom string manipulation
- **Consistent output**: Stable JSON structure across different npm versions
- **Version precision**: Includes exact installed versions from node_modules
- **Error handling**: JSON structure allows graceful handling of missing or malformed data
- **Location awareness**: Can detect project context through package.json presence
- **Package manager detection**: Intelligently detects npm vs yarn/pnpm/bun usage through lock file analysis

## Alternatives Considered

- **npm list --parseable**: Simpler output but requires custom parsing and less metadata
- **npm list (default)**: Human-readable but inconsistent formatting across versions
- **package.json parsing**: Would miss actually installed versions vs declared ranges
- **node_modules directory scanning**: Complex and unreliable across different npm versions

## Consequences

- **Positive**: Reliable, structured parsing of Node.js package information
- **Positive**: Focus on direct dependencies reduces noise and complexity
- **Positive**: JSON format provides extensibility for future metadata needs
- **Positive**: Native error handling through JSON structure validation
- **Positive**: Avoids conflicts with yarn/pnpm/bun through intelligent lock file detection
- **Negative**: Requires JSON parsing with potential for decode errors
- **Negative**: Limited to npm package manager (yarn/pnpm/bun would need separate detectors)
- **Negative**: Dependency on npm being installed and functional in target environment
- **Negative**: Lock file detection may not cover all edge cases or future package managers

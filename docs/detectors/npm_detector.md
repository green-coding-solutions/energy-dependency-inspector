# NPM Detector

## Purpose & Scope

The NPM detector identifies Node.js packages managed by `npm` in project environments. It provides structured package information with intelligent package manager detection to avoid conflicts with other Node.js package managers (yarn, pnpm, bun).

## Implementation Approach

### Package Manager Detection

Uses `npm list --json --depth=0` for structured dependency information:

- **Structured format**: JSON output enables reliable programmatic parsing
- **Direct dependencies only**: `--depth=0` limits output to project's direct dependencies
- **Machine readable**: Native JSON parsing eliminates custom string manipulation
- **Consistent output**: Stable JSON structure across different npm versions
- **Version precision**: Includes exact installed versions from node_modules

### Alternatives Considered

Several npm command options were evaluated:

- **`npm list --json --depth=0`**: Chosen for structured data and direct dependencies focus
- **`npm list`**: Default human-readable tree format but inconsistent formatting
- **`npm list --parseable`**: Simple flat list format but requires custom parsing
- **`npm ls`**: Alias for npm list with same options
- **Package.json parsing**: Would miss actually installed versions vs declared ranges
- **Node_modules scanning**: Complex and unreliable across npm versions

**Decision rationale**: JSON format with depth limitation provides structured, machine-readable data focused on direct dependencies with reliable programmatic parsing.

### Intelligent Package Manager Selection

Prevents conflicts with other Node.js package managers through lock file detection:

**Exclusion checks (in order):**

1. `yarn.lock` exists → Skip (defer to yarn)
2. `pnpm-lock.yaml` exists → Skip (defer to pnpm)
3. `bun.lockb` exists → Skip (defer to bun)

**Inclusion checks:**

- `package.json` exists OR `package-lock.json` exists
- No conflicting lock files present

### Project Context Detection

Determines project vs system scope based on:

- Presence of `package.json` in working directory
- Presence of `node_modules` directory
- Fallback to system scope when no project indicators found

## Command Used

```bash
npm list --json --depth=0
```

**Output format example:**

```json
{
  "name": "my-app",
  "version": "1.0.0",
  "dependencies": {
    "express": {
      "version": "4.18.2"
    },
    "lodash": {
      "version": "4.17.21"
    }
  }
}
```

## Package Information Parsing

The detector processes JSON output:

1. Parse JSON response from npm command
2. Extract `dependencies` object
3. For each dependency, collect:
   - **Package name**: Object key
   - **Version**: `version` field from package info

```python
npm_data = json.loads(stdout)
npm_dependencies = npm_data.get("dependencies", {})

for package_name, package_info in npm_dependencies.items():
    version = package_info.get("version", "unknown")
    dependencies[package_name] = {"version": version}
```

## Hash Generation

### Location-Based Hashing

Implements package manager location hashing for project-scoped dependencies:

**Hash generation strategy:**

- **Individual Package Hashes**: Not implemented (follows multi-tiered strategy)
- **Location Hashes**: Generated for project scope using directory contents
- **System Scope**: No location hash (system-wide installations)

### Directory Content Hashing

```bash
cd '{location}' && find . \
  -name 'node_modules/.cache' -prune -o \
  -name '*.log' -prune -o \
  -name '.npm' -prune -o \
  -not -name '*.tmp' \
  -not -name '*.temp' \
  \( -type f -o -type l \) -printf '%s %p %l\n' | LC_COLLATE=C sort -n -k1,1 -k2,2
```

**Exclusions:**

- `node_modules/.cache` - npm cache directories
- `*.log` - Log files that change frequently
- `.npm` - npm configuration/cache
- `*.tmp`, `*.temp` - Temporary files

**Sort strategy:**

- Primary: File size (numeric)
- Secondary: Path (lexicographic with LC_COLLATE=C for consistency)
- Includes symbolic links with target paths for complete state capture

## Environment Detection

### Scope Determination

- **Project scope**: When `package.json` or `node_modules` exists in working directory
- **System scope**: When no project indicators found

### Location Resolution

```python
def _get_npm_location(self, executor: EnvironmentExecutor, working_dir: str = None) -> str:
    search_dir = working_dir or "."

    if executor.path_exists(f"{search_dir}/package.json"):
        return self._resolve_absolute_path(executor, search_dir)

    if executor.path_exists(f"{search_dir}/node_modules"):
        return self._resolve_absolute_path(executor, search_dir)

    return "system"
```

## Output Format

### Project Scope (with location hash)

```json
{
  "scope": "project",
  "location": "/path/to/project",
  "hash": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890",
  "dependencies": {
    "express": {
      "version": "4.18.2"
    },
    "lodash": {
      "version": "4.17.21"
    }
  }
}
```

### System Scope (no location/hash)

```json
{
  "scope": "system",
  "dependencies": {
    "npm": {
      "version": "9.6.4"
    }
  }
}
```

## Package Manager Conflict Avoidance

### Lock File Detection Logic

```python
def is_usable(self, executor: EnvironmentExecutor, working_dir: str = None) -> bool:
    # Check npm availability
    if not npm_available():
        return False

    search_dir = working_dir or "."

    # Exclude if other package managers detected
    if executor.path_exists(f"{search_dir}/yarn.lock"):
        return False
    if executor.path_exists(f"{search_dir}/pnpm-lock.yaml"):
        return False
    if executor.path_exists(f"{search_dir}/bun.lockb"):
        return False

    # Include if npm indicators present
    return (executor.path_exists(f"{search_dir}/package.json") or
            executor.path_exists(f"{search_dir}/package-lock.json"))
```

**Benefits:**

- **Avoids conflicts**: Prevents npm from running in yarn/pnpm/bun projects
- **Respects project choice**: Defers to the project's chosen package manager
- **Future-proof**: Extensible to additional Node.js package managers

## Limitations & Constraints

- **JSON parsing dependency**: Requires valid JSON output from npm command
- **npm-specific**: Limited to npm package manager (yarn/pnpm/bun need separate detectors)
- **Lock file detection**: May not cover all edge cases or future package managers
- **Direct dependencies only**: `--depth=0` excludes transitive dependencies
- **Environment dependency**: Requires npm to be installed and functional

## Error Handling

- **JSON decode errors**: Gracefully handles malformed npm output
- **Command failures**: Returns empty dependencies when npm command fails
- **Path resolution errors**: Raises clear error messages for path resolution failures
- **Hash generation failures**: Returns empty hash on directory listing failures (with debug output)
- **Missing attributes**: Handles missing version information with "unknown" fallback

## Use Cases

- **Node.js project analysis**: Track direct dependencies in npm-managed projects
- **Version monitoring**: Detect changes in installed package versions
- **Environment comparison**: Compare dependencies across different environments
- **Build reproducibility**: Ensure consistent dependency versions through location hashing

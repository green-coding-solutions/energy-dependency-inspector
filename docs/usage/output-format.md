# Output Format Guide

This guide explains the JSON output structure produced by the dependency-resolver.

## JSON Structure Overview

The dependency-resolver outputs a JSON object where each key represents a detector (package manager) and contains information about detected dependencies:

```json
{
  "source": { ... },
  "dpkg": { ... },
  "pip": { ... },
  "npm": { ... }
}
```

## Source Information

When analyzing environments, the `source` section provides metadata about where the scan was performed:

```json
{
  "source": {
    "type": "container",
    "name": "nginx-container",
    "image": "nginx:latest",
    "hash": "sha256:2cd1d97f893f..."
  }
}
```

### Fields

- `type` - Source type (`"container"` for Docker containers, `"host"` for host scans)
- `name` - Container name (for container sources)
- `image` - Docker image used (for container sources)
- `hash` - Container image hash (for container sources)

## Package Manager Sections

Each package manager detector produces a section with this structure:

### System-Scoped Packages

System-wide package managers (dpkg, apk) output:

```json
{
  "dpkg": {
    "scope": "system",
    "dependencies": {
      "package-name": {
        "version": "1.2.3 amd64",
        "hash": "abc123..."
      },
      "another-package": {
        "version": "2.0.0 amd64",
        "hash": "def456..."
      }
    }
  }
}
```

### Project-Scoped Packages

Project-specific package managers (pip, npm) output:

```json
{
  "pip": {
    "scope": "project",
    "location": "/path/to/venv/lib/python3.12/site-packages",
    "hash": "def456...",
    "dependencies": {
      "package-name": {
        "version": "1.2.3"
      },
      "another-package": {
        "version": "2.0.0"
      }
    }
  }
}
```

## Field Definitions

### Common Fields

- **scope** - Either `"system"` or `"project"`
  - `system`: System-wide packages affecting the entire environment
  - `project`: Project-specific packages in a local scope

- **dependencies** - Object containing all detected packages
  - Keys: Package names
  - Values: Objects with version and optional hash information

### Project-Scoped Fields

- **location** - Absolute path where project dependencies are installed
- **hash** - Hash of the dependency location/environment

### Package Fields

- **version** - Package version string (format varies by package manager)
- **hash** - Package-specific hash (when available)

## Hash Strategy

The dependency-resolver implements a tiered hash strategy:

### Tier 1: Authentic Hashes

Package managers that provide authentic hashes use them directly:

```json
{
  "package-name": {
    "version": "1.2.3",
    "hash": "sha256:authentic-hash-from-package-manager"
  }
}
```

### Tier 2: Location-Based Hashes

For project-scoped package managers, a location hash is provided:

```json
{
  "pip": {
    "scope": "project",
    "location": "/path/to/venv/lib/python3.12/site-packages",
    "hash": "sha256:location-based-hash",
    "dependencies": { ... }
  }
}
```

### Tier 3: No Hashes

Some package managers don't provide hash information:

```json
{
  "package-name": {
    "version": "1.2.3"
  }
}
```

## Complete Example

Here's a complete example showing multiple package managers:

```json
{
  "source": {
    "type": "container",
    "name": "web-app",
    "image": "python:3.12-slim",
    "hash": "sha256:a1b2c3d4e5f6..."
  },
  "dpkg": {
    "scope": "system",
    "dependencies": {
      "libc6": {
        "version": "2.36-9+deb12u4 amd64",
        "hash": "abc123..."
      },
      "python3": {
        "version": "3.11.2-1+b1 amd64",
        "hash": "def456..."
      }
    }
  },
  "pip": {
    "scope": "project",
    "location": "/app/venv/lib/python3.12/site-packages",
    "hash": "sha256:xyz789...",
    "dependencies": {
      "flask": {
        "version": "2.3.3"
      },
      "requests": {
        "version": "2.31.0"
      }
    }
  },
  "npm": {
    "scope": "project",
    "location": "/app/node_modules",
    "hash": "sha256:npm456...",
    "dependencies": {
      "express": {
        "version": "4.18.2"
      },
      "lodash": {
        "version": "4.17.21"
      }
    }
  }
}
```

## Processing the Output

### Python Processing Example

```python
import json
import dependency_resolver

# Get dependencies as dictionary
deps = dependency_resolver.resolve_dependencies_as_dict("host")

# Process each detector
for detector_name, result in deps.items():
    if detector_name.startswith("_"):
        continue  # Skip metadata sections

    print(f"\n{detector_name.upper()} ({result['scope']} scope):")

    if "location" in result:
        print(f"  Location: {result['location']}")

    dependencies = result.get("dependencies", {})
    print(f"  Packages: {len(dependencies)}")

    for package, info in dependencies.items():
        version = info.get("version", "unknown")
        has_hash = "hash" in info
        print(f"    {package}: {version} {'✓' if has_hash else ''}")
```

### Filtering Examples

```python
# Get only system packages
system_packages = {k: v for k, v in deps.items()
                  if not k.startswith("_") and v.get("scope") == "system"}

# Get only project packages
project_packages = {k: v for k, v in deps.items()
                   if not k.startswith("_") and v.get("scope") == "project"}

# Count total packages
total = sum(len(v.get("dependencies", {})) for v in deps.values()
           if not k.startswith("_"))
```

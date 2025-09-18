# Output Format Guide

This guide explains the JSON output structure produced by the dependency-resolver.

## JSON Structure Overview

The dependency-resolver outputs a unified JSON structure that aggregates all packages by scope:

```json
{
  "source": { ... },
  "project": {
    "packages": [...],
    "package-management": {
      "pip": { ... },
      "npm": { ... }
    }
  },
  "system": {
    "packages": [...]
  }
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

## Package Sections

### Project Packages

Project-specific packages from all package managers are aggregated in a single array:

```json
{
  "project": {
    "packages": [
      {
        "name": "flask",
        "version": "2.3.3",
        "type": "pip"
      },
      {
        "name": "express",
        "version": "4.18.2",
        "type": "npm"
      }
    ],
    "package-management": {
      "pip": {
        "location": "/path/to/venv/lib/python3.12/site-packages",
        "hash": "def456..."
      },
      "npm": {
        "location": "/app/node_modules",
        "hash": "abc123..."
      }
    }
  }
}
```

### System Packages

System-wide packages are aggregated in a single array:

```json
{
  "system": {
    "packages": [
      {
        "name": "libc6",
        "version": "2.36-9+deb12u4 amd64",
        "hash": "abc123...",
        "type": "dpkg"
      },
      {
        "name": "bash",
        "version": "5.2.15-r5 x86_64",
        "type": "apk"
      }
    ]
  }
}
```

## Field Definitions

### Package Fields

Each package in the `packages` arrays contains:

- **name** - Package name
- **version** - Package version string (format varies by package manager)
- **type** - Package manager type (`"pip"`, `"npm"`, `"dpkg"`, `"apk"`, `"maven"`)
- **hash** - Package-specific hash (when available, primarily for system packages)

### Project Metadata Fields

Project-scoped package managers provide metadata sections:

- **location** - Absolute path where dependencies are installed
- **hash** - Hash of the dependency location/environment for change detection

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

For project-scoped package managers, a location hash is provided in the metadata:

```json
{
  "project": {
    "packages": [...],
    "package-management": {
      "pip": {
        "location": "/path/to/venv/lib/python3.12/site-packages",
        "hash": "sha256:location-based-hash"
      }
    }
  }
}
```

### Tier 3: No Hashes

Some package managers don't provide hash information:

```json
{
  "name": "package-name",
  "version": "1.2.3",
  "type": "npm"
}
```

## Complete Example

Here's a complete example showing the new unified structure:

```json
{
  "source": {
    "type": "container",
    "name": "web-app",
    "image": "python:3.12-slim",
    "hash": "sha256:a1b2c3d4e5f6..."
  },
  "project": {
    "packages": [
      {
        "name": "flask",
        "version": "2.3.3",
        "type": "pip"
      },
      {
        "name": "requests",
        "version": "2.31.0",
        "type": "pip"
      },
      {
        "name": "express",
        "version": "4.18.2",
        "type": "npm"
      },
      {
        "name": "lodash",
        "version": "4.17.21",
        "type": "npm"
      }
    ],
    "package-management": {
      "pip": {
        "location": "/app/venv/lib/python3.12/site-packages",
        "hash": "sha256:xyz789..."
      },
      "npm": {
        "location": "/app/node_modules",
        "hash": "sha256:npm456..."
      }
    }
  },
  "system": {
    "packages": [
      {
        "name": "libc6",
        "version": "2.36-9+deb12u4 amd64",
        "hash": "abc123...",
        "type": "dpkg"
      },
      {
        "name": "python3",
        "version": "3.11.2-1+b1 amd64",
        "hash": "def456...",
        "type": "dpkg"
      }
    ]
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

# Process project packages
if "project" in deps:
    project = deps["project"]
    packages = project.get("packages", [])
    print(f"\nPROJECT PACKAGES: {len(packages)}")

    for pkg in packages:
        name = pkg.get("name", "unknown")
        version = pkg.get("version", "unknown")
        pkg_type = pkg.get("type", "unknown")
        has_hash = "hash" in pkg
        print(f"  {name}: {version} ({pkg_type}) {'✓' if has_hash else ''}")

    # Show metadata for each package manager
    package_management = project.get("package-management", {})
    for key, value in package_management.items():
        if isinstance(value, dict):
            location = value.get("location", "N/A")
            has_hash = "hash" in value
            print(f"  {key.upper()} location: {location} {'✓' if has_hash else ''}")

# Process system packages
if "system" in deps:
    packages = deps["system"].get("packages", [])
    print(f"\nSYSTEM PACKAGES: {len(packages)}")

    for pkg in packages:
        name = pkg.get("name", "unknown")
        version = pkg.get("version", "unknown")
        pkg_type = pkg.get("type", "unknown")
        has_hash = "hash" in pkg
        print(f"  {name}: {version} ({pkg_type}) {'✓' if has_hash else ''}")
```

### Filtering Examples

```python
# Get only system packages
system_packages = deps.get("system", {}).get("packages", [])

# Get only project packages
project_packages = deps.get("project", {}).get("packages", [])

# Get packages by type
pip_packages = [pkg for pkg in project_packages if pkg.get("type") == "pip"]
npm_packages = [pkg for pkg in project_packages if pkg.get("type") == "npm"]

# Count total packages
total_project = len(project_packages)
total_system = len(system_packages)
total = total_project + total_system

# Get all packages with hashes
packages_with_hashes = [
    pkg for pkg in (project_packages + system_packages)
    if "hash" in pkg
]
```

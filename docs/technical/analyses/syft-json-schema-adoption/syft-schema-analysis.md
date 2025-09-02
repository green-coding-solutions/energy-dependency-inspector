# Syft JSON Schema Analysis - Minimal Required Structure

## Overview

This analysis identifies the minimal required fields for a valid Syft JSON output according to schema version 16.0.39. The goal is to understand what the absolute minimum valid Syft JSON structure looks like for dependency resolution output.

## Schema Analysis Results

### Document (Root Object) Required Fields

The root `Document` object requires these fields:

- `artifacts` (array of Package objects)
- `artifactRelationships` (array of Relationship objects)
- `source` (Source object)
- `distro` (LinuxRelease object)
- `descriptor` (Descriptor object)
- `schema` (Schema object)

### Package Object Required Fields

Each `Package` in the `artifacts` array requires:

- `id` (string) - Unique identifier for the package
- `name` (string) - Package name
- `version` (string) - Package version
- `type` (string) - Package type (e.g., "deb", "rpm", "npm")
- `foundBy` (string) - Which cataloger found this package
- `locations` (array of Location objects) - Where the package was found
- `licenses` (array of License objects) - Package licenses
- `language` (string) - Programming language (can be empty)
- `cpes` (array of CPE objects) - Common Platform Enumeration identifiers
- `purl` (string) - Package URL identifier

### Supporting Object Required Fields

**Relationship Object:**

- `parent` (string) - Parent package ID
- `child` (string) - Child package ID
- `type` (string) - Relationship type (e.g., "dependency-of")

**Source Object:**

- `id` (string) - Source identifier
- `name` (string) - Source name
- `version` (string) - Source version
- `type` (string) - Source type (e.g., "image", "directory")
- `metadata` (object) - Source metadata (can be empty object)

**Descriptor Object:**

- `name` (string) - Tool name (e.g., "syft")
- `version` (string) - Tool version

**Schema Object:**

- `version` (string) - Schema version
- `url` (string) - Schema URL

**Location Object:**

- `path` (string) - File path where package was found
- `accessPath` (string) - Access path to the file

**License Object:**

- `value` (string) - License name/identifier
- `spdxExpression` (string) - SPDX license expression
- `type` (string) - License type (e.g., "declared", "concluded")
- `urls` (array of strings) - License URLs (can be empty)
- `locations` (array of Location objects) - Where license was found

**CPE Object:**

- `cpe` (string) - CPE identifier string

**LinuxRelease Object:**

- No required fields (can be empty object)

## Minimal Valid Examples

### Basic Minimal Example

```json
{
  "artifacts": [
    {
      "id": "pkg1",
      "name": "example-package",
      "version": "1.0.0",
      "type": "deb",
      "foundBy": "dpkg-db-cataloger",
      "locations": [
        {
          "path": "/var/lib/dpkg/status",
          "accessPath": "/var/lib/dpkg/status"
        }
      ],
      "licenses": [
        {
          "value": "MIT",
          "spdxExpression": "MIT",
          "type": "declared",
          "urls": [],
          "locations": [
            {
              "path": "/usr/share/doc/example-package/copyright",
              "accessPath": "/usr/share/doc/example-package/copyright"
            }
          ]
        }
      ],
      "language": "",
      "cpes": [
        {
          "cpe": "cpe:2.3:a:example:example-package:1.0.0:*:*:*:*:*:*:*"
        }
      ],
      "purl": "pkg:deb/debian/example-package@1.0.0"
    }
  ],
  "artifactRelationships": [],
  "source": {
    "id": "source1",
    "name": "example-container",
    "version": "latest",
    "type": "image",
    "metadata": {}
  },
  "distro": {},
  "descriptor": {
    "name": "syft",
    "version": "v0.100.0"
  },
  "schema": {
    "version": "16.0.39",
    "url": "https://raw.githubusercontent.com/anchore/syft/main/schema/json/schema-16.0.39.json"
  }
}
```

### Example with Relationships

```json
{
  "artifacts": [
    {
      "id": "pkg1",
      "name": "openssl",
      "version": "3.0.0",
      "type": "deb",
      "foundBy": "dpkg-db-cataloger",
      "locations": [
        {
          "path": "/var/lib/dpkg/status",
          "accessPath": "/var/lib/dpkg/status"
        }
      ],
      "licenses": [
        {
          "value": "Apache-2.0",
          "spdxExpression": "Apache-2.0",
          "type": "declared",
          "urls": [],
          "locations": [
            {
              "path": "/usr/share/doc/openssl/copyright",
              "accessPath": "/usr/share/doc/openssl/copyright"
            }
          ]
        }
      ],
      "language": "",
      "cpes": [
        {
          "cpe": "cpe:2.3:a:openssl:openssl:3.0.0:*:*:*:*:*:*:*"
        }
      ],
      "purl": "pkg:deb/debian/openssl@3.0.0"
    },
    {
      "id": "pkg2",
      "name": "libssl3",
      "version": "3.0.0",
      "type": "deb",
      "foundBy": "dpkg-db-cataloger",
      "locations": [
        {
          "path": "/var/lib/dpkg/status",
          "accessPath": "/var/lib/dpkg/status"
        }
      ],
      "licenses": [
        {
          "value": "Apache-2.0",
          "spdxExpression": "Apache-2.0",
          "type": "declared",
          "urls": [],
          "locations": [
            {
              "path": "/usr/share/doc/libssl3/copyright",
              "accessPath": "/usr/share/doc/libssl3/copyright"
            }
          ]
        }
      ],
      "language": "",
      "cpes": [
        {
          "cpe": "cpe:2.3:a:openssl:libssl:3.0.0:*:*:*:*:*:*:*"
        }
      ],
      "purl": "pkg:deb/debian/libssl3@3.0.0"
    }
  ],
  "artifactRelationships": [
    {
      "parent": "pkg1",
      "child": "pkg2",
      "type": "dependency-of"
    }
  ],
  "source": {
    "id": "debian-container",
    "name": "debian",
    "version": "12",
    "type": "image",
    "metadata": {
      "digest": "sha256:abc123",
      "mediaType": "application/vnd.docker.distribution.manifest.v2+json"
    }
  },
  "distro": {
    "name": "Debian GNU/Linux",
    "id": "debian",
    "version": "12",
    "versionID": "12"
  },
  "descriptor": {
    "name": "syft",
    "version": "v0.100.0"
  },
  "schema": {
    "version": "16.0.39",
    "url": "https://raw.githubusercontent.com/anchore/syft/main/schema/json/schema-16.0.39.json"
  }
}
```

## Key Insights for Dependency Resolvers

1. **Minimum Structure**: Even the simplest valid Syft output requires substantial structure including packages, source info, descriptor, and schema reference.

2. **Package Identification**: Every package needs multiple identifiers (id, name, version, purl, cpes) for proper identification and vulnerability matching.

3. **Location Tracking**: Packages must specify where they were found (`locations`) for audit and debugging purposes.

4. **License Information**: License data is required and must include SPDX expressions and location references.

5. **Relationships**: While `artifactRelationships` can be an empty array for simple cases, it's useful for showing dependency relationships between packages.

6. **Cataloger Attribution**: The `foundBy` field identifies which detection method found each package, important for understanding data provenance.

## Files Generated

- `minimal_syft_sample.json` - Basic minimal example
- `minimal_syft_with_relationships.json` - Example with package relationships

Both files have been validated against the Syft schema and are confirmed valid.

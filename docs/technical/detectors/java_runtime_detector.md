# Java Runtime Detector

## Overview

The Java Runtime Detector identifies Java applications in production environments by detecting JAR files and Java runtime information. It complements the Maven detector by targeting environments where JAR files exist but Maven build tools are unavailable (e.g., production containers).

## Type and Scope

- **Type**: `runtime` - Detects runtime artifacts rather than installed dependencies
- **Target Environments**: Production containers, runtime environments with JAR files
- **Working Directory**: Scans the specified working directory and subdirectories for JAR files
- **Complementary**: Works alongside Maven detector (Maven handles build-time dependencies, Java Runtime handles runtime artifacts)

## Detection Logic

### Usability Check (`is_usable`)

The detector considers an environment usable if either condition is met:

1. **JAR Files Present**: Any `.jar` files found in working directory or subdirectories
2. **Java Runtime Available**: `java -version` command executes successfully

### Runtime Artifact Extraction (`get_dependencies`)

1. **JAR Discovery**: Uses `find` to locate all `.jar` files recursively
2. **Artifact Metadata Extraction**: For each JAR file:
   - File size via `stat` command (converted to integer)
   - Version from JAR manifest (META-INF/MANIFEST.MF)
   - Fallback version extraction from filename patterns
   - Full path location of the artifact
3. **Runtime Environment Info**: Collects Java runtime information via `java -version`
4. **Location Hash**: Generates Tier 2 hash based on JAR file list and sizes

### Version Extraction Strategy

**Priority Order**:

1. **JAR Manifest**: Looks for version attributes in META-INF/MANIFEST.MF:
   - Implementation-Version
   - Bundle-Version
   - Version
   - Specification-Version
2. **Filename Patterns**: Extracts version from filename using regex patterns:
   - `name-1.2.3.jar`
   - `name_1.2.3.jar`
   - `name-v1.2.3.jar`
3. **Fallback**: Sets version as "unknown" if no version found

## Hash Strategy

**Tier 2 - Location-based**: Generates SHA256 hash from:

- List of all JAR files in working directory
- File sizes for each JAR
- Sorted consistently using `LC_COLLATE=C sort`

This provides change detection when JARs are added, removed, or modified.

## Limitations

1. **No Transitive Dependencies**: Cannot resolve dependencies between JARs
2. **Runtime-Only**: Provides JAR inventory, not complete dependency tree
3. **Limited Version Detection**: Depends on manifest quality and filename conventions
4. **No Build-Time Info**: Cannot access original build dependencies or configurations

## Example Output

```json
{
  "type": "runtime",
  "location": "/app",
  "runtime_environment": {
    "platform": "java",
    "version": "17.0.8",
    "vendor": "Eclipse Adoptium",
    "runtime": "OpenJDK Runtime Environment"
  },
  "artifacts": {
    "my-application.jar": {
      "version": "1.2.3",
      "size": 15728640,
      "type": "jar",
      "path": "/app/my-application.jar"
    },
    "lib/commons-lang3-3.12.0.jar": {
      "version": "3.12.0",
      "size": 587264,
      "type": "jar",
      "path": "/app/lib/commons-lang3-3.12.0.jar"
    },
    "lib/spring-boot-2.7.0.jar": {
      "version": "2.7.0",
      "size": 1245184,
      "type": "jar",
      "path": "/app/lib/spring-boot-2.7.0.jar"
    },
    "legacy-app.jar": {
      "version": "unknown",
      "size": 2048000,
      "type": "jar",
      "path": "/app/legacy-app.jar"
    }
  },
  "hash": "sha256:abc123def456..."
}
```

## Use Cases

### Production Container Scanning

```bash
# Scan production container with JAR files but no Maven
python3 -m dependency_resolver docker my-prod-container
```

### Runtime Environment Analysis

```bash
# Analyze JAR-based application in working directory
python3 -m dependency_resolver host --working-dir /opt/myapp
```

### Complementary with Maven

- **Development**: Maven detector provides complete build dependencies
- **Production**: Java Runtime detector provides deployed JAR inventory
- **Combined**: Full lifecycle dependency visibility

## Technical Notes

### JAR Manifest Parsing

- Uses `unzip -q -c` to extract manifest without temporary files
- Handles various manifest formats and encoding issues
- Gracefully falls back to filename parsing on manifest read failures

### File Size Calculation

- Uses `stat` command with BSD/GNU compatibility (`-f%z` with `-c%s` fallback)
- Provides byte-accurate size information for change detection

### Java Version Parsing

- Parses `java -version` stderr/stdout output
- Extracts version, runtime name, and vendor information
- Handles various Java distribution output formats

### Performance Considerations

- `find` command limited to working directory scope
- Caches Java availability and version info to avoid repeated calls
- Uses efficient `head -1` for initial JAR detection in usability check

## Error Handling

- **Missing Java**: Gracefully continues with JAR-only detection
- **JAR Read Failures**: Logs debug info, continues with other JARs
- **Command Failures**: Returns empty artifacts instead of exceptions
- **Permission Issues**: Handles restricted file access gracefully

## Integration

The detector integrates seamlessly with the orchestrator priority system:

1. Runs after system package detectors (dpkg, apk)
2. Runs before Maven detector (complements rather than conflicts)
3. Project scope ensures proper working directory handling
4. Debug mode provides detailed extraction logging

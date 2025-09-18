# Maven Detector

## Overview

The Maven detector identifies and extracts dependency information from Maven-based Java projects. Maven is a widely-used build automation and project management tool for Java projects that uses XML configuration files (`pom.xml`) to define project dependencies, build settings, and metadata.

## Scope

- **Type**: Project-scoped detector
- **Target Environment**: Maven projects with `pom.xml` files
- **Priority**: Runs after system package managers (dpkg, apk) but before pip/npm
- **Scope**: Always `project` scope - Maven dependencies are project-specific

## Detection Logic

### Usability Check

The detector considers itself usable when:

1. **Primary condition**: A `pom.xml` file exists in the working directory
2. **No additional requirements**: Maven CLI installation is NOT required for basic functionality

### Dependency Extraction Strategy

The Maven detector uses a hybrid approach with graceful degradation:

#### 1. Maven CLI Method (Preferred)

- **Maven Wrapper Priority**: Checks for `./mvnw` first, then falls back to system `mvn`
- **Commands**:
  - `./mvnw dependency:list -B -q -DoutputFile=/dev/stdout -DexcludeTransitive=true` (when wrapper exists)
  - `mvn dependency:list -B -q -DoutputFile=/dev/stdout -DexcludeTransitive=true` (fallback to system Maven)
- **When available**: If `./mvnw --version` or `mvn --version` succeeds
- **Benefits**: Provides resolved dependency versions and handles complex scenarios
- **Output format**: Parses Maven's dependency list format (`groupId:artifactId:type:version:scope`)
- **Performance**: Uses batch mode (`-B`) for non-interactive execution and caches Maven availability checks

#### 2. POM.xml Parsing (Fallback)

- **Method**: Direct XML parsing of `pom.xml` file
- **When used**: If Maven CLI is not available (common in production containers)
- **Benefits**: Works without Maven installation, respects read-only constraint
- **Features**:
  - Parses `<dependencies>` section
  - Handles Maven namespaces
  - Resolves simple property placeholders (e.g., `${junit.version}`)
  - Excludes test-scoped dependencies
  - Supports `${project.version}` built-in property

#### 3. Scope Filtering

- **Included scopes**: `compile` (default), `runtime`, `provided`
- **Excluded scopes**: `test` (filtered out to avoid development-only dependencies)
- **Scope filtering**: Applied during Maven CLI output parsing to ensure comprehensive runtime snapshot

## Hash Strategy

### Tier 2: Location-based Hash

The detector generates a SHA-256 hash based on Maven project files:

- **Included files**: `pom.xml`, `*.properties` files
- **Excluded paths**: `target/` (build output), `.m2/` (local repository)
- **Method**: Uses `find` with consistent sorting (`LC_COLLATE=C sort -n -k1,1 -k2,2`)
- **Purpose**: Detects changes in project configuration

## Limitations

### POM.xml Parsing Limitations

1. **Property Resolution**: Only resolves simple properties and `${project.version}`
2. **Parent POM**: Does not resolve parent POM inheritance
3. **Profiles**: Does not evaluate Maven profiles or conditional dependencies
4. **Version Ranges**: Does not resolve dynamic version ranges
5. **Dependency Management**: Does not process `<dependencyManagement>` sections

### Maven CLI Limitations

1. **Availability**: May not be available in production/container environments
2. **Performance**: Slower than direct parsing, may require network access for resolution

### General Limitations

1. **Transitive Dependencies**: Only direct dependencies are captured (by design)
2. **Multi-module Projects**: Processes only the specific `pom.xml` in working directory
3. **Complex Builds**: Does not handle complex build scenarios or plugins

## Output Format

The detector returns a tuple: `(packages, metadata)`

### With Maven CLI Available

**Packages:**

```json
[
  {
    "name": "org.apache.commons:commons-lang3",
    "version": "3.12.0",
    "type": "maven"
  },
  {
    "name": "com.fasterxml.jackson.core:jackson-core",
    "version": "2.15.2",
    "type": "maven"
  }
]
```

**Metadata:**

```json
{
  "location": "/path/to/maven/project",
  "hash": "abc123def456789012345678901234567890123456789012345678901234567890"
}
```

### With POM.xml Parsing Only

**Packages:**

```json
[
  {
    "name": "org.apache.commons:commons-lang3",
    "version": "3.12.0",
    "type": "maven"
  },
  {
    "name": "com.fasterxml.jackson.core:jackson-core",
    "version": "2.15.2",
    "type": "maven"
  },
  {
    "name": "org.springframework:spring-core",
    "version": "${spring.version}",
    "type": "maven"
  }
]
```

**Metadata:**

```json
{
  "location": "/path/to/maven/project",
  "hash": "def789abc012345678901234567890123456789012345678901234567890123456"
}
```

## Error Handling

- **Missing pom.xml**: Detector reports as not usable
- **Malformed XML**: Returns empty dependencies, logs debug info
- **Maven command failure**: Falls back to POM.xml parsing
- **Permission issues**: Returns empty dependencies gracefully
- **Hash generation failure**: Returns empty hash string, continues processing

## Testing

The detector is tested using Docker containers:

- **Full Maven environment**: `maven:3.9-eclipse-temurin-17` (tests CLI approach)
- **Java-only environment**: `eclipse-temurin:17-jre` (tests POM parsing approach)

Test scenarios cover:

- Maven CLI dependency resolution (system Maven)
- Maven wrapper dependency resolution (./mvnw)
- Maven wrapper priority over system Maven
- POM.xml parsing without Maven CLI
- Property resolution (`${junit.version}`)
- Scope filtering (excludes test dependencies)
- Project structure and hash generation

## Architecture Integration

- **Read-only compliance**: No installations or system modifications
- **Production-ready**: Works in minimal container environments
- **Graceful degradation**: CLI → POM parsing → empty results
- **Performance**: Fast POM parsing, reasonable CLI performance
- **Debugging**: Comprehensive debug logging when enabled

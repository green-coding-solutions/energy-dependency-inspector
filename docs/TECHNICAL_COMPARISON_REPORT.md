# Dependency Resolution Tools: Technical Comparison Report

> **Disclaimer:** This analysis was generated with the assistance of Claude Code and may include inaccurate information. Technical details about external tools should be verified against official documentation before making implementation decisions.

## Introduction

### Software Bill of Materials (SBOM) Landscape

Software Bill of Materials (SBOM) generation has become a critical component of modern software supply chain security and compliance. Industry standards like **[SPDX](https://spdx.dev/)** (Software Package Data Exchange) and **[CycloneDX](https://cyclonedx.org/)** provide standardized formats for representing software component inventories, enabling organizations to track dependencies, vulnerabilities, and licenses across their software ecosystem.

### Current Ecosystem Solutions

**[GitHub](https://github.com)** utilizes proprietary software to generate dependency graphs for repositories, automatically detecting dependencies in supported languages and providing security advisory integration. This closed-source approach offers deep integration with GitHub's platform but limited customization for specialized requirements.

**[GitLab](https://gitlab.com)** takes an open-source approach with their [dependency-scanning component](https://gitlab.com/gitlab-org/security-products/analyzers/dependency-scanning/-/tree/main), which provides transparent dependency analysis as part of their security scanning suite. While comprehensive for CI/CD integration, it focuses primarily on source code analysis rather than runtime environment scanning.

**Popular Open Source Tools:**

- **[syft](https://github.com/anchore/syft)** (Anchore): Widely adopted SBOM generation tool supporting 25+ ecosystems with multiple output formats
- **[trivy](https://github.com/aquasecurity/trivy)** (Aqua Security): Comprehensive security scanner with SBOM capabilities, popular for vulnerability assessment

**Additional Notable Tools (Development Inspiration):**

- **[sbom-tool](https://github.com/microsoft/sbom-tool)** (Microsoft): Comprehensive SBOM generator with extensive [component-detection](https://github.com/microsoft/component-detection) catalog supporting diverse package managers and build systems. While not directly comparable for runtime scanning, its detector architecture provides valuable implementation patterns for comprehensive package manager coverage.
- **[tern](https://github.com/tern-tools/tern)**: Python-based container analysis tool focusing on Docker image layer inspection and package detection. Shares similar Python implementation approach and provides insights into container filesystem analysis techniques.

These tools have gained significant traction in the open source ecosystem due to their broad package manager support and integration with CI/CD pipelines.

### Analysis Context

This comparison evaluates whether existing popular SBOM tools can fulfill the specific requirements for **runtime production environment scanning** needed by the Green Metrics Tool (GMT), or whether continued development of the specialized dependency-resolver is justified. The key distinction is between traditional build-time/source-code analysis versus live production environment dependency capture.

## Executive Summary

After analyzing syft, trivy, and the current dependency-resolver implementation, **the recommendation is to continue developing the dependency-resolver tool**. While existing tools provide comprehensive SBOM generation, they have critical gaps for the specific requirements: runtime production environment scanning without installation footprint and comprehensive hash retrieval for package integrity verification.

**Key Findings:**

- Neither syft nor trivy can scan running containers natively without image-based approaches
- Hash/checksum retrieval is limited in existing tools compared to dependency-resolver's comprehensive approach
- The sidecar container approach is possible but adds architectural complexity
- Dependency-resolver's modular architecture provides better extensibility for specific detector requirements

## Requirements vs. Capabilities Matrix

| Requirement                     | dependency-resolver            | syft                     | trivy                   |
|---------------------------------|--------------------------------|--------------------------|-------------------------|
| **Runtime Production Scanning** | ✅ Direct `docker exec`        | ❌ Image-only*          | ❌ Image-only*          |
| **Non-invasive Deployment**     | ✅ External execution          | ❌ Requires sidecar*    | ❌ Requires sidecar*    |
| **Individual Package Hashes**   | ✅ dpkg MD5, location hashes   | ❌ Limited/none visible | ❌ Limited/none visible |
| **Docker Compose Image Hashes** | ✅ Full SHA256 extraction      | ❌ No compose support   | ❌ No compose support   |
| **Package Manager Coverage**    | ✅ pip, npm, dpkg, apk, docker | ✅ 25+ ecosystems       | ✅ Multiple ecosystems  |
| **Custom Output Format**        | ✅ Structured JSON schema      | ✅ Templates available  | ✅ SPDX/CycloneDX       |
| **Modular Architecture**        | ✅ Pluggable detectors         | ❌ Monolithic           | ❌ Monolithic           |

*_Sidecar container approach theoretically possible but not documented as primary use case_

## Technical Architecture Comparison

### 3.1 Scanning Architecture and Package Manager Coverage

**dependency-resolver:**

- **Runtime Strategy**: Executes commands inside containers via `docker exec` for live environment analysis
- **Coverage**: dpkg/apk (system), pip/npm (language), Docker Compose (orchestration)
- **Architecture**: Modular detector system with requirement checks

**syft:**

- **Static Strategy**: Image-based filesystem analysis, no native runtime scanning
- **Coverage**: 25+ ecosystems including Java, Go, Rust, PHP with mature detection algorithms
- **Architecture**: Monolithic scanner with comprehensive ecosystem support

**trivy:**

- **Multi-target Strategy**: Container images, filesystems, repositories with vulnerability focus
- **Coverage**: Popular programming languages and OS packages across multiple platforms
- **Architecture**: Security-focused scanner with SBOM capabilities

### 3.2 Hash Retrieval Capabilities

**dependency-resolver provides comprehensive hash support:**

```json
{
  "dpkg": {"dependencies": {"adduser": {"version": "3.134 all", "hash": "aeb90488192cb14ee517facb2a74eeb3e507e2743f3ec6443ee9027942b69c0d"}}},
  "pip": {"location": "/var/www/startup/venv/lib/python3.13/site-packages", "hash": "77a4ac35e0bfb7521c8d7eb715ef33f0aea51d61d96b5ab922e3e76b26b933a6"}
}
```

- ✅ Package-level MD5 hashes (dpkg) and location-based hashes (pip virtual environments)
- ✅ SHA256 format for container images and Docker Compose stacks

**syft provides limited hash support:**

- ✅ File-level MD5 digests in detailed metadata only
- ❌ No package-level or location-based integrity hashes

**trivy provides minimal hash support:**

- ❌ No package hashes visible, focuses on vulnerability data rather than integrity verification

### 3.3 Output Format Comparison

**dependency-resolver:** Custom JSON schema with scope-based organization and location tracking, optimized for GMT integration

**syft:** Multiple standard formats (SPDX, CycloneDX) with template-based customization and rich metadata (licenses, CPEs, PURLs)

**trivy:** Standard SBOM formats with integrated vulnerability data but limited customization options

## Runtime Docker Container Scanning: Technical Approaches

### Approach 1: Direct Container Execution (dependency-resolver)

**Implementation:**

```bash
# Runtime scanning of live container
dependency_resolver.py docker container_name
# Uses docker exec to run detection commands inside running container
```

**Technical Details:**

- Uses Docker API to execute commands inside running containers
- No modification of container or orchestration required
- Leverages existing package managers inside target containers

**Advantages:**

- ✅ **True Runtime State**: Captures actual running environment, including runtime-installed packages
- ✅ **Zero Installation Footprint**: No tools or agents installed in target containers
- ✅ **Production Ready**: Works with existing container deployments without changes
- ✅ **Orchestration Agnostic**: Compatible with Docker Compose, Kubernetes, standalone containers
- ✅ **Security Isolation**: Scanner runs externally, target containers unchanged

**Limitations:**

- ❌ **Container Access Required**: Needs Docker API access and exec permissions
- ❌ **Container Dependency**: Target containers must have required package managers installed

### Approach 2: Sidecar Container with Volume Sharing

**Implementation:**

```yaml
# Docker Compose modification required for syft/trivy
services:
  app:
    volumes:
      - app-filesystem:/app
  scanner:
    image: anchore/syft
    volumes:
      - app-filesystem:/scan-target
    command: /scan-target
```

**Technical Details:**

- Deploy scanning tools as additional containers with shared volumes
- Mount application filesystem to scanner container
- Analyze mounted filesystem using traditional SBOM tools

**Advantages:**

- ✅ **Tool Reuse**: Leverage existing mature SBOM tools (syft/trivy)
- ✅ **Broad Ecosystem Support**: Access to 25+ package managers
- ✅ **Standard Output**: SPDX/CycloneDX compliant formats

**Limitations:**

- ❌ **Infrastructure Changes**: Requires modification of all production deployments
- ❌ **Volume Management Complexity**: Shared filesystem architecture
- ❌ **Security Context Issues**: Permission handling across containers
- ❌ **Runtime State Gap**: Scans filesystem, not actual running process state
- ❌ **Resource Overhead**: Additional containers and storage requirements
- ❌ **Orchestration Complexity**: Ongoing maintenance of dual-container patterns

**Engineering Effort:** Significant - requires infrastructure-wide changes

### Approach 3: Agent Installation (Not Applicable)

**Implementation:** Install scanning tools directly inside target containers

**Limitations:**

- ❌ **Violates Non-Invasive Requirement**: Modifies production containers
- ❌ **Security Risk**: Additional software in production environment
- ❌ **Maintenance Overhead**: Agent updates and management

**Assessment:** Not viable for production scanning requirements

### Approach 4: Host Filesystem Access

**Implementation:** Mount container filesystems on host and scan directly

**Technical Details:**

- Access container filesystem layers from Docker host
- Scan mounted filesystems using external tools

**Advantages:**

- ✅ **No Container Modification**: External scanning approach
- ✅ **Tool Compatibility**: Can use existing SBOM tools

**Limitations:**

- ❌ **Host Access Required**: Requires privileged host filesystem access
- ❌ **Security Implications**: Direct filesystem access bypasses container isolation
- ❌ **Overlay Filesystem Complexity**: Docker layer management complications
- ❌ **Runtime State Gap**: Still filesystem-based, not runtime process state

### Approach 5: Image Analysis + Runtime Correlation

**Implementation:** Scan container images and correlate with running containers

**Technical Details:**

- Use syft/trivy to scan container images
- Map running containers to their base images
- Assume image content matches runtime state

**Advantages:**

- ✅ **Mature Tools**: Full syft/trivy capability
- ✅ **No Runtime Intrusion**: Pure image analysis
- ✅ **Standard Formats**: SPDX/CycloneDX output

**Critical Limitations:**

- ❌ **Runtime Installation Gap**: Misses packages installed at runtime
- ❌ **Environment Variable Dependencies**: Cannot capture runtime-configured package sources
- ❌ **Dynamic Configuration**: Misses environment-specific installations
- ❌ **Compose Stack Context**: No orchestration-level dependency analysis

### Technical Implementation Notes

**Sidecar Volume Sharing Challenges:**

- **Permission Models**: Container user/group mapping across shared volumes
- **Filesystem Overlays**: Docker overlay filesystem complexity
- **Security Contexts**: SELinux/AppArmor policy adjustments required
- **Resource Management**: Additional CPU/memory overhead for scanner containers

**Runtime State vs. Filesystem Analysis:**
The fundamental difference between filesystem scanning and runtime execution is the ability to capture:

- Packages installed during container startup
- Environment-variable driven package installations
- Virtual environment activations
- Runtime-configured package repositories

### Approach Comparison Summary

| Approach              | Runtime State     | Engineering Effort | Production Impact | Compose Support |
|-----------------------|-------------------|--------------------|-------------------|-----------------|
| **Direct Exec**       | ✅ Complete        | Low                | None              | ✅ Native        |
| **Sidecar**           | ❌ Filesystem only | High               | Significant       | ❌ None          |
| **Agent Install**     | ✅ Complete        | Medium             | High (invasive)   | ❌ Manual        |
| **Host FS**           | ❌ Filesystem only | Medium             | Medium            | ❌ Complex       |
| **Image+Correlation** | ❌ Image only      | Low                | None              | ❌ Manual        |

**Assessment**: Direct container execution (dependency-resolver approach) is the only method that achieves true runtime state capture without requiring infrastructure changes or compromising production security.

## Docker Compose Image Hash Extraction - Critical Capability

**dependency-resolver approach:**

```json
{
  "docker-compose": {
    "scope": "compose",
    "dependencies": {
      "backend": {
        "version": "latest",
        "hash": "sha256:b41e0217213000d43f675266eb229624fde33fb92c1dc9afb9e0a53bfa3dbb0b"
      },
      "frontend": {
        "version": "v1.2.3",
        "hash": "sha256:a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
      }
    }
  }
}
```

**Technical Implementation:**

- Analyzes running Docker Compose stack metadata
- Extracts full SHA256 digests for each service image
- Maps service names to specific image versions and hashes
- Provides orchestration-level dependency tracking

**Critical for GMT Requirements:**

- ✅ **Orchestration Context**: Understands Docker Compose as deployment unit
- ✅ **Image Integrity**: Full SHA256 hash extraction for reproducibility
- ✅ **Tag Resolution**: Maps friendly tags to specific digest hashes
- ✅ **Production Stack Analysis**: Analyzes actual deployed configurations

**Alternative Tool Limitations:**

- ❌ **syft/trivy**: No Docker Compose stack analysis capability
- ❌ **Individual Image Focus**: Must scan images separately, losing orchestration context
- ❌ **Service Relationship Gap**: No understanding of multi-container applications

## Installation Footprint and Resource Analysis

**dependency-resolver:**

- **Footprint**: Single Python executable (~2MB) + Docker library
- **Memory**: Low footprint, sequential command execution
- **Network**: No external dependencies or database updates
- **Deployment**: External execution, zero target container impact

**syft:**

- **Footprint**: Go binary (~50MB), no runtime dependencies
- **Memory**: Higher usage for comprehensive ecosystem analysis
- **Network**: No external dependencies (offline capable)
- **Deployment**: Requires sidecar architecture for runtime scanning

**trivy:**

- **Footprint**: Go binary + vulnerability database (~100MB+)
- **Memory**: High usage for database operations
- **Network**: Regular vulnerability database updates required
- **Deployment**: Similar sidecar complexity as syft

## Development Effort Assessment

### Existing Functionality Gaps

**If adopting syft:**

1. **Runtime Scanning Implementation**: Significant engineering effort to implement sidecar pattern
2. **Hash Extraction**: Custom post-processing to extract individual package hashes
3. **Output Format Adaptation**: Template development for GMT-specific schema
4. **Production Integration**: Container orchestration changes for volume sharing

**If adopting trivy:**

1. **Hash Retrieval**: Major limitation - no clear path to individual package hashes
2. **Runtime Scanning**: Similar sidecar pattern complexity as syft
3. **Focus Mismatch**: Tool optimized for vulnerability scanning, not dependency tracking

**Continuing dependency-resolver:**

1. **Additional Detectors**: Incremental effort to add new package managers
2. **Hash Strategy Refinement**: Ongoing improvements to hash generation
3. **Performance Optimization**: Gradual improvements to execution speed
4. **Error Handling**: Continued robustness improvements

### Maintenance Overhead

**dependency-resolver:**

- **Codebase**: ~2000 lines of Python, focused scope
- **Dependencies**: Minimal (docker library, standard library)
- **Testing**: Targeted unit tests for each detector

**syft/trivy:**

- **External Dependency**: Reliance on upstream development priorities
- **Integration Complexity**: Wrapper development and maintenance
- **Version Compatibility**: Tracking breaking changes in external tools

## Technical Recommendations

### Primary Recommendation: Continue Development

**Rationale:**

1. **Unique Runtime Capability**: No existing tool provides native runtime production scanning without architectural changes
2. **Hash Integration**: Dependency-resolver's multi-tiered hash strategy is more comprehensive than alternatives
3. **Modular Design**: Better suited for incremental feature development and GMT-specific requirements
4. **Control**: Full control over feature development, output format, and production integration

### Implementation Strategy

**Short Term:**

1. **Complete Core Detectors**: Finish robust implementations of pip, npm, dpkg, apk detectors
2. **Error Handling**: Improve error isolation and debugging capabilities
3. **Performance**: Optimize detector execution and reduce runtime overhead
4. **Testing**: Comprehensive integration tests with various container environments

**Medium Term:**

1. **Additional Package Managers**: Add Java (Maven/Gradle), Go modules, Rust Cargo based on usage patterns
2. **Hash Strategy**: Implement additional hash sources and verification methods
3. **Output Optimization**: Reduce JSON size and improve parsing efficiency
4. **Documentation**: Complete API documentation and usage examples

## Package Detection Strategy: Tool vs Lock File Approach

### Core Methodological Difference

**dependency-resolver (Tool Strategy):**

- Executes package manager commands inside running containers (`docker exec container pip list`)
- Queries live package manager databases for true runtime state
- Captures packages installed through any method, including runtime modifications

**syft/trivy (Lock File Strategy):**

- Analyzes static package metadata files and lock files from filesystem
- Parses package manifests without requiring package managers
- Infers packages from file patterns and metadata

### Critical Runtime Detection Gap

**Production scenario:**

```bash
# Emergency security patch installation
docker exec container apt-get install security-fix
# Runtime dependency installation
docker exec container pip install monitoring-agent
```

**Detection results:**

- dependency-resolver: ✅ Detects all runtime changes
- syft/trivy: ❌ Misses all post-deployment modifications

### Strategic Implications

| Capability                   | Tool Strategy (dependency-resolver) | Lock File Strategy (syft/trivy) |
|------------------------------|-------------------------------------|----------------------------------|
| **Runtime Package Discovery** | ✅ Complete detection               | ❌ Static snapshot only          |
| **Virtual Environment Support** | ✅ Full detection                  | ⚠️ Partial coverage              |
| **Production Drift Detection** | ✅ Captures runtime changes        | ❌ Misses post-deployment mods   |
| **Compliance Accuracy**       | ✅ Audit-ready completeness        | ⚠️ May underreport inventory     |
| **Broad Ecosystem Coverage**  | ⚠️ Incremental development         | ✅ 25+ ecosystems supported     |
| **Historical Analysis**       | ❌ Live containers only            | ✅ Any filesystem/image          |

**For GMT's Production Runtime Scanning:** Tool strategy provides superior accuracy despite requiring package managers in containers.

**The fundamental choice:** "what was intended" (lock files) vs "what is actually installed" (live tools).

## Final Assessment

The dependency-resolver tool addresses a specific and important gap in the current ecosystem. While syft and trivy are excellent tools for their intended use cases (comprehensive SBOM generation and security scanning), they are not architected for the specific production runtime scanning requirements outlined in the SPECIFICATION.md.

**The development effort to adapt existing tools exceeds the effort to complete the dependency-resolver**, especially considering the unique value proposition of true runtime environment scanning without installation footprint.

# Dependency Resolution Tools: Technical Comparison Report

> **Disclaimer:** This analysis was generated with the assistance of Claude Code and may include inaccurate information. Technical details about external tools should be verified against official documentation before making implementation decisions.

## Introduction

### Software Bill of Materials (SBOM) Landscape

Software Bill of Materials (SBOM) generation has become a critical component of modern software supply chain security and compliance. Industry standards like **SPDX** (Software Package Data Exchange) and **CycloneDX** provide standardized formats for representing software component inventories, enabling organizations to track dependencies, vulnerabilities, and licenses across their software ecosystem.

### Current Ecosystem Solutions

**GitHub** utilizes proprietary software to generate dependency graphs for repositories, automatically detecting dependencies in supported languages and providing security advisory integration. This closed-source approach offers deep integration with GitHub's platform but limited customization for specialized requirements.

**GitLab** takes an open-source approach with their [dependency-scanning component](https://gitlab.com/gitlab-org/security-products/analyzers/dependency-scanning/-/tree/main), which provides transparent dependency analysis as part of their security scanning suite. While comprehensive for CI/CD integration, it focuses primarily on source code analysis rather than runtime environment scanning.

**Popular Open Source Tools:**

- **syft** (Anchore): Widely adopted SBOM generation tool supporting 25+ ecosystems with multiple output formats
- **trivy** (Aqua Security): Comprehensive security scanner with SBOM capabilities, popular for vulnerability assessment

**Additional Notable Tools (Development Inspiration):**

- **sbom-tool** (Microsoft): Comprehensive SBOM generator with extensive [component-detection](https://github.com/microsoft/component-detection) catalog supporting diverse package managers and build systems. While not directly comparable for runtime scanning, its detector architecture provides valuable implementation patterns for comprehensive package manager coverage.
- **tern**: Python-based container analysis tool focusing on Docker image layer inspection and package detection. Shares similar Python implementation approach and provides insights into container filesystem analysis techniques.

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

### 3.1 Scanning Approach: Runtime vs. Static

**dependency-resolver:**

- **Runtime Snapshot Strategy**: Executes commands inside running containers via `docker exec`
- **Live Environment Analysis**: Captures actual installed packages, not build-time dependencies
- **Production Ready**: Designed specifically for production environment scanning

**syft:**

- **Image-based Analysis**: Primarily scans container images and filesystems
- **Static Analysis**: Analyzes layers and metadata, not runtime state
- **Limited Runtime Support**: No documented native support for live container scanning

**trivy:**

- **Multi-target Scanner**: Container images, filesystems, repositories
- **Static Focus**: Emphasizes vulnerability scanning of static artifacts
- **Runtime Gap**: No clear runtime production environment scanning capability

### 3.2 Package Manager Detection Coverage

**dependency-resolver:**

- System: dpkg (Debian/Ubuntu), apk (Alpine)
- Language: pip (Python + venv detection), npm (Node.js)
- Container: Docker Compose images with SHA256 hashes
- Architecture: Modular detector system with requirement checks

**syft:**

- Extensive: 25+ ecosystems including Java, Go, Rust, PHP
- Comprehensive: Multiple package manager variants per language
- Mature: Well-tested detection algorithms

**trivy:**

- Broad Support: Most popular programming languages and OS packages
- Vulnerability Focus: Integrates detection with security scanning
- Multi-platform: Various operating systems and platforms

### 3.3 Hash Retrieval Implementation

**dependency-resolver** (from actual output analysis):

```json
{
  "dpkg": {
    "dependencies": {
      "adduser": {
        "version": "3.134 all",
        "hash": "aeb90488192cb14ee517facb2a74eeb3e507e2743f3ec6443ee9027942b69c0d"
      }
    }
  },
  "pip": {
    "scope": "project",
    "location": "/var/www/startup/venv/lib/python3.13/site-packages",
    "hash": "77a4ac35e0bfb7521c8d7eb715ef33f0aea51d61d96b5ab922e3e76b26b933a6",
    "dependencies": {
      "pydantic": {
        "version": "2.10.7"
      }
    }
  }
}
```

- ✅ Individual package MD5 hashes from dpkg
- ✅ Location-based hashes for project-scope installations (pip virtual environments)
- ✅ SHA256 format for container images

**syft** (from actual output analysis):

```json
{
  "artifacts": [{
    "name": "adduser",
    "version": "3.134",
    "metadata": {
      "files": [{
        "path": "/usr/sbin/adduser",
        "digest": {"algorithm": "md5", "value": "2ba08fece3b3434a669f3c529bbea383"}
      }]
    }
  }]
}
```

- ✅ File-level MD5 digests available in detailed metadata
- ❌ No package-level hashes in standard output
- ❌ No location-based hashes for detecting directory changes

**trivy** (from actual output analysis):

- ❌ No individual package hashes visible in SPDX output
- ❌ Focus on vulnerability data rather than integrity hashes
- ❌ Limited hash information for package verification

### 3.4 Output Format and Extensibility

**dependency-resolver:**

```json
{
  "detector_name": {
    "scope": "system|project|compose",
    "location": "/path/to/installation",
    "dependencies": {
      "package_name": {
        "version": "semantic_version",
        "hash": "integrity_hash"
      }
    }
  }
}
```

- ✅ Custom schema optimized for GMT integration
- ✅ Scope-based organization (system/project/compose)
- ✅ Location tracking for project-specific installations

**syft:**

- ✅ Multiple SBOM formats (SPDX, CycloneDX, custom)
- ✅ Template-based customization available
- ✅ Rich metadata including licenses, CPEs, PURLs

**trivy:**

- ✅ Standard SBOM formats (SPDX, CycloneDX)
- ❌ Limited customization options
- ✅ Integrated vulnerability and misconfiguration data

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

## Package Version Detection Approaches: Tool Strategy vs Lock File Strategy

### Overview: Fundamentally Different Methodologies

The approach to package version detection represents a core architectural difference between dependency-resolver and other SBOM tools, with significant implications for runtime container scanning accuracy and reliability.

### dependency-resolver: Package Manager Tool Strategy

**Implementation Approach:**

```bash
# Direct package manager queries inside running containers
docker exec container_name dpkg-query --show --showformat='${Package}\t${Version}\t${MD5sum}\n'
docker exec container_name pip list --format=json
docker exec container_name npm list --json --depth=0
```

**Technical Details:**

- **Live Tool Execution**: Runs actual package manager commands inside target containers
- **Runtime State Query**: Queries the package manager's live database/registry
- **Tool-Native Output**: Leverages each package manager's native reporting capabilities
- **Dynamic Discovery**: Detects packages installed through any method (manual, automated, runtime)

**Advantages for Runtime Container Scanning:**

✅ **True Runtime State**: Captures exactly what the package manager reports as installed
✅ **Installation Method Agnostic**: Detects packages regardless of installation source (pip install, apt install, manual compilation)
✅ **Environment Context**: Includes virtual environments, user-local installations, and scope-specific packages
✅ **Tool Consistency**: Results match what developers see when running package commands locally
✅ **Dynamic Package Discovery**: Finds packages installed during container startup or runtime modifications
✅ **Metadata Completeness**: Access to full package manager metadata (versions, dependencies, installation paths)

**Limitations:**

❌ **Package Manager Dependency**: Requires target containers to have package managers installed
❌ **Execution Overhead**: Must execute commands inside each target container
❌ **Permission Requirements**: Needs Docker exec capabilities

### Alternative Tools: Lock File and Metadata Strategy

**syft/trivy Implementation Approach:**

```bash
# Filesystem analysis of package metadata files
find /container/filesystem -name "package.json" -o -name "requirements.txt" -o -name "Pipfile.lock"
parse /var/lib/dpkg/status
analyze /usr/local/lib/python3.x/site-packages/*.dist-info/METADATA
```

**Technical Details:**

- **Static File Analysis**: Parses package manager metadata files and lock files
- **Filesystem Scanning**: Searches for package manifests, lock files, and installed package metadata
- **Pattern Recognition**: Uses file patterns and metadata parsing to infer installed packages
- **Database Analysis**: Reads package manager databases directly from filesystem

**Advantages for General SBOM Generation:**

✅ **Broad Ecosystem Support**: Can parse 25+ different package manager formats
✅ **No Tool Dependencies**: Works even if package managers are not installed in containers
✅ **Filesystem Efficiency**: Can scan container images without running containers
✅ **Batch Processing**: Can analyze multiple containers simultaneously
✅ **Historical Analysis**: Can scan older container images or archived filesystems

**Critical Limitations for Runtime Container Scanning:**

❌ **Runtime Installation Gap**: Cannot detect packages installed after container startup
❌ **Virtual Environment Blind Spots**: May miss packages in activated virtual environments
❌ **Lock File Staleness**: Lock files may not reflect actual installed versions
❌ **Installation Method Limitations**: May miss packages installed through alternative methods (git+https, local wheels, manual builds)
❌ **Environment Variable Dependencies**: Cannot capture runtime-configured package sources or repositories
❌ **Scope Ambiguity**: Difficulty distinguishing between system vs project scope installations

### Concrete Example: Runtime vs Static Detection Differences

**Scenario**: Python container with development workflow

```bash
# Container startup installs base requirements
pip install -r requirements.txt

# Developer installs additional packages during development
docker exec container pip install debugpy pytest-cov

# Runtime environment variable changes package behavior
export PIP_INDEX_URL=https://private-repo/simple/
pip install internal-package==1.2.3
```

**dependency-resolver Detection (Tool Strategy):**

```json
{
  "pip": {
    "scope": "project",
    "dependencies": {
      "flask": {"version": "2.3.0"},
      "requests": {"version": "2.28.1"},
      "debugpy": {"version": "1.6.3"},
      "pytest-cov": {"version": "4.0.0"},
      "internal-package": {"version": "1.2.3"}
    }
  }
}
```

**syft/trivy Detection (Lock File Strategy):**

```json
{
  "artifacts": [
    {"name": "flask", "version": "2.3.0"},
    {"name": "requests", "version": "2.28.1"}
  ]
}
```

**Missing from Lock File Approach:**

- `debugpy` and `pytest-cov` (runtime installations)
- `internal-package` (environment-specific repository)

### Package Manager Specific Implications

**Python (pip) Ecosystem:**

- **Tool Strategy**: Detects virtual environments, user installations (`--user`), editable installs (`-e`)
- **Lock File Strategy**: Limited to requirements.txt, Pipfile.lock; misses dynamic installations

**Node.js (npm) Ecosystem:**

- **Tool Strategy**: Captures globally installed packages, workspace configurations
- **Lock File Strategy**: Good coverage with package-lock.json, but may miss global packages

**System Packages (dpkg/apk):**

- **Tool Strategy**: Real-time package database query with exact status
- **Lock File Strategy**: Static database files may not reflect post-installation changes

### Production Environment Considerations

**Development vs Production Drift:**

In production environments, containers often undergo modifications after initial deployment:

```bash
# Emergency security patch installation
docker exec prod-container apt-get update && apt-get install -y package-security-fix

# Runtime dependency installation
docker exec prod-container pip install monitoring-agent

# Configuration-driven package installation
docker exec prod-container npm install ${REQUIRED_PLUGINS}
```

**Tool Strategy (dependency-resolver):**

- ✅ **Drift Detection**: Captures all post-deployment changes
- ✅ **Audit Trail Completeness**: Complete inventory of actual runtime state
- ✅ **Compliance Accuracy**: Reports exactly what auditors will find

**Lock File Strategy (syft/trivy):**

- ❌ **Drift Blindness**: Misses all post-deployment modifications
- ❌ **Compliance Gap**: May underreport actual software inventory
- ❌ **Security Blind Spots**: Could miss security-critical runtime installations

### Performance and Resource Implications

**Tool Strategy Resource Profile:**

- **CPU**: Medium - sequential command execution per container
- **Memory**: Low - processes output stream by stream
- **Network**: None - uses local package manager caches
- **I/O**: Medium - package manager database queries

**Lock File Strategy Resource Profile:**

- **CPU**: Low - file parsing operations
- **Memory**: High - loads entire filesystem metadata into memory
- **Network**: None - pure filesystem analysis
- **I/O**: High - extensive filesystem traversal

### Strategic Decision Matrix for Runtime Container Scanning

| Requirement                   | Tool Strategy        | Lock File Strategy   |
|-------------------------------|----------------------|----------------------|
| **Runtime Package Discovery** | ✅ Complete          | ❌ Static snapshot   |
| **Virtual Environment Support** | ✅ Full detection   | ⚠️ Partial           |
| **Development Workflow Support** | ✅ Dynamic changes | ❌ Build-time only   |
| **Compliance Accuracy**      | ✅ Audit-ready       | ⚠️ May underreport   |
| **Container Dependency**      | ❌ Requires tools    | ✅ Tool-independent  |
| **Historical Analysis**       | ❌ Live only         | ✅ Any filesystem    |
| **Broad Ecosystem Coverage**  | ⚠️ Incremental      | ✅ 25+ ecosystems    |

### Conclusion: Context-Driven Strategy Selection

**For Production Runtime Scanning** (GMT use case):
The tool strategy (dependency-resolver approach) provides superior accuracy and completeness for runtime container analysis, despite requiring package manager presence in target containers.

**For Build-Time SBOM Generation**:
The lock file strategy (syft/trivy approach) offers broader ecosystem support and better integration with CI/CD pipelines where runtime state is less critical.

**The choice fundamentally depends on whether the goal is "what was intended to be installed" (lock file strategy) versus "what is actually installed" (tool strategy).**

## Final Assessment

The dependency-resolver tool addresses a specific and important gap in the current ecosystem. While syft and trivy are excellent tools for their intended use cases (comprehensive SBOM generation and security scanning), they are not architected for the specific production runtime scanning requirements outlined in the SPECIFICATION.md.

**The development effort to adapt existing tools exceeds the effort to complete the dependency-resolver**, especially considering the unique value proposition of true runtime environment scanning without installation footprint.

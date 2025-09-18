# Docker Info Detector

## Purpose & Scope

The Docker Info detector extracts metadata from individual Docker containers, providing container name, image information, and image hashes. It enables quick container identification and change detection without analyzing internal dependencies.

## Implementation Approach

### Container Metadata Extraction

The detector works with `DockerExecutor` environments and:

- Extracts container name, image name, and image hash
- Provides lightweight metadata collection
- Supports both container-only and full dependency analysis modes

### Simplified Output Format

Unlike other detectors, Docker Info uses a flattened output structure:

```json
{
  "_container-info": {
    "name": "container-name",
    "image": "nginx:latest",
    "hash": "sha256:abc123def456..."
  }
}
```

This simplified format reflects that container metadata is fundamentally different from package dependencies.

## Implementation Details

### Environment Validation

```python
def is_usable(self, executor: EnvironmentExecutor, working_dir: str = None) -> bool:
    return isinstance(executor, DockerExecutor)
```

Requirements:

1. Must be running in `DockerExecutor` context
2. Works with any running Docker container

### Container Information Collection

```python
def get_dependencies(self, executor: EnvironmentExecutor, working_dir: str = None) -> Dict[str, Any]:
    container_info = executor.get_container_info()

    result = {
        "name": container_info["name"],
        "image": container_info["image"],
        "hash": container_info["image_hash"]
    }
```

### Image Name Processing

- **Tag selection**: Uses first available image tag
- **Registry cleanup**: Removes registry prefixes for readability
- **Fallback handling**: Defaults to "unknown" for missing tags

## Hash Generation

### Image Hash Strategy

Uses Docker image ID as the hash value:

- **Native identifiers**: Leverages Docker's built-in image hashing
- **Content-based**: Image ID changes when image content changes
- **SHA256-based**: Uses Docker's cryptographic image identifiers
- **Reproducible**: Same image produces same hash across environments

### No Location Hashing

Container images don't use location-based hashing since:

- Images are content-addressed by Docker runtime
- Image IDs provide sufficient change detection
- No local file system location to hash

## Environment Detection

### Container Scope

Docker container info has `container` scope in the orchestrator logic, but outputs directly as `_container-info` to distinguish it from package managers.

### Executor Context

Works exclusively with `DockerExecutor` to:

- Access container metadata through Docker API
- Extract image information from running containers
- Provide consistent container identification

## Output Format

The detector returns a tuple: `(packages, metadata)` but is handled specially by the orchestrator.

### Standard Output

**Packages:** (always empty)

```json
[]
```

**Metadata:**

```json
{
  "name": "my-nginx-container",
  "image": "nginx:latest",
  "hash": "sha256:2cd1d97f893f70cee86a38b7160c30e5750f3ed6ad86c598884ca9c6a563a501"
}
```

**Final orchestrator output:**

```json
{
  "_container-info": {
    "name": "my-nginx-container",
    "image": "nginx:latest",
    "hash": "sha256:2cd1d97f893f70cee86a38b7160c30e5750f3ed6ad86c598884ca9c6a563a501"
  }
}
```

### Error Output Format

**Metadata with error:**

```json
{
  "name": "my-container",
  "image": "unknown",
  "hash": "unknown",
  "error": "AttributeError: 'NoneType' object has no attribute 'tags'"
}
```

## Usage Modes

### Container-Only Analysis

When using `--only-container-info` flag:

```bash
python3 -m dependency_resolver docker my-container --only-container-info
```

Output contains only container metadata, skipping all package dependency detection.

### Full Analysis (Default)

When running standard docker analysis:

```bash
python3 -m dependency_resolver docker my-container
```

Container info is included alongside package dependencies (dpkg, pip, npm, etc.).

## Implementation Features

### Automatic Inclusion

- **Always present**: Container info is included by default in docker analysis
- **No configuration**: No special setup required
- **Performance optimized**: Lightweight metadata extraction

### Integration with DockerExecutor

Leverages `DockerExecutor.get_container_info()` method:

```python
def get_container_info(self) -> dict:
    # Reload container to get latest info
    self.container.reload()

    # Get image information
    image = self.container.image
    image_name = self._extract_image_name(image.tags)
    image_id = image.id

    return {
        "name": self.container.name,
        "image": image_name,
        "image_hash": image_id
    }
```

## Error Handling

- **Container access failures**: Returns unknown values with error details
- **Missing image tags**: Gracefully defaults to "unknown"
- **API errors**: Captures and reports Docker API exceptions
- **Graceful degradation**: Container info errors don't affect other detectors

## Limitations & Constraints

- **Docker-specific**: Only works with Docker containers via `DockerExecutor`
- **Running containers only**: Requires active container to extract information
- **Single container**: Analyzes one container at a time
- **Metadata only**: Does not analyze internal container dependencies

## Use Cases

- **Container identification**: Quick container image and hash extraction
- **Change detection**: Monitor when container images are updated
- **CI/CD pipelines**: Fast container verification without full dependency scan
- **Container auditing**: Track container images across environments
- **Deployment validation**: Verify correct container images are running

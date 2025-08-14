# Docker Compose Detector

## Purpose & Scope

The Docker Compose detector identifies container images and their dependencies in Docker Compose environments. It extracts service names, image names, tags, and image hashes for comprehensive container dependency tracking.

## Implementation Approach

### Container Detection

The detector specifically works with `DockerComposeExecutor` environments and:

- Retrieves active containers from the Docker Compose stack
- Extracts service names from container naming conventions
- Collects image information including tags and unique identifiers

### Service Name Extraction

Handles both modern and legacy Docker Compose naming patterns:

**Modern naming:** `<project>-<service>-<number>`

- Example: `myapp-web-1` → service: `web`

**Legacy naming:** `<project>_<service>_<number>`

- Example: `myapp_web_1` → service: `web`

**Fallback:** Uses full container name if patterns don't match

### Image Information Collection

For each container service:

- **Image Name**: Extracts readable name from image tags
- **Image Hash**: Uses Docker image ID as unique identifier
- **Registry Handling**: Removes registry prefixes for cleaner display

## Implementation Details

### Environment Validation

```python
def is_usable(self, executor: EnvironmentExecutor, working_dir: str = None) -> bool:
    return isinstance(executor, DockerComposeExecutor) and len(executor.get_containers()) > 0
```

Requirements:

1. Must be running in `DockerComposeExecutor` context
2. Must have active containers to process

### Container Processing

```python
# Get container details
container.reload()

# Extract service name from container name
service_name = self._extract_service_name(container.name, executor.stack_name)

# Get image information
image = container.image
image_name = self._extract_image_name(image.tags)
image_id = image.id
```

### Error Isolation

Individual container processing failures don't affect other containers:

- Continues processing remaining containers
- Logs warnings for failed containers
- Graceful handling of missing attributes

## Hash Generation

### Image Hash Strategy

Uses Docker image ID as the hash value:

- **Authentic hashes**: Native Docker image identifiers
- **Change detection**: Image ID changes when image content changes
- **Uniqueness**: SHA256-based Docker image identifiers

### No Location Hashing

Container images don't use location-based hashing since:

- Images are content-addressed by Docker
- Image IDs provide sufficient change detection
- No local file system location to hash

## Environment Detection

### Compose Scope

Docker Compose containers have `compose` scope, distinct from:

- `system` scope (system packages)
- `project` scope (project-specific dependencies)

### Stack Context

Leverages `DockerComposeExecutor.stack_name` to:

- Identify containers belonging to the compose stack
- Extract meaningful service names from container names
- Filter containers relevant to the dependency analysis

## Output Format

```json
{
  "scope": "compose",
  "dependencies": {
    "web": {
      "version": "nginx:1.21-alpine",
      "hash": "sha256:abc123def456..."
    },
    "db": {
      "version": "postgres:13",
      "hash": "sha256:def789ghi012..."
    }
  }
}
```

## Service Name Resolution

### Naming Pattern Recognition

```python
def _extract_service_name(self, container_name: str, stack_name: str) -> str:
    # Modern: project-service-number
    if container_name.startswith(f"{stack_name}-"):
        service_part = container_name[len(f"{stack_name}-"):]
        return re.sub(r"-\d+$", "", service_part)

    # Legacy: project_service_number
    if container_name.startswith(f"{stack_name}_"):
        service_part = container_name[len(f"{stack_name}_"):]
        return re.sub(r"_\d+$", "", service_part)

    # Fallback: full container name
    return container_name
```

### Image Name Extraction

```python
def _extract_image_name(self, tags: List[str]) -> str:
    if not tags:
        return "unknown"

    first_tag = tags[0]

    # Remove registry prefix for readability
    if "/" in first_tag:
        return first_tag.split("/")[-1]

    return first_tag
```

## Limitations & Constraints

- **Compose-specific**: Only works with Docker Compose environments
- **Active containers only**: Requires running containers to extract information
- **Naming dependency**: Service name extraction depends on Docker Compose naming conventions
- **Single executor type**: Limited to `DockerComposeExecutor` context

## Error Handling

- **Container failures**: Individual container processing errors don't stop overall detection
- **Missing attributes**: Graceful handling of missing container/image properties
- **Empty container lists**: Returns empty dependencies when no containers are found
- **Image tag issues**: Defaults to "unknown" when image tags are unavailable

## Use Cases

- **Multi-service applications**: Track all services in a Docker Compose stack
- **Image change detection**: Monitor when container images are updated
- **Service dependency mapping**: Understand service composition in containerized applications
- **Version tracking**: Track specific image versions and tags across environments

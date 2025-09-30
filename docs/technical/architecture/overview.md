# Architecture Overview

The energy-dependency-inspector follows a modular architecture designed for extensibility and maintainability.

## High-Level Architecture

```plain
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Interface │    │ Programmatic API │    │   Core Library  │
└─────────┬───────┘    └─────────┬────────┘    └─────────┬───────┘
          │                      │                       │
          └──────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │      Orchestrator       │
                    │  (Dependency Manager)   │
                    └────────────┬────────────┘
                                 │
               ┌─────────────────┼─────────────────┐
               │                 │                 │
    ┌──────────▼──────────┐ ┌───▼────┐ ┌─────────▼────────┐
    │   HostExecutor      │ │ Docker │ │  OutputFormatter │
    │                     │ │Executor│ │                  │
    └─────────────────────┘ └────────┘ └──────────────────┘
               │                 │
               └─────────────────┼─────────────────────────┐
                                 │                         │
                    ┌────────────▼─────────────┐          │
                    │      Detector Layer      │          │
                    └──────────────────────────┘          │
                                 │                         │
        ┌────────────────────────┼────────────────────────┬┘
        │            │           │           │            │
   ┌────▼───┐ ┌─────▼────┐ ┌───▼───┐ ┌─────▼────┐ ┌────▼────┐
   │  dpkg  │ │   apk    │ │  pip  │ │   npm    │ │ docker  │
   │Detector│ │ Detector │ │Detector│ │ Detector │ │  info   │
   └────────┘ └──────────┘ └───────┘ └──────────┘ └─────────┘
```

## Core Components

### Orchestrator

**Purpose**: Central coordinator that manages the dependency resolution process.

**Responsibilities**:

- Instantiate and configure detectors
- Execute detectors in the appropriate order
- Aggregate results from all detectors
- Handle errors and provide unified error handling

### Executors

**Purpose**: Abstract the execution environment (host system vs Docker container).

**Types**:

- **HostExecutor**: Executes commands on the host system
- **DockerExecutor**: Executes commands inside Docker containers

**Responsibilities**:

- Execute shell commands in the target environment
- Handle environment-specific concerns
- Provide consistent interface regardless of execution target

### Detectors

**Purpose**: Package manager-specific logic for detecting dependencies.

**Characteristics**:

- Implement `PackageManagerDetector` interface
- Self-contained and independent
- Handle specific package manager formats and commands

### OutputFormatter

**Purpose**: Format the aggregated results into consumable output formats.

**Responsibilities**:

- Convert internal data structures to JSON
- Handle pretty-printing and formatting options
- Ensure consistent output schema

## Data Flow

1. **Input Processing**: CLI or API receives parameters (environment type, options)
2. **Orchestrator Setup**: Orchestrator configures detectors based on options
3. **Executor Creation**: Appropriate executor (Host/Docker) is instantiated
4. **Detector Execution**: Each detector runs in sequence:
   - Check if detector is usable in the environment
   - Extract dependencies if applicable
   - Return structured data
5. **Result Aggregation**: Orchestrator collects all detector results
6. **Output Formatting**: Results are formatted as JSON and returned

## Key Design Decisions

### Modular Detector Architecture (ADR-0002)

Each package manager is implemented as a separate detector class, allowing:

- Independent development and testing
- Easy addition of new package managers
- Consistent interface across all detectors

### Read-Only Operations (ADR-0003)

The system never modifies the target environment:

- No package installations or updates
- No file system modifications
- Only reads existing package metadata

### Runtime Snapshot Approach (ADR-0001)

Analyzes the current state of installed packages:

- No dependency resolution or tree building
- Captures what's actually installed
- Fast execution with minimal resource usage

## Extensibility Points

### Adding New Package Managers

1. Implement `PackageManagerDetector` interface
2. Register in `Orchestrator.__init__()`
3. Add appropriate tests
4. Document the implementation

### Adding New Execution Environments

1. Implement `EnvironmentExecutor` interface
2. Add factory method or constructor parameter
3. Update CLI/API to support new environment type

### Output Format Extensions

1. Extend `OutputFormatter` class
2. Add new formatting methods
3. Update CLI options if needed

## Error Handling Strategy

- **Graceful Degradation**: Failed detectors don't crash the entire process
- **Optional Dependencies**: Missing package managers are skipped, not errors
- **Debug Information**: Detailed error information available in debug mode
- **Consistent Interface**: All detectors return empty results on failure, not exceptions

## Performance Considerations

- **Parallel Execution**: Detectors could run in parallel (future enhancement)
- **Lazy Loading**: Detectors only execute if they're usable in the environment
- **Minimal Dependencies**: Core library has minimal external dependencies
- **Efficient Commands**: Use fastest package manager commands available

## Security Considerations

- **Command Injection Prevention**: All commands are parameterized appropriately
- **Privilege Requirements**: Designed to work without elevated privileges when possible
- **Container Isolation**: Docker execution is isolated from host system
- **Read-Only Access**: No write operations reduce security risk surface

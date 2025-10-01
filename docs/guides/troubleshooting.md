# Troubleshooting Guide

Common issues and solutions when using energy-dependency-inspector.

## General Issues

### No Output or Empty Results

**Problem**: The tool runs but produces no or minimal output.

**Solutions**:

1. Enable debug mode: `python3 -m energy_dependency_inspector --debug`
2. Check if package managers are installed in the target environment
3. Verify permissions to read package manager files

### Docker Container Issues

**Problem**: Cannot analyze Docker container.

**Solutions**:

1. Verify container is running: `docker ps`
2. Check container name/ID is correct
3. Ensure Docker daemon is accessible
4. Try with container ID instead of name

```bash
# List running containers
docker ps

# Use container ID
python3 -m energy_dependency_inspector docker a1b2c3d4e5f6
```

### Permission Errors

**Problem**: Permission denied when accessing system files.

**Solutions**:

1. Run with appropriate permissions (may need sudo for system analysis)
2. For Docker: ensure user is in docker group
3. Check file permissions in target directories

## Package Manager Specific Issues

### Python/Pip Detection

**Problem**: Virtual environment packages not detected.

**Solutions**:

1. Specify working directory: `--working-dir /path/to/project`
2. Ensure virtual environment is activated when analyzing host
3. Check virtual environment path is accessible

```bash
# For virtual environment analysis
python3 -m energy_dependency_inspector --working-dir /path/to/venv
```

### Node.js/NPM Detection

**Problem**: npm packages not detected.

**Solutions**:

1. Ensure `node_modules` directory exists
2. Run `npm install` first if packages aren't installed
3. Specify project directory: `--working-dir /path/to/project`

### System Package Detection

**Problem**: System packages (dpkg/apk) not detected.

**Solutions**:

1. Verify package manager is installed (`dpkg --version` or `apk --version`)
2. Check if running in appropriate environment (Debian/Ubuntu for dpkg, Alpine for apk)
3. Ensure access to package database files

## Debug Mode Analysis

Enable debug mode for detailed information:

```bash
python3 -m energy_dependency_inspector --debug
```

Debug output shows:

- Which detectors are being tried
- Command executions and their results
- Why detectors are skipped or fail
- Detailed error messages

## Environment-Specific Issues

### Docker Environment

**Common Issues**:

- Container not running
- Wrong container identifier
- Docker daemon not accessible

**Debug Steps**:

```bash
# Verify Docker is working
docker version

# List containers
docker ps -a

# Test container access
docker exec container_name echo "test"
```

### Host Environment

**Common Issues**:

- Missing package managers
- Permission restrictions
- Virtual environment not activated

**Debug Steps**:

```bash
# Check available package managers
which dpkg pip npm

# Test package manager commands
dpkg --version
pip --version
npm --version
```

## Output Issues

### Malformed JSON

**Problem**: Output is not valid JSON.

**Solutions**:

1. Use `--pretty-print` for readable format
2. Check for error messages mixed with output
3. Redirect stderr: `python3 -m energy_dependency_inspector 2>/dev/null`

### Missing Expected Packages

**Problem**: Known packages not appearing in output.

**Solutions**:

1. Check package manager scope (system vs project)
2. Try `--skip-os-packages` or include system scope
3. Verify packages are actually installed in target location
4. Check working directory is correct

## Performance Issues

### Slow Execution

**Problem**: Tool takes too long to run.

**Solutions**:

1. Use `--skip-os-packages` to skip system package managers
2. Use `--skip-hash-collection` to skip hash generation for packages and locations
3. Use `--select-detectors` to analyze only specific package managers (e.g., `--select-detectors "pip,npm"`)
4. For Docker container metadata only, use `--select-detectors "docker-info"`
5. Specify working directory to limit scope
6. Check if system has many installed packages

## Getting Help

If issues persist:

1. **Check Documentation**:
   - [CLI Guide](../usage/cli-guide.md)
   - [Output Format](../usage/output-format.md)
   - [Technical Documentation](../technical/)

2. **Enable Debug Mode**: Always include debug output when reporting issues

3. **Gather Information**:
   - Operating system and version
   - Python version
   - Package manager versions
   - Docker version (if applicable)
   - Complete error messages

4. **Test Environment**: Verify the issue in a minimal test environment

## Common Debug Commands

```bash
# Basic debug
python3 -m energy_dependency_inspector --debug

# Host analysis with debug
python3 -m energy_dependency_inspector host --debug

# Docker analysis with debug
python3 -m energy_dependency_inspector docker container_name --debug

# Skip system scope for faster testing
python3 -m energy_dependency_inspector --skip-os-packages --debug

# Test specific working directory
python3 -m energy_dependency_inspector --working-dir /path --debug
```

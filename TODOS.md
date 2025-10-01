# TODOS

- Add host_info_detector (similar to docker_info_detector)
- Extend the set of supported package managers with the common ones for Go, PHP and Java
- Add Dockerfile
- Add support for Podman
- Add configuration file
  - use Dependabot configuration as an inspiration (<https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference>)
  - Configure which package management systems should be checked
  - Configurable paths for package managers (like a path for venv resolution)
  - Make it configurable, if the JSON output is pretty-printed or not (at the start pretty-print is default)
  - Add different log levels
- Support more operating systems: RedHat Linux (yum/dnf), openSUSE (zypper)
- Add extraction of some relevant environment variables

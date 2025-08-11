# TODOS

- Add tests
  - cli flags
  - apk_detector
  - dpkg_detector
- Add support for Podman + Podman Compose
- Add configuration file
  - use Dependabot configuration as an inspiration (<https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference>)
  - Configure which package management systems should be checked
  - Configurable paths for package managers (like a path for venv resolution)
  - Override default commands (e.g., change from `pip list --format=freeze`)
  - Make it configurable, if the JSON output is pretty-printed or not (at the start pretty-print is default)
  - Add different log levels
- Extend the set of supported package managers with the common ones for Go, PHP and Java
- Support more operating systems: RedHat Linux (yum/dnf), openSUSE (zypper)
- Add extraction of some relevant environment variables
- Add license
- Implement auto-completion of container id / name

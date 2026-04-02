# PECL Detector

## Purpose & Scope

The PECL detector identifies PHP extensions installed via `pecl`. It is a system-scoped detector and also reports the active PHP runtime version.

## Commands Used

- **Usability check**: `pecl version`
- **Extension listing**: `pecl list`
- **PHP runtime version**: `php --version`

## Detection Logic

- Confirms `pecl` is available
- Runs `pecl list`
- Parses installed extension names and versions
- Adds `php_version` from the first line of `php --version`

## Hash Strategy

PECL does not provide a stable package-level hash source in this detector. No hashes are collected.

## Output Format

```json
{
  "scope": "system",
  "php_version": "PHP 8.3.7 (cli)",
  "dependencies": {
    "apcu": {
      "version": "5.1.24"
    },
    "xdebug": {
      "version": "3.3.2"
    }
  }
}
```

## Limitations

- Requires `pecl` to be installed and functional
- Reports extensions visible to `pecl list` only
- Does not collect hashes

# Composer Detector

## Purpose & Scope

The Composer detector identifies PHP packages managed by `composer` in both project and global environments. It follows the same multi-location output pattern used by the `pip` and `npm` detectors.

## Key Features

### Multi-Location Detection

Detects Composer packages in multiple locations:

- **Project dependencies**: All discovered Composer projects under the scan root
- **Global dependencies**: Packages installed in Composer's global project
- **Mixed output**: Returns both when they coexist in the same environment

### Project Discovery

For project scanning, the detector recursively searches for `composer.json` files:

- Under `working_dir` when one is provided
- Under `/` when `working_dir` is not provided
- Excludes paths under `vendor/` to avoid scanning installed dependencies as separate projects

## Commands Used

- **Usability check**: `composer --version`
- **PHP runtime version**: `php --version`
- **Project packages**: `composer show --direct --format=json --no-interaction`
- **Project discovery**: `find <scan-root> -name composer.json`
- **Global packages**: `composer global show --direct --format=json --no-interaction`
- **Project vendor dir**: `composer config vendor-dir --absolute`
- **Global vendor dir**: `composer global config vendor-dir --absolute`

## Hash Generation

The detector implements Tier 2 location-based hashing by hashing the Composer vendor directory contents while excluding:

- Git metadata (`.git`)
- Composer cache metadata (`.composer`)
- Log files (`*.log`)
- Temporary files (`*.tmp`, `*.temp`)

## Output Format

**Single Location** (project or global):

```json
{
  "scope": "project",
  "php_version": "PHP 8.3.7 (cli)",
  "location": "/app/vendor",
  "hash": "abc123...",
  "dependencies": {
    "monolog/monolog": {
      "version": "3.5.0"
    }
  }
}
```

**Mixed Locations** (project and global):

```json
{
  "scope": "mixed",
  "php_version": "PHP 8.3.7 (cli)",
  "locations": {
    "/app/vendor": {
      "scope": "project",
      "hash": "abc123...",
      "dependencies": {
        "laravel/framework": {
          "version": "11.0.0"
        }
      }
    },
    "/root/.config/composer/vendor": {
      "scope": "system",
      "hash": "def456...",
      "dependencies": {
        "psy/psysh": {
          "version": "0.12.0"
        }
      }
    }
  }
}
```

## Benefits

- Captures installed PHP packages from all discovered local projects plus the global Composer context
- Reports the active PHP runtime version alongside dependency data
- Uses Composer's JSON output for reliable parsing
- Respects `working_dir` as the recursive project scan root
- Preserves the repository's established mixed-location contract

## Limitations

- Requires `composer` to be installed and functional
- Reports direct installed dependencies only, not transitive packages
- Uses location-level hashing rather than package-level authentic hashes

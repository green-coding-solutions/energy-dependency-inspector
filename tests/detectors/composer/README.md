# Composer Detector Tests

Tests the Composer detector's project, global, and mixed-location behavior.

## Docker Fixture

`Dockerfile.test-node-php-composer` builds a combined test image with:

- Node.js from a slim Node base image
- PHP and Composer installed via `apt`
- An npm project at `/opt/node-test`
- A Composer project at `/opt/php-test`

## Running Tests

```bash
pytest tests/detectors/composer/
```

# README

## Origin

Origin of this test was a comment by Arne:
<https://github.com/green-coding-solutions/green-metrics-tool/pull/1297#issuecomment-3302240294>

This is my Dockerfile:

```dockerfile
FROM greencoding/gcb_playwright:v20

RUN cd /root && \
    python3 -m virtualenv venv  && \
    /root/venv/bin/pip install psutils

CMD ["tail", "-f", "/dev/null"]
```

psutils is not found

## Test

The test script validates that the issue was resolved.

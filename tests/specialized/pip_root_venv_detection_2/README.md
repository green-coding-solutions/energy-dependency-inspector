# README

## Origin

Origin of this test was a comment by Arne:
<https://github.com/green-coding-solutions/green-metrics-tool/pull/1297#issuecomment-3302325317>

My Dockerfile:

```dockerfile
FROM greencoding/gcb_playwright:v20

RUN cd /root && \
    python3 -m virtualenv venv  && \
    /root/venv/bin/pip install psutils

RUN rm /usr/bin/apt
RUN rm /usr/bin/dpkg
RUN rm /usr/bin/dpkg-query
RUN rm /usr/bin/python3

CMD ["tail", "-f", "/dev/null"]
```

Our tool finds nothing.

## Test

The test fails. The energy dependency inspector can't resolve the dependencies, because pip can't be executed:

```sh
/usr/local/bin/pip: cannot execute: required file not found
```

pip is missing python3.

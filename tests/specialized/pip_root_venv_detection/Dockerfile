FROM greencoding/gcb_playwright:v20

RUN cd /root && \
    python3 -m virtualenv venv  && \
    /root/venv/bin/pip install psutils

CMD ["tail", "-f", "/dev/null"]

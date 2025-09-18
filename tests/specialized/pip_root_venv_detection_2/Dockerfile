FROM greencoding/gcb_playwright:v20

RUN cd /root && \
    python3 -m virtualenv venv  && \
    /root/venv/bin/pip install psutils

RUN rm /usr/bin/apt
RUN rm /usr/bin/dpkg
RUN rm /usr/bin/dpkg-query
RUN rm /usr/bin/python3

CMD ["tail", "-f", "/dev/null"]

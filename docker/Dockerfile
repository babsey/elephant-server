FROM python:3.12-slim
LABEL maintainer="Sebastian Spreizer <spreizer@web.de>"

COPY . /elephant-server
RUN pip install /elephant-server

COPY ./docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 52428
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]


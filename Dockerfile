FROM python:3.12-slim
LABEL maintainer="Sebastian Spreizer <spreizer@web.de>"

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./elephant_server ./elephant_server
COPY ./bin/elephant-server ./elephant_server

EXPOSE 5001
# CMD [ "gunicorn", "--bind", "0.0.0.0:5001", "--capture-output", "--log-level", "debug",  "elephant_server:app" ]
CMD [ "elephant-server", "start"]

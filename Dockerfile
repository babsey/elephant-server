FROM python:3
LABEL maintainer="Sebastian Spreizer <spreizer@web.de>"

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./elephant_server ./elephant_server

EXPOSE 5000
CMD [ "python", "/usr/src/app/elephant_server/main.py" ]

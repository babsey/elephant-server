FROM python:3
LABEL maintainer="Sebastian Spreizer <spreizer@web.de>"

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./elephant_server ./elephant_server

EXPOSE 5000
CMD [ "gunicorn", "elephant_server:app", "--bind 0.0.0.0:5000" ]

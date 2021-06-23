FROM python:3.8.7

ENV PYTHONUNBUFFERED 1
ENV HTTP_PROXY http://192.168.2.9:5000/
ENV HTTPS_PROXY http://192.168.2.9:5000/

COPY reader/ /reader

COPY _CI/docker-entrypoint.sh /reader

WORKDIR /reader

RUN chmod +x docker-entrypoint.sh

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

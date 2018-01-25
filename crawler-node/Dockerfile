FROM python:3.6
# FROM pypy:3
ENV PYTHONUNBUFFERED 1

# RUN apt-get install ca-certificates

COPY ./src /src/

RUN pip install -r /src/requirements.txt

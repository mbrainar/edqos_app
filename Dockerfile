##
## Dockerfile for Event Driven QoS
##
FROM python:2-alpine
MAINTAINER Steven Luzynski <sluzynsk@cisco.com>
EXPOSE 5000

RUN pip install --no-cache-dir setuptools wheel

ADD . /app
WORKDIR /app
RUN pip install --requirement /app/requirements.txt
RUN FLASK_APP=app.py flask initdb
CMD ["python", "app.py"]

FROM jfloff/alpine-python:2.7-slim

WORKDIR /usr/local/bin

RUN pip install prometheus_client
ADD claymore-export.py .
ADD entrypoint.sh .
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

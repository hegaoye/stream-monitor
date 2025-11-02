FROM python:3.9.18

ENV PYTHONPATH=/app

COPY requirements.txt /app/
RUN apt update && apt install docker.io -y
RUN pip install --upgrade pip \
    && pip install wheel \
    && pip install -r /app/requirements.txt \
    && rm -rf ~/.cache/pip

COPY . /app/
ENTRYPOINT [ "sh", "-c", "python /app/run.py" ]

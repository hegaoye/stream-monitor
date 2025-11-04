FROM python:3.9-slim

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/* \

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app/
ENTRYPOINT [ "sh", "-c", "python /app/run.py" ]

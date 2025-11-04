FROM python:3.9-slim-bullseye

WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# 使用更稳定的 Debian 11 (bullseye) 源
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 复制 requirements 并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p logs

# 设置非 root 用户
RUN groupadd -r monitor && useradd -r -g monitor monitor \
    && chown -R monitor:monitor /app
USER monitor

CMD ["python", "main.py"]
# 使用说明

### 框架使用说明

工作原理

1. 流媒体协议处理
   使用 PyAV (FFmpeg) 处理 RTMP 协议
   RTMP (Real Time Messaging Protocol) 是 Adobe 的专有流媒体协议
   通过 FFmpeg 的 RTMP 解复用器解析流数据

2.健康监控机制
连接状态: 定期检查流连接
数据接收: 检查是否有持续的数据包
关键帧检测: 监控关键帧间隔
延迟估算: 基于最后包时间计算延迟

3.技术架构
多线程架构
Webhook 集成
可配置的检查间隔
多种警报级别

```text
PyAV (FFmpeg bindings)
    ↓
RTMP Demuxer (解复用器)
    ↓
Video/Audio Packets (数据包)
    ↓
Health Assessment (健康评估)
    ↓
Webhook Alerts (警报)
```

4.全面的监控指标
连接状态
数据包统计
关键帧检测
延迟估算
质量评估

### 安装依赖包

```shell
#安装依赖包, 加入：--break-system-packages 突破限制管理
pip install   --break-system-packages -r  requirements.txt
```

### 启动

```shell
#执行，启动后默认端口为 8080
python main.py
```

config.ymal 配置说明：

```yaml
# 监控配置
monitoring:
  check_interval: 10  # 检查间隔(秒)
  max_samples: 1000  # 最大样本数，监控视频流数据包的个数

# 流地址配置,支持批量监控
streams:
  - id: "video1" #视频流 id
    url: "https://demo1.com/demo1/demo1.flv" #视频流地址 仅支持http-flv
  - id: "video2" #视频流 id
    url: "https://demo2.com/demo2/demo2.flv" #视频流地址 仅支持http-flv


# 报警配置
webhook:
  enabled: false # true|false  设置为 true启用，需要确保 url 设置否则依然不起作用
  url: "https://demo.com/v1/alerts"   # 监控 streams 的可用性，延迟等统计信息，会以 json方式 post到此地址
```

webhook 举例：

```config
{
  "type": "stream_monitor",
  "timestamp": "2025-11-04T10:28:02.784071",
  "data": {
    "streamId": "video1",  # 视频 id
    "streamUrl": "https://demo.com/nw35/8-351.flv", # 视频流地址
    "playable": true, # 是否可以播放 true|false
    "quality": "good", #播放质量 poor|good|fair
    "delay": "149", # 延迟 单位ms
    "videoPackets": 250, # 视频包数
    "keyframes": 5, # 第几个关键帧
    "count": 2, # 检查的第几次
    "timestamp": "11/04/25 10:28:02", # 时间戳
    "bitrate": 532.5, # 码率
    "avgBitrate": 1140.3, # 平均码率
    "frameRate": 41.9, # 帧率
    "resolution": "1920x1080", # 分辨率
    "codec": "h264", # 编码
    "gopSize": 60, # GOP
    "bitrateStability": "stable", # 码率稳定性 stable|unstable
    "message": "流 video1 运行正常", # 综合信息
    "alertLevel": "info" # 监控稳定性级别 info|warning|error 和可播放性对应
  }
}
```


# Docker

## Build

```shell
#打包
docker build -t stream-monitor:latest .

#测试运行
docker run --rm stream-monitor:latest
```

## Test

```shell
#测试运行
docker run --rm stream-monitor:latest

#进入容器测试
docker run -it --rm stream-monitor:latest /bin/bash

#进入容器测试
docker run -it --entrypoint /bin/sh  stream-monitor-debug
```

## Run

```shell
docker run  --name stream-monitor  -v /home/config/config.yaml:/app/config.yaml  --restart always -d stream-monitor:latest
```

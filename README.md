# 使用说明

### 框架使用说明
框架采用
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

```json
{
  "type": "stream_monitor",
  "timestamp": "2025-11-04T09:56:28.185840",
  "data": {
    "streamId": "video1",
    "streamUrl": "https://demo.com/demo/demo.flv",
    "playable": true,
    "quality": "good",
    "delay": "985",
    "videoPackets": 209,
    "keyframes": 4,
    "count": 2,
    "timestamp": "2025-11-04T09:56:28.185019",
    "message": "流 video1 连接成功"
  }
}
```

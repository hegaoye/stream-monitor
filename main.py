import logging
import threading

from config.ConfigLoader import get_config
from monitor.SimpleStreamMonitor import SimpleStreamMonitor

# 配置日志
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def main():
    """主函数示例"""
    print("=== 流媒体可播放性监控系统 ===")

    # 使用简化的监控器
    stream_url = "http://192.168.8.125/live/livestream.flv"

    monitor = SimpleStreamMonitor(
        stream_url=stream_url,
        check_interval=5  # 5秒检查一次
    )

    try:
        # 启动监控（运行5分钟）
        import time
        monitor_thread = threading.Thread(target=monitor.start_monitoring)
        monitor_thread.daemon = True
        monitor_thread.start()

        # 等待5分钟或用户中断
        time.sleep(300)  # 5分钟

    except KeyboardInterrupt:
        print("\n用户中断监控")
    finally:
        monitor.stop()


if __name__ == '__main__':
    log.info("启动 Stream Monitor 服务器...")
    config = get_config()
    log.info(config.get("monitoring.playability.enabled"))
    log.info(config.get("monitoring.playability.health_checks.connection_timeout"))
    streams = config.get("streams")
    for stream in streams:
        log.info(stream["id"])
        log.info(stream["url"])
    main()

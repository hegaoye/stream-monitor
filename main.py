import threading

from config.ConfigLoader import get_config
from config.log4py import logger
from job.monitor_job import MonitorJob
from monitor.StreamMonitor import StreamMonitor


def main():
    """主函数示例"""
    logger.info("=== 流媒体可播放性监控系统 ===")

    # 使用简化的监控器
    stream_url = "https://bt-01-pull.g33-video.com/nw35/8-351.flv"

    monitor = StreamMonitor(
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
        logger.error("\n用户中断监控")
    finally:
        monitor.stop()


if __name__ == '__main__':
    logger.info("启动 Stream Monitor 服务器...")
    config = get_config()
    logger.info(config.get("monitoring.playability.enabled"))
    logger.info(config.get("monitoring.playability.health_checks.connection_timeout"))
    streams = config.get("streams")
    for stream in streams:
        stream_id = stream["id"]
        stream_url = stream["url"]

        logger.info("视频 id: %s , url: %s", stream_id, stream_url)
        check_interval = config.get("monitoring.general.check_interval")
        monitor_job = MonitorJob(stream_id, stream_url, check_interval)
        monitor_job.run()

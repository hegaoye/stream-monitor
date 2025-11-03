import threading

from config.log4py import logger
from monitor.SimpleStreamMonitor import SimpleStreamMonitor


class MonitorJob:
    def __init__(self, stream_url, check_interval):
        self.stream_url = stream_url
        self.check_interval = check_interval

    def run(self):
        """主函数示例"""
        logger.info("=== 流媒体可播放性监控系统 ===")

        # 使用简化的监控器
        stream_url = self.stream_url
        check_interval = self.check_interval

        monitor = SimpleStreamMonitor(
            stream_url=stream_url,  # 直播流地址
            check_interval=check_interval  # x秒检查一次
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

import threading

from config.log4py import logger
from monitor.StreamMonitor import StreamMonitor


class MonitorJob:
    """
    监控任务 - 多线程版本
    """

    def __init__(self, stream_id, stream_url, check_interval):
        self.stream_id = stream_id
        self.stream_url = stream_url
        self.check_interval = check_interval
        self.monitor = None
        self.running = False
        self.thread = None

    def start(self):
        """
        启动监控任务
        """
        if self.running:
            logger.warning(f"监控任务 {self.stream_id} 已经在运行")
            return

        self.thread = threading.Thread(target=self._run_monitor, daemon=True)
        self.thread.start()
        self.running = True
        logger.info(f"启动监控任务: {self.stream_id}")

    def stop(self):
        """
        停止监控任务
        """
        self.running = False
        if self.monitor:
            self.monitor.stop()
        logger.info(f"停止监控任务: {self.stream_id}")

    def _run_monitor(self):
        """
        监控任务的主循环
        """
        logger.info(f"=== 开始监控流: {self.stream_id} ===")

        # 这里需要根据实际的 StreamMonitor 类进行调整
        self.monitor = StreamMonitor(
            stream_id=self.stream_id,
            stream_url=self.stream_url,
            check_interval=self.check_interval
        )

        try:
            # 启动监控
            self.running = self.monitor.start_monitoring()
        except Exception as e:
            self.running = False
            logger.error(f"监控任务 {self.stream_id} 发生错误: {e}")
        finally:
            if self.monitor:
                self.monitor.stop()
            logger.info(f"监控任务 {self.stream_id} 已结束")

    def is_running(self):
        """
        检查任务是否在运行
        """
        return self.running and self.thread and self.thread.is_alive()

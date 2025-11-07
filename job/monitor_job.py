import threading
import time

from config.log4py import logger
from monitor.StreamMonitor import StreamMonitor


class MonitorJob:
    """
    监控任务 - 多线程版本
    """

    def __init__(self, stream_id, stream_name, stream_url, check_interval):
        self.stream_id = stream_id
        self.stream_name = stream_name
        self.stream_url = stream_url
        self.check_interval = check_interval
        self.monitor = None
        self.running = False
        self.thread = None
        self._stop_event = threading.Event()

    def start(self):
        """
        启动监控任务
        """
        if self.running:
            logger.warning(f"监控任务 {self.stream_id} {self.stream_name} {self.stream_url} 已经在运行")
            return

        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run_monitor, daemon=True)
        self.thread.start()
        self.running = True
        logger.info(f"启动监控任务: {self.stream_id}")

    def stop(self):
        """
        停止监控任务
        """
        self.running = False
        self._stop_event.set()

        if self.monitor:
            self.monitor.stop()

        if self.thread and self.thread.is_alive():
            try:
                self.thread.join(timeout=5.0)  # 等待最多5秒
                if self.thread.is_alive():
                    logger.error(f"强制终止线程: {self.stream_id}")
                    # 线程仍在运行，记录但继续执行
            except Exception as e:
                logger.error(f"停止线程时发生错误: {e}")

        logger.info(f"停止监控任务: {self.stream_id} {self.stream_name} {self.stream_url}")

    def _run_monitor(self):
        """
        监控任务的主循环
        """
        logger.info(f"=== 开始监控流: {self.stream_id} {self.stream_name} {self.stream_url} ===")

        # 这里需要根据实际的 StreamMonitor 类进行调整
        self.monitor = StreamMonitor(
            stream_id=self.stream_id,
            stream_name=self.stream_name,
            stream_url=self.stream_url,
            check_interval=self.check_interval
        )

        try:
            self.monitor = StreamMonitor(
                stream_id=self.stream_id,
                stream_name=self.stream_name,
                stream_url=self.stream_url,
                check_interval=self.check_interval
            )

            while not self._stop_event.is_set():
                if not self.monitor.start_monitoring():
                    break
                time.sleep(0.1)  # 防止CPU过度使用

        except Exception as e:
            logger.error(f"监控任务 {self.stream_id} {self.stream_name} {self.stream_url} 发生错误: {e}")
        finally:
            self.running = False
            if self.monitor:
                try:
                    self.monitor.stop()
                except Exception as e:
                    logger.error(f"停止监控器时发生错误: {e}")
            logger.info(f"监控任务 {self.stream_id} {self.stream_name} {self.stream_url} 已结束")

    def is_running(self):
        """
        检查任务是否在运行
        """
        return self.running and self.thread and self.thread.is_alive()

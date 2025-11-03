from typing import Dict

from config.log4py import logger
from job.monitor_job import MonitorJob


class MonitorManager:
    """
    监控任务管理器
    """

    def __init__(self):
        self.monitor_jobs: Dict[str, MonitorJob] = {}
        self.running = False

    def add_stream(self, stream_id: str, stream_url: str, check_interval: int = 30):
        """
        添加要监控的流
        """
        if stream_id in self.monitor_jobs:
            logger.warning(f"流 {stream_id} 已经在监控列表中")
            return False

        job = MonitorJob(stream_id, stream_url, check_interval)
        self.monitor_jobs[stream_id] = job
        logger.info(f"添加流到监控列表: {stream_id}")
        return True

    def start_all(self):
        """
        启动所有监控任务
        """
        self.running = True
        for stream_id, job in self.monitor_jobs.items():
            job.start()
        logger.info(f"启动了 {len(self.monitor_jobs)} 个监控任务")

    def stop_all(self):
        """
        停止所有监控任务
        """
        self.running = False
        for stream_id, job in self.monitor_jobs.items():
            job.stop()
        logger.info("所有监控任务已停止")

    def start_stream(self, stream_id: str):
        """
        启动指定流的监控
        """
        if stream_id in self.monitor_jobs:
            self.monitor_jobs[stream_id].start()
            return True
        return False

    def stop_stream(self, stream_id: str):
        """
        停止指定流的监控
        """
        if stream_id in self.monitor_jobs:
            self.monitor_jobs[stream_id].stop()
            return True
        return False

    def get_status(self):
        """
        获取所有监控任务状态
        """
        status = {}
        for stream_id, job in self.monitor_jobs.items():
            status[stream_id] = {
                'running': job.is_running(),
                'stream_url': job.stream_url
            }
        return status

from config.ConfigLoader import get_config
from config.log4py import logger
from job.monitor_job import MonitorJob

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

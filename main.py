import time

from config.ConfigLoader import get_config
from config.log4py import logger
from job.monitor_manager import MonitorManager


def main():
    """
    主函数 - 启动多线程监控系统
    """
    logger.info("启动 Stream Monitor 服务器...")
    config = get_config()
    streams = config.get("streams")

    # 创建监控管理器
    manager = MonitorManager()

    # 添加所有流到监控列表
    for stream in streams:
        stream_id = stream["id"]
        stream_url = stream["url"]
        check_interval = config.get("monitoring.check_interval")

        logger.info("视频 id: %s , url: %s", stream_id, stream_url)
        manager.add_stream(stream_id, stream_url, check_interval)

    # 启动所有监控任务
    manager.start_all()

    try:
        logger.info("监控系统已启动，按 Ctrl+C 停止所有监控...")
        logger.info("当前监控任务状态:")

        # 主循环：定期显示状态并保持运行
        while manager.running:
            logger.info("定期显示状态并保持运行 开始监听")
            # 每30秒显示一次状态
            time.sleep(30)
            logger.info("已等待 30s")

            status = manager.get_status()
            running_count = sum(1 for s in status.values() if s['running'])
            logger.info(f"状态报告 - 运行中: {running_count}/{len(status)}")

            # 检查是否有任务异常停止
            for stream_id, info in status.items():
                if not info['running'] and manager.running:
                    logger.warning(f"流 {stream_id} 异常停止，尝试重新启动...")
                    manager.start_stream(stream_id)

    except KeyboardInterrupt:
        logger.info("\n收到停止信号...")
    finally:
        # 停止所有监控任务
        manager.stop_all()
        logger.info("监控系统已关闭")


if __name__ == '__main__':
    main()

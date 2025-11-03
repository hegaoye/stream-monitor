import threading
import time
from collections import deque
from datetime import datetime

import av

from config.log4py import logger


class SimpleStreamMonitor:
    def __init__(self, stream_id, stream_url, check_interval=5):
        self.stream_id = stream_id
        self.stream_url = stream_url
        self.check_interval = check_interval
        self.container = None
        self.running = False

        # 监控状态
        self.stats = {
            'total_packets': 0,
            'video_packets': 0,
            'audio_packets': 0,
            'keyframes': 0,
            'start_time': None,
            'last_packet_time': None,
            'last_keyframe_time': None
        }

        # 质量评估
        self.quality_history = deque(maxlen=100)

    def connect(self):
        """连接到流"""
        try:
            options = {
                'rtmp_live': 'live',
                'rtmp_buffer': '1000',
                'timeout': '10000000',
            }

            self.container = av.open(self.stream_url, options=options)
            self.stats['start_time'] = datetime.now()
            logger.info(f"✅ 成功连接到: {self.stream_id}")
            return True
        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            return False

    def assess_stream_health(self):
        """评估流健康状况"""
        current_time = time.time()
        health = {
            'playable': True,
            'quality': 'good',
            'issues': [],
            'estimated_delay': None
        }

        # 检查数据接收
        if (self.stats['last_packet_time'] and
                current_time - self.stats['last_packet_time'] > 10):
            health['playable'] = False
            health['issues'].append("10秒内无数据包")

        # 检查关键帧
        if (self.stats['last_keyframe_time'] and
                current_time - self.stats['last_keyframe_time'] > 30):
            health['issues'].append("30秒内无关键帧")
            health['quality'] = 'poor'

        # 估算延迟（基于最后包时间）
        if self.stats['last_packet_time']:
            health['estimated_delay'] = int((current_time - self.stats['last_packet_time']) * 1000)

        return health

    def start_monitoring(self):
        """开始监控"""
        if not self.connect():
            return False

        self.running = True
        logger.info("🚀 开始流监控: %s", self.stream_id)

        # 启动健康检查线程
        health_thread = threading.Thread(target=self.health_check_loop)
        health_thread.daemon = True
        health_thread.start()

        try:
            # 主监控循环
            for packet in self.container.demux():
                if not self.running:
                    break

                self.stats['total_packets'] += 1
                self.stats['last_packet_time'] = time.time()

                # 统计包类型
                if packet.stream and packet.stream.type == 'video':
                    self.stats['video_packets'] += 1
                    if packet.is_keyframe:
                        self.stats['keyframes'] += 1
                        self.stats['last_keyframe_time'] = time.time()
                elif packet.stream and packet.stream.type == 'audio':
                    self.stats['audio_packets'] += 1

        except Exception as e:
            logger.error(f"监控错误: {e}")
        finally:
            self.stop()

    def health_check_loop(self):
        """
        健康检查循环
        """
        check_count = 0

        while self.running:
            try:
                health = self.assess_stream_health()
                check_count += 1

                # 打印状态
                self.print_status(health, check_count)

                # 记录质量历史
                self.quality_history.append(health['quality'])

            except Exception as e:
                logger.error(f"健康检查错误: {e}")

            time.sleep(self.check_interval)

    def print_status(self, health, check_count):
        """
        视频监控信息
        """
        timestamp = datetime.now().strftime('%D %H:%M:%S')
        status_icon = "✅" if health['playable'] else "❌"
        delay_display = f"{health['estimated_delay']}" if health['estimated_delay'] else "N/A"

        monitor_record = {
            "streamId": self.stream_id,
            "streamUrl": self.stream_url,
            "playable": health['playable'],
            "quality": health['quality'],
            "delay": delay_display,
            "videoPackets": self.stats['video_packets'],
            "keyframes": self.stats['keyframes'],
            "count": check_count,
            "timestamp": timestamp
        }

        logger.info(monitor_record)
        logger.info(f"[{timestamp}] 检查#{check_count:03d} {status_icon} "
                    f"可播放: {health['playable']} | "
                    f"质量: {health['quality']:6} | "
                    f"延迟ms: {delay_display:>6} | "
                    f"视频包: {self.stats['video_packets']} | "
                    f"关键帧: {self.stats['keyframes']}")

        # 显示问题
        for issue in health['issues']:
            logger.info(f"       ⚠️  {issue}")

    def stop(self):
        """停止监控"""
        self.running = False
        if self.container:
            self.container.close()

        # 打印总结
        total_time = (datetime.now() - self.stats['start_time']).seconds if self.stats['start_time'] else 0
        logger.info(f"\n📊 监控总结")
        logger.info(f"   运行时间: {total_time}秒")
        logger.info(f"   总包数: {self.stats['total_packets']}")
        logger.info(f"   视频包: {self.stats['video_packets']}")
        logger.info(f"   音频包: {self.stats['audio_packets']}")
        logger.info(f"   关键帧: {self.stats['keyframes']}")
        logger.info("🛑 流监控已停止")

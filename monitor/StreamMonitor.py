import logging
import threading
import time
from collections import deque
from datetime import datetime

import av
import numpy as np

from config.WebhookSender import WebhookSender
from config.log4py import logger


class StreamMonitor:
    """
    视频流监控类 - 增强版（支持码率、分辨率等深度分析）
    """

    def __init__(self, stream_id, stream_name, stream_url, check_interval=5):
        self.stream_id = stream_id
        self.stream_name = stream_name
        self.stream_url = stream_url
        self.check_interval = check_interval
        self.container = None
        self.running = False
        self.webhook_sender = WebhookSender()

        # 基础监控状态
        self.stats = {
            'total_packets': 0,
            'video_packets': 0,
            'audio_packets': 0,
            'keyframes': 0,
            'start_time': None,
            'last_packet_time': None,
            'last_keyframe_time': None
        }

        # 深度分析状态
        self.deep_stats = {
            'current_bitrate': 0,  # 当前码率 (bps)
            'average_bitrate': 0,  # 平均码率
            'bitrate_history': deque(maxlen=60),  # 码率历史 (最近60秒)
            'resolution': (0, 0),  # 分辨率 (宽, 高)
            'frame_rate': 0,  # 帧率
            'codec': 'unknown',  # 视频编码
            'profile': 'unknown',  # 编码配置
            'bit_depth': 8,  # 位深
            'color_space': 'unknown',  # 色彩空间
            'gop_size': 0,  # GOP大小
            'last_gop_start': None,  # 上一个GOP开始时间
            'buffer_health': 100,  # 缓冲区健康度 (%)
            'packet_loss': 0,  # 丢包率
            'jitter': 0,  # 抖动
            'last_frame_analysis': None  # 最后帧分析时间
        }

        # 质量评估历史
        self.quality_history = deque(maxlen=100)

        # 帧分析相关
        self.frame_buffer = deque(maxlen=30)  # 保存最近30帧的时间戳用于帧率计算
        self.byte_count = 0  # 字节计数器（用于码率计算）
        self.last_byte_count_time = time.time()

    def connect(self):
        """
        连接到流
        """
        try:
            # options = {
            #     'rtmp_live': 'live',
            #     'rtmp_buffer': '1000',
            #     'timeout': '10000000',
            #     'analyzeduration': '1000000',
            #     'probesize': '500000'
            # }

            logger.info(f"=== 尝试连接: {self.stream_id} 流 {self.stream_name} {self.stream_url} ===")
            self.container = av.open(self.stream_url)
            # self.container = av.open(self.stream_url, options=options)
            self.stats['start_time'] = datetime.now()

            # 尝试获取流信息
            self._analyze_stream_info()

            logger.info(f"✅ 成功连接到: {self.stream_id} {self.stream_name} {self.stream_url}")
            return True
        except av.AVError as e:
            logger.error(f"❌AVError 连接失败: {self.stream_id} {self.stream_name} {self.stream_url}")
            logger.error(f"❌AVError 连接失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 连接失败: {self.stream_id} {self.stream_name} {self.stream_url}")
            logger.error(f"❌ 连接失败: {e}")
            return False

    def _analyze_stream_info(self):
        """
        分析流信息（分辨率、编码等）
        """
        try:
            logging.info(f"=== 尝试获取{self.stream_id} {self.stream_name} {self.stream_url} 流信息 ===")
            video_stream = None
            for stream in self.container.streams:
                if stream.type == 'video':
                    video_stream = stream
                    break

            if video_stream:
                # 获取基础流信息
                codec_name = video_stream.codec_context.name if video_stream.codec_context else 'unknown'
                profile = getattr(video_stream.codec_context, 'profile', 'unknown')

                self.deep_stats.update({
                    'codec': codec_name,
                    'profile': profile,
                    'resolution': (video_stream.width, video_stream.height) if video_stream.width else (0, 0)
                })

                logger.info(f"📺 流信息 - 编码: {codec_name}, 分辨率: {video_stream.width}x{video_stream.height}")

        except Exception as e:
            logger.warning(f"无法获取流信息: {self.stream_id} {self.stream_name} {self.stream_url}")
            logger.warning(f"无法获取流信息: {e}")

    def _calculate_bitrate(self):
        """
        计算实时码率
        """
        current_time = time.time()
        time_diff = current_time - self.last_byte_count_time

        if time_diff > 0:
            # 计算当前码率 (bps)
            current_bitrate = (self.byte_count * 8) / time_diff
            self.deep_stats['current_bitrate'] = current_bitrate
            self.deep_stats['bitrate_history'].append(current_bitrate)

            # 计算平均码率
            if self.deep_stats['bitrate_history']:
                self.deep_stats['average_bitrate'] = sum(self.deep_stats['bitrate_history']) / len(
                    self.deep_stats['bitrate_history'])

            # 重置计数器
            self.byte_count = 0
            self.last_byte_count_time = current_time

    def _analyze_frame_quality(self, frame):
        """
        分析帧质量
        """
        try:
            # 转换为numpy数组进行分析
            np_frame = frame.to_ndarray(format='bgr24')

            # 计算亮度
            brightness = np.mean(np_frame)

            # 计算对比度 (标准差)
            contrast = np.std(np_frame)

            return {
                'brightness': brightness,
                'contrast': contrast,
                'resolution': (frame.width, frame.height)
            }
        except Exception as e:
            logger.error(f"帧质量分析失败: {self.stream_id} {self.stream_name} {self.stream_url}")
            logger.error(f"帧质量分析失败: {e}")
            return None

    def _calculate_frame_rate(self):
        """
        计算实时帧率
        """
        current_time = time.time()
        self.frame_buffer.append(current_time)

        if len(self.frame_buffer) > 1:
            time_diff = self.frame_buffer[-1] - self.frame_buffer[0]
            if time_diff > 0:
                self.deep_stats['frame_rate'] = (len(self.frame_buffer) - 1) / time_diff

    def _analyze_video_packet(self, packet):
        """
        深度分析视频包
        """
        if packet.stream and packet.stream.type == 'video':
            # 统计字节数用于码率计算
            self.byte_count += packet.size

            # 记录帧时间用于帧率计算
            self._calculate_frame_rate()

            # 分析关键帧/GOP
            if packet.is_keyframe:
                self.stats['keyframes'] += 1
                self.stats['last_keyframe_time'] = time.time()

                # 计算GOP大小
                if self.deep_stats['last_gop_start']:
                    gop_duration = time.time() - self.deep_stats['last_gop_start']
                    gop_size = int(gop_duration * self.deep_stats.get('frame_rate', 25))
                    self.deep_stats['gop_size'] = gop_size

                self.deep_stats['last_gop_start'] = time.time()

            # 定期进行帧质量分析（每10帧或每5秒）
            current_time = time.time()
            if (self.deep_stats['last_frame_analysis'] is None or
                    current_time - self.deep_stats['last_frame_analysis'] > 5):

                try:
                    # 尝试解码一帧进行分析
                    for frame in packet.decode():
                        frame_analysis = self._analyze_frame_quality(frame)
                        if frame_analysis:
                            self.deep_stats.update(frame_analysis)
                        break  # 只分析第一帧

                    self.deep_stats['last_frame_analysis'] = current_time
                except Exception as e:
                    logger.error(f"帧解码失败: {self.stream_id} {self.stream_name} {self.stream_url}")
                    logger.error(f"帧解码失败: {e}")

    def assess_stream_health(self):
        """
        评估流健康状况 - 增强版
        """
        current_time = time.time()
        health = {
            'playable': True,
            'quality': 'good',
            'issues': [],
            'estimated_delay': None,
            'bitrate_stability': 'stable',
            'resolution_stability': 'stable'
        }

        # 基础健康检查
        if (self.stats['last_packet_time'] and
                current_time - self.stats['last_packet_time'] > 10):
            health['playable'] = False
            health['issues'].append("10秒内无数据包")

        if (self.stats['last_keyframe_time'] and
                current_time - self.stats['last_keyframe_time'] > 30):
            health['issues'].append("30秒内无关键帧")
            health['quality'] = 'poor'

        # 码率稳定性检查
        if len(self.deep_stats['bitrate_history']) > 10:
            recent_bitrates = list(self.deep_stats['bitrate_history'])[-10:]
            bitrate_variance = np.std(recent_bitrates) / np.mean(recent_bitrates) if np.mean(recent_bitrates) > 0 else 0

            if bitrate_variance > 0.5:
                health['bitrate_stability'] = 'unstable'
                health['issues'].append("码率波动较大")
                health['quality'] = 'poor'
            elif bitrate_variance > 0.2:
                health['bitrate_stability'] = 'moderate'
                health['quality'] = 'fair'

        # 帧率检查
        if self.deep_stats['frame_rate'] > 0:
            if self.deep_stats['frame_rate'] < 15:
                health['issues'].append(f"帧率过低: {self.deep_stats['frame_rate']:.1f}fps")
                health['quality'] = 'poor'
            elif self.deep_stats['frame_rate'] < 24:
                health['issues'].append(f"帧率较低: {self.deep_stats['frame_rate']:.1f}fps")
                if health['quality'] == 'good':
                    health['quality'] = 'fair'

        # GOP大小检查
        if self.deep_stats['gop_size'] > 0:
            if self.deep_stats['gop_size'] > 300:  # GOP太大可能导致seek困难
                health['issues'].append(f"GOP过大: {self.deep_stats['gop_size']}帧")
            elif self.deep_stats['gop_size'] < 10:  # GOP太小影响编码效率
                health['issues'].append(f"GOP过小: {self.deep_stats['gop_size']}帧")

        # 估算延迟
        if self.stats['last_packet_time']:
            health['estimated_delay'] = int((current_time - self.stats['last_packet_time']) * 1000)

        return health

    def start_monitoring(self):
        """
        开始监控
        """
        if not self.connect():
            self.running = False
            return False

        self.running = True
        logger.info(f"🚀 开始流监控: {self.stream_id} {self.stream_name} {self.stream_url}")

        # 启动健康检查线程
        health_thread = threading.Thread(target=self.health_check_loop)
        health_thread.daemon = True
        health_thread.start()

        # 启动码率计算线程
        bitrate_thread = threading.Thread(target=self.bitrate_calculation_loop)
        bitrate_thread.daemon = True
        bitrate_thread.start()

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
                    self._analyze_video_packet(packet)
                elif packet.stream and packet.stream.type == 'audio':
                    self.stats['audio_packets'] += 1
                    self.byte_count += packet.size  # 音频包也计入码率

        except Exception as e:
            logger.error(f"监控错误: {self.stream_id} {self.stream_name} {self.stream_url}")
            logger.error(f"监控错误: {e}")
        finally:
            self.stop()

    def bitrate_calculation_loop(self):
        """
        码率计算循环
        """
        while self.running:
            try:
                self._calculate_bitrate()
            except Exception as e:
                logger.error(f"码率计算错误: {self.stream_id} {self.stream_name} {self.stream_url}")
                logger.error(f"码率计算错误: {e}")

            time.sleep(1)  # 每秒计算一次

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
                logger.error(f"健康检查错误: {self.stream_id} {self.stream_name} {self.stream_url}")
                logger.error(f"健康检查错误: {e}")

            time.sleep(self.check_interval)

    def print_status(self, health, check_count):
        """
        打印增强版监控信息
        """
        timestamp = datetime.now().strftime('%m/%d/%y %H:%M:%S')
        delay_display = f"{health['estimated_delay']}" if health['estimated_delay'] else "N/A"

        # 格式化码率显示
        current_bitrate_kbps = self.deep_stats['current_bitrate'] / 1000
        avg_bitrate_kbps = self.deep_stats['average_bitrate'] / 1000 if self.deep_stats['average_bitrate'] > 0 else 0

        # 分辨率显示
        width, height = self.deep_stats['resolution']
        resolution_display = f"{width}x{height}" if width > 0 and height > 0 else "N/A"

        monitor_data = {
            "streamId": self.stream_id,
            "streamName": self.stream_name,
            "streamUrl": self.stream_url,
            "playable": health['playable'],
            "quality": health['quality'],
            "delay": delay_display,
            "videoPackets": self.stats['video_packets'],
            "keyframes": self.stats['keyframes'],
            "count": check_count,
            "timestamp": timestamp,
            # 深度分析数据
            "bitrate": round(current_bitrate_kbps, 1),
            "avgBitrate": round(avg_bitrate_kbps, 1),
            "frameRate": round(self.deep_stats['frame_rate'], 1),
            "resolution": resolution_display,
            "codec": self.deep_stats['codec'],
            "gopSize": self.deep_stats['gop_size'],
            "bitrateStability": health['bitrate_stability']
        }

        logger.info(monitor_data)

        # 增强的状态显示
        logger.info(f"[{timestamp}] 检查#{check_count:03d} {self.stream_id} {self.stream_name} ({self.stream_url})")
        logger.info(f"   可播放: {health['playable']} | 质量: {health['quality']:6} | 延迟: {delay_display:>6}ms")
        logger.info(f"   视频包: {self.stats['video_packets']} | 关键帧: {self.stats['keyframes']}")
        logger.info(
            f"   码率: {current_bitrate_kbps:.1f}kbps (平均: {avg_bitrate_kbps:.1f}kbps) | 稳定性: {health['bitrate_stability']}")
        logger.info(f"   帧率: {self.deep_stats['frame_rate']:.1f}fps | 分辨率: {resolution_display}")
        logger.info(f"   编码: {self.deep_stats['codec']} | GOP: {self.deep_stats['gop_size']}帧")

        # 发送 Webhook 警报
        if not monitor_data['playable']:  # 流不可播放时发送
            message = f"stream {self.stream_id} can not be played."
            alert_level = "error"
        elif monitor_data['quality'] == 'poor':  # 质量差时发送
            message = f"stream {self.stream_id} quality is poor."
            alert_level = "warning"
        elif monitor_data['bitrateStability'] == 'unstable':  # 码率不稳定
            message = f"stream {self.stream_id} bitrate is unstable."
            alert_level = "warning"
        else:
            message = f"stream {self.stream_id} running OK."
            alert_level = "info"

        self.webhook_sender.send_alert({
            **monitor_data,
            "message": message,
            "alertLevel": alert_level
        })

        # 显示问题
        for issue in health['issues']:
            logger.info(f" {issue}")

    def stop(self):
        """
        停止监控
        """
        self.running = False
        if self.container:
            self.container.close()

        # 打印详细总结
        total_time = (datetime.now() - self.stats['start_time']).seconds if self.stats['start_time'] else 0

        logger.info(f"\n📊 深度监控总结 - {self.stream_id} {self.stream_name} ({self.stream_url})")
        logger.info(f"   运行时间: {total_time}秒")
        logger.info(f"   总包数: {self.stats['total_packets']}")
        logger.info(f"   视频包: {self.stats['video_packets']} | 音频包: {self.stats['audio_packets']}")
        logger.info(f"   关键帧: {self.stats['keyframes']}")
        logger.info(f"   平均码率: {self.deep_stats['average_bitrate'] / 1000:.1f} kbps")
        logger.info(f"   平均帧率: {self.deep_stats['frame_rate']:.1f} fps")
        logger.info(f"   分辨率: {self.deep_stats['resolution'][0]}x{self.deep_stats['resolution'][1]}")
        logger.info(f"   编码: {self.deep_stats['codec']} ({self.deep_stats['profile']})")
        logger.info("🛑 流监控已停止")

import json
from datetime import datetime
from typing import Dict

import requests
import yaml

from config.log4py import logger


class WebhookSender:
    """
    Webhook 发送器
    """

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.enabled = self.config.get('webhook', {}).get('enabled', False)
        self.url = self.config.get('webhook', {}).get('url', '')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'StreamMonitor/1.0'
        })

    def _load_config(self, config_path: str) -> Dict:
        """
        加载配置文件
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"配置文件 {config_path} 未找到，使用默认配置")
            return {}
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}

    def send_alert(self, stream_data: Dict) -> bool:
        """
        发送警报到 Webhook
        """
        if not self.enabled or not self.url:
            return False

        try:
            # 准备报警数据
            alert_data = {
                "type": "stream_monitor",
                "timestamp": datetime.now().isoformat(),
                "data": stream_data
            }

            data = json.dumps(alert_data, ensure_ascii=False)
            logger.info("统计数据：\n %s", data)
            response = self.session.post(
                self.url,
                data=data,
                timeout=10
            )

            if response.status_code in [200, 201, 204]:
                logger.debug(f"Webhook 发送成功: {stream_data.get('streamId')}")
                return True
            else:
                logger.warning(f"Webhook 发送失败: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Webhook 请求失败: {e}")
            return False
        except Exception as e:
            logger.error(f"发送 Webhook 时发生错误: {e}")
            return False

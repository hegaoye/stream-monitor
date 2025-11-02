import logging
import os
from typing import Dict, Any, Optional

import yaml

from settings import SYS_CONF


class ConfigLoader:
    """
    读取YAML配置文件
    """

    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.logger = logging.getLogger(__name__)
        self._config = {}

    def load_config(self, custom_config: Optional[str] = None) -> Dict[str, Any]:
        """
        加载配置文件
        :param custom_config: 自定义配置文件名
        :return: 合并后的配置字典
        """
        try:
            # 加载默认配置
            default_config = self._load_yaml_file(self.config_dir)
            if not default_config:
                raise ValueError("无法加载默认配置文件")

            # 加载自定义配置（如果存在）
            custom_config_data = {}
            if custom_config:
                custom_config_data = self._load_yaml_file(custom_config)
            elif os.path.exists(os.path.join(self.config_dir, "custom.yml")):
                custom_config_data = self._load_yaml_file("custom.yml")

            # 合并配置
            self._config = self._deep_merge(default_config, custom_config_data)

            self.logger.info("配置文件加载成功")
            return self._config

        except Exception as e:
            self.logger.error(f"配置文件加载失败: {e}")
            raise

    def _load_yaml_file(self, filename: str) -> Dict[str, Any]:
        """加载 YAML 文件"""
        filepath = os.path.join(self.config_dir, filename)
        if not os.path.exists(filepath):
            self.logger.warning(f"配置文件不存在: {filepath}")
            return {}

        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file) or {}
        except yaml.YAMLError as e:
            self.logger.error(f"YAML 解析错误 ({filename}): {e}")
            return {}
        except Exception as e:
            self.logger.error(f"文件读取错误 ({filename}): {e}")
            return {}

    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """深度合并两个字典"""
        result = base.copy()

        for key, value in update.items():
            if (key in result and
                    isinstance(result[key], dict) and
                    isinstance(value, dict)):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点分隔键"""
        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_stream_config(self, stream_name: str) -> Optional[Dict[str, Any]]:
        """获取指定流的配置"""
        streams = self.get('streams', {})
        return streams.get(stream_name)

    def get_enabled_streams(self) -> Dict[str, Dict]:
        """获取所有启用的流配置"""
        streams = self.get('streams', {})
        return {name: config for name, config in streams.items()
                if config.get('enabled', False)}

    def validate_config(self) -> bool:
        """验证配置完整性"""
        required_sections = ['monitoring', 'streams']

        for section in required_sections:
            if not self.get(section):
                self.logger.error(f"缺少必要配置段: {section}")
                return False

        # 检查是否有启用的流
        enabled_streams = self.get_enabled_streams()
        if not enabled_streams:
            self.logger.error("没有启用的流配置")
            return False

        return True


# 配置单例
_config_instance: Optional[ConfigLoader] = None


def get_config(config_dir: str = "config", custom_config: Optional[str] = None) -> ConfigLoader:
    """获取配置实例（单例模式）"""
    global _config_instance

    if _config_instance is None:
        _config_instance = ConfigLoader(SYS_CONF)
        _config_instance.load_config(custom_config)

    return _config_instance

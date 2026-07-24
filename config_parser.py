"""
配置文件解析器
负责读取和解析YAML格式的配置文件，提取API密钥和端点信息
"""

import yaml
import os
from typing import Dict, Any, Optional


class ConfigParser:
    """配置文件解析器类"""
    
    def __init__(self, config_path: str):
        """
        初始化配置解析器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = {}
        
    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            解析后的配置字典
            
        Raises:
            FileNotFoundError: 配置文件不存在
            yaml.YAMLError: 配置文件格式错误
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
                
            if not isinstance(self.config, dict):
                raise ValueError("配置文件格式错误：应为字典格式")
                
            return self.config
            
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"配置文件解析错误: {e}")
    
    def get_api_key(self, service_name: str) -> Optional[str]:
        """
        获取指定服务的API密钥
        
        Args:
            service_name: 服务名称（如 'ZHIPU', 'DEEPSEEK' 等）
            
        Returns:
            API密钥字符串，如果不存在则返回None
        """
        key_name = f"{service_name}_API_KEY"
        return self.config.get(key_name)
    
    def get_openrouter_config(self) -> Dict[str, Any]:
        """
        获取OpenRouter配置
        
        Returns:
            包含API密钥和端点的配置字典
        """
        return {
            'api_key': self.config.get('OPENROUTER_API_KEY'),
            'base_url': 'https://openrouter.ai/api/v1',
            'models': self._get_openrouter_models()
        }
    
    def get_zhipu_config(self) -> Dict[str, Any]:
        """
        获取智谱AI配置
        
        Returns:
            包含API密钥和端点的配置字典
        """
        return {
            'api_key': self.config.get('ZHIPU_API_KEY'),
            'base_url': 'https://open.bigmodel.cn/api/paas/v4',
            'models': ['glm-4.6v-flash', 'glm-4.7-flash']
        }
    
    def get_nvidia_config(self) -> Dict[str, Any]:
        """
        获取NVIDIA NIM配置
        
        Returns:
            包含API密钥和端点的配置字典
        """
        return {
            'api_key': self.config.get('NVIDIA_API_KEY'),
            'base_url': 'https://integrate.api.nvidia.com/v1',
            'models': self._get_nvidia_models()
        }
    
    def get_test_config(self) -> Dict[str, Any]:
        """
        获取测试配置
        
        Returns:
            测试相关配置字典
        """
        return {
            'timeout': self.config.get('REQUEST_TIMEOUT', 30),
            'test_prompt': self.config.get('TEST_PROMPT', '你好，请简单介绍一下你自己'),
            'free_models_only': self.config.get('TEST_FREE_MODELS_ONLY', True),
            'max_retries': self.config.get('MAX_RETRIES', 2)
        }
    
    def _get_openrouter_models(self) -> list:
        """
        获取OpenRouter免费模型列表
        
        Returns:
            模型ID列表
        """
        return [
            'minimax-ai/minimax-m2.5:free',
            'google/gemma-4-26b-a4b-it:free',
            'moonshotai/kimi-k2.6:free',
            'deepseek/deepseek-v4-flash:free',
            'qwen/qwen3-coder:free',
            'qwen/qwen3-next-80b-a3b-instruct:free',
            'meta-llama/llama-4-scout:free'
        ]
    
    def _get_nvidia_models(self) -> list:
        """
        获取NVIDIA NIM模型列表
        
        Returns:
            模型ID列表
        """
        return [
            'zai-org/glm-5',
            'zai-org/glm-5.1',
            'deepseek-ai/deepseek-v4-flash',
            'deepseek-ai/deepseek-v4-pro',
            'moonshotai/kimi-k2.5',
            'moonshotai/kimi-k2.6',
            'minimax-ai/minimax-m2.5',
            'qwen/qwen3-coder-next',
            'meta-llama/llama-4-scout',
            'meta-llama/llama-4-maverick'
        ]
    
    def validate_config(self) -> Dict[str, Any]:
        """
        验证配置完整性
        
        Returns:
            验证结果字典，包含有效配置和警告信息
        """
        warnings = []
        valid_configs = {}
        
        # 检查OpenRouter配置
        openrouter_key = self.get_api_key('OPENROUTER')
        if openrouter_key:
            valid_configs['openrouter'] = self.get_openrouter_config()
        else:
            warnings.append("未配置OPENROUTER_API_KEY，将跳过OpenRouter测试")
        
        # 检查智谱AI配置
        zhipu_key = self.get_api_key('ZHIPU')
        if zhipu_key:
            valid_configs['zhipu'] = self.get_zhipu_config()
        else:
            warnings.append("未配置ZHIPU_API_KEY，将跳过智谱AI测试")
        
        # 检查NVIDIA配置
        nvidia_key = self.get_api_key('NVIDIA')
        if nvidia_key:
            valid_configs['nvidia'] = self.get_nvidia_config()
        else:
            warnings.append("未配置NVIDIA_API_KEY，将跳过NVIDIA NIM测试")
        
        # 检查其他API密钥
        other_keys = ['DEEPSEEK', 'KIMI', 'MIMO', 'QWEN']
        for key in other_keys:
            if not self.get_api_key(key):
                warnings.append(f"未配置{key}_API_KEY，将跳过{key}相关测试")
        
        return {
            'valid_configs': valid_configs,
            'warnings': warnings,
            'test_config': self.get_test_config()
        }


def load_config_from_file(config_path: str) -> Dict[str, Any]:
    """
    从文件加载配置的便捷函数
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        验证后的配置字典
    """
    parser = ConfigParser(config_path)
    parser.load_config()
    return parser.validate_config()
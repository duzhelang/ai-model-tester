"""
AI模型连接测试器
负责测试各种AI模型API的连接状态
"""

import requests
import json
import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class TestStatus(Enum):
    """测试状态枚举"""
    SUCCESS = "成功"
    FAILED = "失败"
    TIMEOUT = "超时"
    ERROR = "错误"


@dataclass
class TestResult:
    """测试结果数据类"""
    model_id: str
    service: str
    status: TestStatus
    response_time: float  # 毫秒
    response_data: Optional[Dict] = None
    error_message: Optional[str] = None
    status_code: Optional[int] = None


class ModelTester:
    """AI模型连接测试器"""
    
    def __init__(self, timeout: int = 30, max_retries: int = 2):
        """
        初始化测试器
        
        Args:
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AI-Model-Tester/1.0'
        })
    
    def test_openrouter_model(self, api_key: str, model_id: str, prompt: str) -> TestResult:
        """
        测试OpenRouter模型
        
        Args:
            api_key: OpenRouter API密钥
            model_id: 模型ID
            prompt: 测试提示词
            
        Returns:
            测试结果
        """
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'HTTP-Referer': 'https://ai-model-tester.local',
            'X-Title': 'AI Model Tester'
        }
        
        payload = {
            "model": model_id,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        return self._make_request(url, headers, payload, model_id, "OpenRouter")
    
    def test_zhipu_model(self, api_key: str, model_id: str, prompt: str) -> TestResult:
        """
        测试智谱AI模型
        
        Args:
            api_key: 智谱AI API密钥
            model_id: 模型ID
            prompt: 测试提示词
            
        Returns:
            测试结果
        """
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": model_id,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        return self._make_request(url, headers, payload, model_id, "智谱AI")
    
    def test_nvidia_model(self, api_key: str, model_id: str, prompt: str) -> TestResult:
        """
        测试NVIDIA NIM模型
        
        Args:
            api_key: NVIDIA API密钥
            model_id: 模型ID
            prompt: 测试提示词
            
        Returns:
            测试结果
        """
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": model_id,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        return self._make_request(url, headers, payload, model_id, "NVIDIA NIM")
    
    def _make_request(self, url: str, headers: Dict, payload: Dict, 
                     model_id: str, service: str) -> TestResult:
        """
        发送HTTP请求并处理响应
        
        Args:
            url: 请求URL
            headers: 请求头
            payload: 请求体
            model_id: 模型ID
            service: 服务名称
            
        Returns:
            测试结果
        """
        for attempt in range(self.max_retries + 1):
            start_time = time.time()
            
            try:
                response = self.session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                response_time = (time.time() - start_time) * 1000  # 转换为毫秒
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        return TestResult(
                            model_id=model_id,
                            service=service,
                            status=TestStatus.SUCCESS,
                            response_time=response_time,
                            response_data=response_data,
                            status_code=response.status_code
                        )
                    except json.JSONDecodeError:
                        return TestResult(
                            model_id=model_id,
                            service=service,
                            status=TestStatus.ERROR,
                            response_time=response_time,
                            error_message="响应JSON解析失败",
                            status_code=response.status_code
                        )
                else:
                    error_msg = f"HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        if 'error' in error_data:
                            error_msg = error_data['error'].get('message', error_msg)
                    except:
                        pass
                    
                    return TestResult(
                        model_id=model_id,
                        service=service,
                        status=TestStatus.FAILED,
                        response_time=response_time,
                        error_message=error_msg,
                        status_code=response.status_code
                    )
                    
            except requests.exceptions.Timeout:
                response_time = (time.time() - start_time) * 1000
                if attempt == self.max_retries:
                    return TestResult(
                        model_id=model_id,
                        service=service,
                        status=TestStatus.TIMEOUT,
                        response_time=response_time,
                        error_message=f"请求超时 ({self.timeout}秒)"
                    )
                time.sleep(1)  # 重试前等待1秒
                
            except requests.exceptions.RequestException as e:
                response_time = (time.time() - start_time) * 1000
                return TestResult(
                    model_id=model_id,
                    service=service,
                    status=TestStatus.ERROR,
                    response_time=response_time,
                    error_message=str(e)
                )
        
        # 不应该到达这里，但为了安全起见
        return TestResult(
            model_id=model_id,
            service=service,
            status=TestStatus.ERROR,
            response_time=0,
            error_message="未知错误"
        )
    
    def test_model(self, service: str, api_key: str, model_id: str, prompt: str) -> TestResult:
        """
        测试指定模型的通用接口
        
        Args:
            service: 服务名称
            api_key: API密钥
            model_id: 模型ID
            prompt: 测试提示词
            
        Returns:
            测试结果
        """
        # 将服务名称标准化为小写，便于匹配
        service_lower = service.lower()
        
        if service_lower == "openrouter":
            return self.test_openrouter_model(api_key, model_id, prompt)
        elif service_lower == "zhipu":
            return self.test_zhipu_model(api_key, model_id, prompt)
        elif service_lower == "nvidia":
            return self.test_nvidia_model(api_key, model_id, prompt)
        else:
            return TestResult(
                model_id=model_id,
                service=service,
                status=TestStatus.ERROR,
                response_time=0,
                error_message=f"不支持的服务: {service}"
            )
    
    def batch_test(self, test_configs: Dict[str, Any], test_prompt: str) -> list:
        """
        批量测试多个模型
        
        Args:
            test_configs: 测试配置字典
            test_prompt: 测试提示词
            
        Returns:
            测试结果列表
        """
        results = []
        
        for service_name, config in test_configs.items():
            api_key = config.get('api_key')
            models = config.get('models', [])
            
            if not api_key:
                print(f"跳过 {service_name}: 未提供API密钥")
                continue
            
            print(f"\n测试 {service_name} 服务...")
            
            for model_id in models:
                print(f"  测试模型: {model_id}")
                result = self.test_model(service_name, api_key, model_id, test_prompt)
                results.append(result)
                
                # 打印简要结果
                status_icon = "✓" if result.status == TestStatus.SUCCESS else "✗"
                print(f"    {status_icon} {result.status.value} - {result.response_time:.0f}ms")
                
                if result.error_message:
                    print(f"      错误: {result.error_message}")
        
        return results
    
    def close(self):
        """关闭会话"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
"""
测试报告生成器
负责生成格式化的测试结果报告
"""

from typing import List, Dict, Any
from datetime import datetime
from model_tester import TestResult, TestStatus
import json


class ReportGenerator:
    """测试报告生成器"""
    
    def __init__(self):
        """初始化报告生成器"""
        self.results = []
        self.start_time = None
        self.end_time = None
    
    def set_results(self, results: List[TestResult]):
        """
        设置测试结果
        
        Args:
            results: 测试结果列表
        """
        self.results = results
    
    def set_timing(self, start_time: datetime, end_time: datetime):
        """
        设置测试时间
        
        Args:
            start_time: 测试开始时间
            end_time: 测试结束时间
        """
        self.start_time = start_time
        self.end_time = end_time
    
    def generate_summary(self) -> Dict[str, Any]:
        """
        生成测试摘要
        
        Returns:
            测试摘要字典
        """
        if not self.results:
            return {"error": "没有测试结果"}
        
        total = len(self.results)
        success = sum(1 for r in self.results if r.status == TestStatus.SUCCESS)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        timeout = sum(1 for r in self.results if r.status == TestStatus.TIMEOUT)
        error = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        
        avg_response_time = 0
        if self.results:
            response_times = [r.response_time for r in self.results if r.response_time > 0]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
        
        return {
            "测试总数": total,
            "成功": success,
            "失败": failed,
            "超时": timeout,
            "错误": error,
            "成功率": f"{success/total*100:.1f}%" if total > 0 else "0%",
            "平均响应时间": f"{avg_response_time:.0f}ms",
            "测试时间": self._format_duration()
        }
    
    def generate_text_report(self) -> str:
        """
        生成文本格式报告
        
        Returns:
            格式化的文本报告
        """
        summary = self.generate_summary()
        
        report = []
        report.append("=" * 60)
        report.append("AI 模型连接测试报告")
        report.append("=" * 60)
        report.append("")
        
        # 测试摘要
        report.append("【测试摘要】")
        for key, value in summary.items():
            report.append(f"  {key}: {value}")
        report.append("")
        
        # 详细结果
        report.append("【详细结果】")
        report.append("-" * 60)
        
        # 按服务分组
        services = {}
        for result in self.results:
            if result.service not in services:
                services[result.service] = []
            services[result.service].append(result)
        
        for service, results in services.items():
            report.append(f"\n{service} 服务:")
            report.append("-" * 40)
            
            for result in results:
                status_icon = self._get_status_icon(result.status)
                report.append(f"  {status_icon} {result.model_id}")
                report.append(f"    状态: {result.status.value}")
                report.append(f"    响应时间: {result.response_time:.0f}ms")
                
                if result.status_code:
                    report.append(f"    HTTP状态码: {result.status_code}")
                
                if result.error_message:
                    report.append(f"    错误信息: {result.error_message}")
                
                if result.response_data and result.status == TestStatus.SUCCESS:
                    # 提取响应中的关键信息
                    if 'choices' in result.response_data:
                        choices = result.response_data['choices']
                        if choices and len(choices) > 0:
                            content = choices[0].get('message', {}).get('content', '')
                            if content:
                                # 截取前100个字符
                                preview = content[:100] + "..." if len(content) > 100 else content
                                report.append(f"    响应预览: {preview}")
                
                report.append("")
        
        # 建议和说明
        report.append("【建议】")
        if summary["成功"] == summary["测试总数"]:
            report.append("  ✓ 所有测试通过！API连接正常。")
        else:
            report.append("  ⚠ 部分测试失败，请检查：")
            if summary["失败"] > 0:
                report.append("    - API密钥是否有效")
                report.append("    - 模型ID是否正确")
                report.append("    - 账户余额是否充足（对于付费模型）")
            if summary["超时"] > 0:
                report.append("    - 网络连接是否稳定")
                report.append("    - 服务器是否响应缓慢")
            if summary["错误"] > 0:
                report.append("    - 请求格式是否正确")
                report.append("    - 服务端点是否可访问")
        
        report.append("")
        report.append("=" * 60)
        report.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def generate_json_report(self) -> str:
        """
        生成JSON格式报告
        
        Returns:
            JSON格式的报告字符串
        """
        summary = self.generate_summary()
        
        report_data = {
            "summary": summary,
            "results": [],
            "generated_at": datetime.now().isoformat()
        }
        
        for result in self.results:
            result_data = {
                "model_id": result.model_id,
                "service": result.service,
                "status": result.status.value,
                "response_time_ms": result.response_time,
                "status_code": result.status_code,
                "error_message": result.error_message
            }
            
            # 添加响应数据（如果成功）
            if result.response_data and result.status == TestStatus.SUCCESS:
                # 只保留关键信息，避免数据过大
                if 'choices' in result.response_data:
                    choices = result.response_data['choices']
                    if choices and len(choices) > 0:
                        content = choices[0].get('message', {}).get('content', '')
                        result_data["response_preview"] = content[:200] if content else None
            
            report_data["results"].append(result_data)
        
        return json.dumps(report_data, ensure_ascii=False, indent=2)
    
    def generate_markdown_report(self) -> str:
        """
        生成Markdown格式报告
        
        Returns:
            Markdown格式的报告字符串
        """
        summary = self.generate_summary()
        
        report = []
        report.append("# AI 模型连接测试报告")
        report.append("")
        report.append(f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 测试摘要表格
        report.append("## 测试摘要")
        report.append("")
        report.append("| 指标 | 数值 |")
        report.append("|------|------|")
        for key, value in summary.items():
            report.append(f"| {key} | {value} |")
        report.append("")
        
        # 详细结果表格
        report.append("## 详细结果")
        report.append("")
        report.append("| 服务 | 模型 | 状态 | 响应时间 | 备注 |")
        report.append("|------|------|------|----------|------|")
        
        for result in self.results:
            status_icon = self._get_status_icon(result.status)
            status_text = f"{status_icon} {result.status.value}"
            response_time = f"{result.response_time:.0f}ms"
            note = result.error_message if result.error_message else "-"
            
            # 截断过长的模型ID
            model_id = result.model_id
            if len(model_id) > 30:
                model_id = model_id[:27] + "..."
            
            report.append(f"| {result.service} | {model_id} | {status_text} | {response_time} | {note} |")
        
        report.append("")
        
        # 成功模型列表
        success_results = [r for r in self.results if r.status == TestStatus.SUCCESS]
        if success_results:
            report.append("## 可用模型列表")
            report.append("")
            report.append("以下模型连接测试成功，可以正常使用：")
            report.append("")
            for result in success_results:
                report.append(f"- **{result.service}**: `{result.model_id}` ({result.response_time:.0f}ms)")
            report.append("")
        
        # 失败模型分析
        failed_results = [r for r in self.results if r.status != TestStatus.SUCCESS]
        if failed_results:
            report.append("## 问题分析")
            report.append("")
            
            # 按错误类型分组
            error_types = {}
            for result in failed_results:
                error_key = result.status.value
                if error_key not in error_types:
                    error_types[error_key] = []
                error_types[error_key].append(result)
            
            for error_type, results in error_types.items():
                report.append(f"### {error_type}问题")
                report.append("")
                for result in results:
                    report.append(f"- `{result.model_id}`: {result.error_message or '无详细信息'}")
                report.append("")
        
        report.append("---")
        report.append("*本报告由 AI 模型连接测试工具自动生成*")
        
        return "\n".join(report)
    
    def _get_status_icon(self, status: TestStatus) -> str:
        """
        获取状态图标
        
        Args:
            status: 测试状态
            
        Returns:
            状态图标字符串
        """
        icons = {
            TestStatus.SUCCESS: "✓",
            TestStatus.FAILED: "✗",
            TestStatus.TIMEOUT: "⏱",
            TestStatus.ERROR: "⚠"
        }
        return icons.get(status, "?")
    
    def _format_duration(self) -> str:
        """
        格式化测试持续时间
        
        Returns:
            格式化的时间字符串
        """
        if not self.start_time or not self.end_time:
            return "未知"
        
        duration = self.end_time - self.start_time
        seconds = duration.total_seconds()
        
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}分钟"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}小时"
    
    def save_report(self, filename: str, format: str = "text"):
        """
        保存报告到文件
        
        Args:
            filename: 文件名
            format: 报告格式（text, json, markdown）
        """
        if format == "json":
            content = self.generate_json_report()
        elif format == "markdown":
            content = self.generate_markdown_report()
        else:
            content = self.generate_text_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"报告已保存到: {filename}")


def print_console_report(results: List[TestResult]):
    """
    在控制台打印测试报告
    
    Args:
        results: 测试结果列表
    """
    generator = ReportGenerator()
    generator.set_results(results)
    report = generator.generate_text_report()
    print(report)
#!/usr/bin/env python3
"""
AI 模型连接测试工具
主程序入口文件
"""

import argparse
import sys
import os
from datetime import datetime
from typing import List

from config_parser import load_config_from_file
from model_tester import ModelTester, TestResult
from report_generator import ReportGenerator, print_console_report


def parse_arguments():
    """
    解析命令行参数
    
    Returns:
        解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        description="AI 模型连接测试工具 - 测试各种AI模型API的连接状态",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python ai_tester.py --config config.yaml
  python ai_tester.py --config config.yaml --output report.txt
  python ai_tester.py --config config.yaml --format json --output report.json
  python ai_tester.py --config config.yaml --format markdown --output report.md
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        required=True,
        help='配置文件路径 (YAML格式)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='输出报告文件路径 (不指定则输出到控制台)'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['text', 'json', 'markdown'],
        default='text',
        help='报告格式 (默认: text)'
    )
    
    parser.add_argument(
        '--prompt', '-p',
        type=str,
        help='自定义测试提示词 (覆盖配置文件中的设置)'
    )
    
    parser.add_argument(
        '--timeout', '-t',
        type=int,
        help='请求超时时间(秒) (覆盖配置文件中的设置)'
    )
    
    parser.add_argument(
        '--retries', '-r',
        type=int,
        help='最大重试次数 (覆盖配置文件中的设置)'
    )
    
    parser.add_argument(
        '--free-only',
        action='store_true',
        help='仅测试免费模型'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细测试过程'
    )
    
    return parser.parse_args()


def load_and_validate_config(config_path: str) -> dict:
    """
    加载并验证配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        验证后的配置字典
    """
    try:
        config = load_config_from_file(config_path)
        
        # 显示警告信息
        if config.get('warnings'):
            print("配置警告:")
            for warning in config['warnings']:
                print(f"  ⚠ {warning}")
            print()
        
        # 检查是否有有效的测试配置
        if not config.get('valid_configs'):
            print("错误: 没有找到有效的API配置，请检查配置文件")
            sys.exit(1)
        
        return config
        
    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"配置文件解析错误: {e}")
        sys.exit(1)


def run_tests(config: dict, args) -> List[TestResult]:
    """
    运行测试
    
    Args:
        config: 配置字典
        args: 命令行参数
        
    Returns:
        测试结果列表
    """
    # 获取测试配置
    test_config = config.get('test_config', {})
    
    # 应用命令行参数覆盖
    timeout = args.timeout if args.timeout else test_config.get('timeout', 30)
    max_retries = args.retries if args.retries else test_config.get('max_retries', 2)
    test_prompt = args.prompt if args.prompt else test_config.get('test_prompt', '你好，请简单介绍一下你自己')
    
    print("AI 模型连接测试工具")
    print("=" * 50)
    print(f"测试提示词: {test_prompt}")
    print(f"超时时间: {timeout}秒")
    print(f"最大重试: {max_retries}次")
    print("=" * 50)
    
    # 创建测试器
    with ModelTester(timeout=timeout, max_retries=max_retries) as tester:
        # 获取要测试的配置
        valid_configs = config.get('valid_configs', {})
        
        # 如果指定了仅测试免费模型，过滤配置
        if args.free_only:
            filtered_configs = {}
            for service, service_config in valid_configs.items():
                if service == 'openrouter':  # OpenRouter有免费模型
                    filtered_configs[service] = service_config
                # 其他服务根据模型ID判断是否免费
                elif 'models' in service_config:
                    free_models = [m for m in service_config['models'] if ':free' in m]
                    if free_models:
                        filtered_configs[service] = {
                            **service_config,
                            'models': free_models
                        }
            valid_configs = filtered_configs
        
        # 运行批量测试
        print("\n开始测试...")
        start_time = datetime.now()
        
        results = tester.batch_test(valid_configs, test_prompt)
        
        end_time = datetime.now()
        print(f"\n测试完成，耗时: {(end_time - start_time).total_seconds():.1f}秒")
        
        return results


def generate_report(results: List[TestResult], args):
    """
    生成测试报告
    
    Args:
        results: 测试结果列表
        args: 命令行参数
    """
    generator = ReportGenerator()
    generator.set_results(results)
    
    if args.output:
        # 保存到文件
        generator.save_report(args.output, args.format)
        print(f"\n报告已保存到: {args.output}")
        
        # 同时在控制台显示摘要
        print("\n测试摘要:")
        summary = generator.generate_summary()
        for key, value in summary.items():
            print(f"  {key}: {value}")
    else:
        # 输出到控制台
        print("\n" + "=" * 60)
        if args.format == 'json':
            print(generator.generate_json_report())
        elif args.format == 'markdown':
            print(generator.generate_markdown_report())
        else:
            print_console_report(results)


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 检查配置文件是否存在
    if not os.path.exists(args.config):
        print(f"错误: 配置文件不存在: {args.config}")
        sys.exit(1)
    
    # 加载配置
    print(f"加载配置文件: {args.config}")
    config = load_and_validate_config(args.config)
    
    # 运行测试
    results = run_tests(config, args)
    
    # 生成报告
    generate_report(results, args)
    
    # 返回退出码（如果有失败则返回1）
    success_count = sum(1 for r in results if r.status.value == "成功")
    if success_count < len(results):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
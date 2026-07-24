#!/usr/bin/env python3
"""
AI 模型连接测试工具 - 图形界面版本
双击运行即可使用
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import sys
import os
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_parser import load_config_from_file, ConfigParser
from model_tester import ModelTester, TestResult, TestStatus
from report_generator import ReportGenerator


class AITesterGUI:
    """AI模型测试工具图形界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("AI 模型连接测试工具 v1.0")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # 设置样式
        self.style = ttk.Style()
        self.style.configure("Title.TLabel", font=("微软雅黑", 16, "bold"))
        self.style.configure("Status.TLabel", font=("微软雅黑", 9))
        self.style.configure("Run.TButton", font=("微软雅黑", 11, "bold"))
        
        # 测试结果
        self.results = []
        self.is_testing = False
        
        # 创建界面
        self.create_widgets()
        
        # 自动加载默认配置
        self.load_default_config()
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ===== 标题区域 =====
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="AI 模型连接测试工具", style="Title.TLabel").pack(side=tk.LEFT)
        
        # ===== 配置区域 =====
        config_frame = ttk.LabelFrame(main_frame, text="配置文件", padding="5")
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        config_inner = ttk.Frame(config_frame)
        config_inner.pack(fill=tk.X)
        
        self.config_path_var = tk.StringVar(value="config.yaml")
        ttk.Entry(config_inner, textvariable=self.config_path_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(config_inner, text="浏览...", command=self.browse_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(config_inner, text="加载", command=self.load_config).pack(side=tk.LEFT)
        
        # ===== 测试选项区域 =====
        options_frame = ttk.LabelFrame(main_frame, text="测试选项", padding="5")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 第一行选项
        row1 = ttk.Frame(options_frame)
        row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(row1, text="测试提示词:").pack(side=tk.LEFT)
        self.prompt_var = tk.StringVar(value="你好，请简单介绍一下你自己")
        ttk.Entry(row1, textvariable=self.prompt_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 第二行选项
        row2 = ttk.Frame(options_frame)
        row2.pack(fill=tk.X, pady=2)
        
        ttk.Label(row2, text="超时时间(秒):").pack(side=tk.LEFT)
        self.timeout_var = tk.StringVar(value="15")
        ttk.Entry(row2, textvariable=self.timeout_var, width=8).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row2, text="重试次数:").pack(side=tk.LEFT, padx=(20, 0))
        self.retries_var = tk.StringVar(value="2")
        ttk.Entry(row2, textvariable=self.retries_var, width=8).pack(side=tk.LEFT, padx=5)
        
        self.free_only_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(row2, text="仅测试免费模型", variable=self.free_only_var).pack(side=tk.LEFT, padx=(20, 0))
        
        # ===== API 状态区域 =====
        api_frame = ttk.LabelFrame(main_frame, text="API 配置状态", padding="5")
        api_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.api_status_text = scrolledtext.ScrolledText(api_frame, height=4, font=("Consolas", 9))
        self.api_status_text.pack(fill=tk.X)
        self.api_status_text.config(state=tk.DISABLED)
        
        # ===== 操作按钮区域 =====
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.run_button = ttk.Button(button_frame, text="开始测试", style="Run.TButton", command=self.start_test)
        self.run_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_test, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="清空结果", command=self.clear_results).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="导出报告", command=self.export_report).pack(side=tk.LEFT)
        
        # ===== 测试结果区域 =====
        result_frame = ttk.LabelFrame(main_frame, text="测试结果", padding="5")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(result_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        # 结果文本框
        self.result_text = scrolledtext.ScrolledText(result_frame, font=("Consolas", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # ===== 状态栏 =====
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(status_frame, textvariable=self.status_var, style="Status.TLabel").pack(side=tk.LEFT)
        
        self.count_var = tk.StringVar(value="")
        ttk.Label(status_frame, textvariable=self.count_var, style="Status.TLabel").pack(side=tk.RIGHT)
    
    def load_default_config(self):
        """加载默认配置文件"""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
        if os.path.exists(config_path):
            self.config_path_var.set(config_path)
            self.load_config()
    
    def browse_config(self):
        """浏览选择配置文件"""
        filename = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("YAML文件", "*.yaml;*.yml"), ("所有文件", "*.*")]
        )
        if filename:
            self.config_path_var.set(filename)
            self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        config_path = self.config_path_var.get()
        
        if not os.path.exists(config_path):
            messagebox.showerror("错误", f"配置文件不存在: {config_path}")
            return
        
        try:
            self.config = load_config_from_file(config_path)
            self.show_api_status()
            self.status_var.set("配置文件加载成功")
        except Exception as e:
            messagebox.showerror("错误", f"配置文件加载失败: {e}")
            self.status_var.set("配置文件加载失败")
    
    def show_api_status(self):
        """显示API配置状态"""
        self.api_status_text.config(state=tk.NORMAL)
        self.api_status_text.delete(1.0, tk.END)
        
        if hasattr(self, 'config'):
            # 显示有效配置
            valid_configs = self.config.get('valid_configs', {})
            self.api_status_text.insert(tk.END, "已配置服务: ", "normal")
            if valid_configs:
                for service in valid_configs.keys():
                    self.api_status_text.insert(tk.END, f"[{service}] ", "success")
            else:
                self.api_status_text.insert(tk.END, "无", "error")
            self.api_status_text.insert(tk.END, "\n")
            
            # 显示警告
            warnings = self.config.get('warnings', [])
            if warnings:
                self.api_status_text.insert(tk.END, "警告: ", "warning")
                for warning in warnings:
                    self.api_status_text.insert(tk.END, f"\n  - {warning}", "warning")
        
        self.api_status_text.config(state=tk.DISABLED)
    
    def start_test(self):
        """开始测试"""
        if self.is_testing:
            return
        
        if not hasattr(self, 'config'):
            messagebox.showwarning("警告", "请先加载配置文件")
            return
        
        self.is_testing = True
        self.run_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.results = []
        self.result_text.delete(1.0, tk.END)
        
        # 在新线程中运行测试
        self.test_thread = threading.Thread(target=self.run_tests, daemon=True)
        self.test_thread.start()
    
    def stop_test(self):
        """停止测试"""
        self.is_testing = False
        self.status_var.set("正在停止...")
    
    def clear_results(self):
        """清空结果"""
        self.result_text.delete(1.0, tk.END)
        self.results = []
        self.progress_var.set(0)
        self.count_var.set("")
        self.status_var.set("就绪")
    
    def run_tests(self):
        """运行测试（在后台线程中执行）"""
        try:
            # 获取测试参数
            timeout = int(self.timeout_var.get())
            max_retries = int(self.retries_var.get())
            test_prompt = self.prompt_var.get()
            free_only = self.free_only_var.get()
            
            # 更新状态
            self.root.after(0, lambda: self.status_var.set("正在测试..."))
            
            # 创建测试器
            with ModelTester(timeout=timeout, max_retries=max_retries) as tester:
                valid_configs = self.config.get('valid_configs', {})
                
                # 如果仅测试免费模型，过滤配置
                if free_only:
                    filtered_configs = {}
                    for service, service_config in valid_configs.items():
                        if service == 'openrouter':
                            filtered_configs[service] = service_config
                        elif 'models' in service_config:
                            free_models = [m for m in service_config['models'] if ':free' in m]
                            if free_models:
                                filtered_configs[service] = {**service_config, 'models': free_models}
                    valid_configs = filtered_configs
                
                # 计算总测试数
                total_models = sum(len(c.get('models', [])) for c in valid_configs.values())
                tested_count = 0
                
                for service_name, service_config in valid_configs.items():
                    if not self.is_testing:
                        break
                    
                    api_key = service_config.get('api_key')
                    models = service_config.get('models', [])
                    
                    if not api_key:
                        continue
                    
                    self.root.after(0, lambda s=service_name: self.append_result(f"\n{'='*50}\n测试 {s} 服务\n{'='*50}\n"))
                    
                    for model_id in models:
                        if not self.is_testing:
                            break
                        
                        # 运行测试
                        result = tester.test_model(service_name, api_key, model_id, test_prompt)
                        self.results.append(result)
                        
                        # 更新界面
                        tested_count += 1
                        progress = (tested_count / total_models) * 100
                        self.root.after(0, lambda r=result, p=progress, tc=tested_count, tm=total_models: 
                                        self.update_result(r, p, tc, tm))
            
            # 测试完成
            self.root.after(0, self.test_completed)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"测试过程中出错: {e}"))
            self.root.after(0, self.test_completed)
    
    def update_result(self, result, progress, tested_count, total_models):
        """更新测试结果（在主线程中执行）"""
        # 更新进度条
        self.progress_var.set(progress)
        
        # 构建结果文本
        status_icon = "✓" if result.status == TestStatus.SUCCESS else "✗"
        color_tag = "success" if result.status == TestStatus.SUCCESS else "error"
        
        self.result_text.insert(tk.END, f"\n{status_icon} ", "normal")
        self.result_text.insert(tk.END, f"{result.model_id}\n", color_tag)
        self.result_text.insert(tk.END, f"   状态: {result.status.value}", color_tag)
        self.result_text.insert(tk.END, f" | 响应时间: {result.response_time:.0f}ms\n", "normal")
        
        if result.error_message:
            self.result_text.insert(tk.END, f"   错误: {result.error_message}\n", "error")
        
        if result.response_data and result.status == TestStatus.SUCCESS:
            if 'choices' in result.response_data:
                content = result.response_data['choices'][0].get('message', {}).get('content', '')
                if content:
                    preview = content[:80] + "..." if len(content) > 80 else content
                    self.result_text.insert(tk.END, f"   回复: {preview}\n", "normal")
        
        self.result_text.see(tk.END)
        
        # 更新计数
        success_count = sum(1 for r in self.results if r.status == TestStatus.SUCCESS)
        self.count_var.set(f"已测试: {tested_count}/{total_models} | 成功: {success_count}")
    
    def append_result(self, text):
        """追加结果文本"""
        self.result_text.insert(tk.END, text)
        self.result_text.see(tk.END)
    
    def test_completed(self):
        """测试完成"""
        self.is_testing = False
        self.run_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        # 显示汇总
        success_count = sum(1 for r in self.results if r.status == TestStatus.SUCCESS)
        total_count = len(self.results)
        
        self.result_text.insert(tk.END, f"\n{'='*50}\n", "normal")
        self.result_text.insert(tk.END, f"测试完成! 成功: {success_count}/{total_count}\n", "title")
        self.result_text.insert(tk.END, f"{'='*50}\n", "normal")
        
        self.status_var.set(f"测试完成 - 成功率: {success_count/total_count*100:.1f}%" if total_count > 0 else "测试完成")
        self.progress_var.set(100)
    
    def export_report(self):
        """导出测试报告"""
        if not self.results:
            messagebox.showwarning("警告", "没有测试结果可导出")
            return
        
        filename = filedialog.asksaveasfilename(
            title="保存测试报告",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("Markdown文件", "*.md"), ("JSON文件", "*.json")]
        )
        
        if filename:
            generator = ReportGenerator()
            generator.set_results(self.results)
            
            if filename.endswith('.json'):
                format_type = 'json'
            elif filename.endswith('.md'):
                format_type = 'markdown'
            else:
                format_type = 'text'
            
            generator.save_report(filename, format_type)
            messagebox.showinfo("成功", f"报告已保存到: {filename}")


def main():
    """主函数"""
    root = tk.Tk()
    
    # 配置文本标签样式
    app = AITesterGUI(root)
    app.result_text.tag_config("normal", foreground="black")
    app.result_text.tag_config("success", foreground="green")
    app.result_text.tag_config("error", foreground="red")
    app.result_text.tag_config("warning", foreground="orange")
    app.result_text.tag_config("title", foreground="blue", font=("微软雅黑", 11, "bold"))
    
    app.api_status_text.tag_config("normal", foreground="black")
    app.api_status_text.tag_config("success", foreground="green")
    app.api_status_text.tag_config("error", foreground="red")
    app.api_status_text.tag_config("warning", foreground="orange")
    
    root.mainloop()


if __name__ == '__main__':
    main()

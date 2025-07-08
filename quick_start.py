#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动脚本
提供交互式配置和运行Token输出速率测试
"""

import asyncio
import os
import sys
from model_token_rate_test import TestConfig, TokenRateTester

def print_banner():
    """打印欢迎横幅"""
    print("=" * 60)
    print("🚀 模型Token输出速率测试工具 - 快速启动")
    print("=" * 60)
    print()

def get_user_config():
    """获取用户配置"""
    config = TestConfig()
    
    print("📋 配置设置")
    print("-" * 30)
    
    # 模型URL
    print("请选择模型服务类型:")
    print("1. OpenAI API")
    print("2. Azure OpenAI")
    print("3. 本地模型服务 (vLLM/Ollama等)")
    print("4. 自定义服务")
    
    while True:
        choice = input("请选择 (1-4): ").strip()
        if choice == "1":
            config.model_url = "https://api.openai.com/v1/chat/completions"
            config.model_name = "gpt-3.5-turbo"
            break
        elif choice == "2":
            config.model_url = input("请输入Azure OpenAI端点URL: ").strip()
            config.model_name = "gpt-35-turbo"
            break
        elif choice == "3":
            config.model_url = "http://localhost:8000/v1/chat/completions"
            config.model_name = input("请输入模型名称 (如: llama2-7b-chat): ").strip()
            break
        elif choice == "4":
            config.model_url = input("请输入模型服务URL: ").strip()
            config.model_name = input("请输入模型名称: ").strip()
            break
        else:
            print("❌ 无效选择，请重新输入")
    
    # API密钥
    if choice in ["1", "2", "4"]:
        config.api_key = input("请输入API密钥: ").strip()
    else:
        config.api_key = input("请输入API密钥 (如果不需要可留空): ").strip()
    
    # 其他参数
    print("\n🔧 高级配置 (可选，直接回车使用默认值)")
    
    try:
        max_tokens = input(f"最大Token数 (默认: {config.max_tokens}): ").strip()
        if max_tokens:
            config.max_tokens = int(max_tokens)
    except ValueError:
        print("❌ 无效输入，使用默认值")
    
    try:
        temperature = input(f"温度参数 (默认: {config.temperature}): ").strip()
        if temperature:
            config.temperature = float(temperature)
    except ValueError:
        print("❌ 无效输入，使用默认值")
    
    try:
        timeout = input(f"超时时间(秒) (默认: {config.timeout}): ").strip()
        if timeout:
            config.timeout = int(timeout)
    except ValueError:
        print("❌ 无效输入，使用默认值")
    
    return config

def confirm_config(config):
    """确认配置"""
    print("\n📋 当前配置:")
    print("-" * 30)
    print(f"模型URL: {config.model_url}")
    print(f"模型名称: {config.model_name}")
    print(f"API密钥: {'*' * 10 if config.api_key else '无'}")
    print(f"最大Token数: {config.max_tokens}")
    print(f"温度参数: {config.temperature}")
    print(f"超时时间: {config.timeout}秒")
    print()
    
    while True:
        confirm = input("确认开始测试? (y/n): ").lower().strip()
        if confirm in ['y', 'yes', '是']:
            return True
        elif confirm in ['n', 'no', '否']:
            return False
        else:
            print("❌ 请输入 y 或 n")

def run_test(config):
    """运行测试"""
    print("\n🚀 开始测试...")
    print("=" * 50)
    
    try:
        # 创建测试器
        tester = TokenRateTester(config)
        
        # 运行异步测试
        asyncio.run(tester.run_all_tests())
        
        # 生成报告
        print("\n📊 生成报告...")
        report = tester.generate_report()
        
        print("\n" + "=" * 50)
        print("✅ 测试完成！")
        print("=" * 50)
        print(report)
        
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        return False
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        return False

def show_results():
    """显示结果文件"""
    print("\n📁 生成的文件:")
    print("-" * 30)
    
    # 查找报告文件
    report_files = [f for f in os.listdir('.') if f.startswith('token_rate_report_')]
    chart_files = [f for f in os.listdir('.') if f.startswith('token_rate_chart_')]
    response_dir = 'responses' if os.path.exists('responses') else None
    
    if report_files:
        print("📄 文本报告:")
        for f in sorted(report_files, reverse=True)[:3]:  # 显示最新的3个
            print(f"  - {f}")
    
    if chart_files:
        print("📈 图表报告:")
        for f in sorted(chart_files, reverse=True)[:3]:  # 显示最新的3个
            print(f"  - {f}")
    
    if response_dir:
        response_files = os.listdir(response_dir)
        print(f"📝 响应文件: {len(response_files)} 个文件在 responses/ 目录中")
    
    print()

def main():
    """主函数"""
    try:
        print_banner()
        
        # 检查依赖
        try:
            import aiohttp
            import matplotlib
        except ImportError as e:
            print(f"❌ 缺少依赖包: {e}")
            print("请运行: pip install -r requirements.txt")
            return
        
        # 获取配置
        config = get_user_config()
        
        # 确认配置
        if not confirm_config(config):
            print("👋 测试已取消")
            return
        
        # 运行测试
        success = run_test(config)
        
        if success:
            show_results()
            
            # 询问是否查看报告
            while True:
                view_report = input("\n是否查看最新报告? (y/n): ").lower().strip()
                if view_report in ['y', 'yes', '是']:
                    report_files = [f for f in os.listdir('.') if f.startswith('token_rate_report_')]
                    if report_files:
                        latest_report = sorted(report_files, reverse=True)[0]
                        try:
                            with open(latest_report, 'r', encoding='utf-8') as f:
                                print(f"\n📄 {latest_report}:")
                                print("-" * 50)
                                print(f.read())
                        except Exception as e:
                            print(f"❌ 读取报告失败: {e}")
                    break
                elif view_report in ['n', 'no', '否']:
                    break
                else:
                    print("❌ 请输入 y 或 n")
        
        print("\n👋 感谢使用！")
        
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序运行错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
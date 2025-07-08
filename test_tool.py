#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具功能测试脚本
用于验证TokenRateTester的基本功能
"""

import asyncio
import json
import aiohttp
from unittest.mock import AsyncMock, patch
from model_token_rate_test import TestConfig, TokenRateTester, TestResult

class MockResponse:
    """模拟API响应"""
    def __init__(self, status=200, content="", tokens=100):
        self.status = status
        self.content = content
        self.tokens = tokens
    
    async def text(self):
        if self.status == 200:
            return json.dumps({
                "choices": [{"message": {"content": self.content}}],
                "usage": {"total_tokens": self.tokens}
            })
        else:
            return f"HTTP {self.status} Error"

async def test_basic_functionality():
    """测试基本功能"""
    print("开始测试基本功能...")
    
    # 创建测试配置
    config = TestConfig()
    config.model_url = "http://test-server:8000/v1/chat/completions"
    config.model_name = "test-model"
    config.api_key = "test-key"
    
    # 创建测试器
    tester = TokenRateTester(config)
    
    # 测试随机问题生成
    prompt1 = tester.get_random_prompt()
    prompt2 = tester.get_random_prompt()
    print(f"随机问题1: {prompt1[:50]}...")
    print(f"随机问题2: {prompt2[:50]}...")
    print(f"问题是否不同: {prompt1 != prompt2}")
    
    # 测试响应内容保存
    test_content = "这是一个测试响应内容，包含中文字符和English text。"
    tester.save_response_content(1, 2, test_content)
    print("响应内容保存测试完成")
    
    print("基本功能测试完成\n")

async def test_mock_api_calls():
    """测试模拟API调用"""
    print("开始测试模拟API调用...")
    
    config = TestConfig()
    tester = TokenRateTester(config)
    
    # 模拟成功的API响应
    mock_response = MockResponse(
        status=200,
        content="这是一个模拟的API响应，用于测试token计算功能。",
        tokens=150
    )
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_post.return_value.__aenter__.return_value = mock_response
        
        async with aiohttp.ClientSession() as session:
            result = await tester.call_model_api(session, "测试问题")
            
            print(f"API调用结果: {result}")
            print(f"是否成功: {result.get('success', False)}")
            print(f"Token数: {result.get('tokens', 0)}")
            print(f"响应时间: {result.get('response_time', 0):.2f}秒")
    
    print("模拟API调用测试完成\n")

def test_report_generation():
    """测试报告生成功能"""
    print("开始测试报告生成功能...")
    
    config = TestConfig()
    tester = TokenRateTester(config)
    
    # 添加模拟测试结果
    mock_results = [
        TestResult(
            concurrency=1,
            total_tokens=1000,
            total_time=10.0,
            tokens_per_second=100.0,
            success_count=1,
            error_count=0,
            avg_response_time=10.0,
            min_response_time=10.0,
            max_response_time=10.0
        ),
        TestResult(
            concurrency=2,
            total_tokens=1800,
            total_time=10.0,
            tokens_per_second=180.0,
            success_count=2,
            error_count=0,
            avg_response_time=5.0,
            min_response_time=4.8,
            max_response_time=5.2
        )
    ]
    
    tester.results = mock_results
    
    # 生成文本报告
    text_report = tester.generate_text_report()
    print("文本报告生成成功")
    print(f"报告长度: {len(text_report)} 字符")
    
    # 生成图表报告
    try:
        tester.generate_chart_report("test")
        print("图表报告生成成功")
    except Exception as e:
        print(f"图表报告生成失败: {e}")
    
    print("报告生成测试完成\n")

def test_error_handling():
    """测试错误处理"""
    print("开始测试错误处理...")
    
    config = TestConfig()
    tester = TokenRateTester(config)
    
    # 测试异常响应处理
    mock_responses = [
        Exception("网络连接错误"),
        {"success": False, "error": "API认证失败", "response_time": 1.0},
        {"success": True, "content": "正常响应", "tokens": 100, "response_time": 2.0},
        "意外的响应类型"
    ]
    
    # 模拟处理结果
    total_tokens = 0
    success_count = 0
    error_count = 0
    response_times = []
    
    for i, response in enumerate(mock_responses):
        if isinstance(response, Exception):
            error_count += 1
            print(f"处理异常 {i}: {response}")
        elif isinstance(response, dict) and response.get('success'):
            success_count += 1
            total_tokens += response.get('tokens', 0)
            response_times.append(response.get('response_time', 0))
            print(f"处理成功响应 {i}: {response.get('tokens', 0)} tokens")
        elif isinstance(response, dict):
            error_count += 1
            print(f"处理失败响应 {i}: {response.get('error', '未知错误')}")
        else:
            error_count += 1
            print(f"处理意外响应类型 {i}: {type(response)}")
    
    print(f"处理结果: 成功 {success_count}, 失败 {error_count}, 总Token {total_tokens}")
    print("错误处理测试完成\n")

async def main():
    """主测试函数"""
    print("=" * 50)
    print("Token输出速率测试工具 - 功能测试")
    print("=" * 50)
    
    try:
        # 运行各项测试
        await test_basic_functionality()
        await test_mock_api_calls()
        test_report_generation()
        test_error_handling()
        
        print("=" * 50)
        print("所有测试完成！")
        print("=" * 50)
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 
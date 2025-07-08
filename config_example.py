#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置示例文件
展示如何配置不同的模型服务
"""

from model_token_rate_test import TestConfig

# OpenAI API 配置示例
def get_openai_config():
    """OpenAI API 配置"""
    config = TestConfig()
    config.model_url = "https://api.openai.com/v1/chat/completions"
    config.model_name = "gpt-3.5-turbo"
    config.api_key = "your-openai-api-key"
    config.max_tokens = 2000
    config.temperature = 0.7
    config.timeout = 60
    return config

# Azure OpenAI 配置示例
def get_azure_config():
    """Azure OpenAI 配置"""
    config = TestConfig()
    config.model_url = "https://your-resource.openai.azure.com/openai/deployments/your-deployment/chat/completions?api-version=2023-05-15"
    config.model_name = "gpt-35-turbo"
    config.api_key = "your-azure-api-key"
    config.max_tokens = 2000
    config.temperature = 0.7
    config.timeout = 60
    return config

# 本地模型服务配置示例 (如 vLLM, Ollama 等)
def get_local_config():
    """本地模型服务配置"""
    config = TestConfig()
    config.model_url = "http://localhost:8000/v1/chat/completions"
    config.model_name = "llama2-7b-chat"
    config.api_key = "your-local-api-key"  # 如果不需要认证可以设为空字符串
    config.max_tokens = 2000
    config.temperature = 0.7
    config.timeout = 60
    return config

# Anthropic Claude 配置示例
def get_claude_config():
    """Anthropic Claude 配置"""
    config = TestConfig()
    config.model_url = "https://api.anthropic.com/v1/messages"
    config.model_name = "claude-3-sonnet-20240229"
    config.api_key = "your-anthropic-api-key"
    config.max_tokens = 2000
    config.temperature = 0.7
    config.timeout = 60
    return config

# 自定义模型服务配置示例
def get_custom_config():
    """自定义模型服务配置"""
    config = TestConfig()
    config.model_url = "https://your-custom-model-server.com/api/chat"
    config.model_name = "your-custom-model"
    config.api_key = "your-custom-api-key"
    config.max_tokens = 2000
    config.temperature = 0.7
    config.timeout = 60
    return config

# 使用示例
if __name__ == "__main__":
    print("配置示例:")
    print("1. OpenAI API")
    print("2. Azure OpenAI")
    print("3. 本地模型服务")
    print("4. Anthropic Claude")
    print("5. 自定义模型服务")
    
    choice = input("请选择配置类型 (1-5): ")
    
    config_map = {
        "1": get_openai_config,
        "2": get_azure_config,
        "3": get_local_config,
        "4": get_claude_config,
        "5": get_custom_config
    }
    
    if choice in config_map:
        config = config_map[choice]()
        print(f"\n选择的配置:")
        print(f"模型URL: {config.model_url}")
        print(f"模型名称: {config.model_name}")
        print(f"API密钥: {config.api_key[:10]}..." if config.api_key else "无")
        print(f"最大Token数: {config.max_tokens}")
        print(f"温度参数: {config.temperature}")
        print(f"超时时间: {config.timeout}秒")
    else:
        print("无效选择") 
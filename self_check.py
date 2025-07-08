import importlib.util
import sys
import socket
from dataclasses import dataclass
import matplotlib.font_manager as fm
import openai
import time
import json

@dataclass
class ModelConfig:
    name: str = 'default'
    api_type: str = 'openai'  # openai/thirdparty/vllm/ollama
    model_url: str = ''
    model_name: str = ''
    api_key: str = ''
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 60

def check_dependencies():
    required = ["openai", "matplotlib"]
    missing = []
    for pkg in required:
        if importlib.util.find_spec(pkg) is None:
            missing.append(pkg)
    if missing:
        print(f"缺少依赖包: {', '.join(missing)}，请先通过 pip install 安装！")
        return False
    return True

def check_network(url: str, timeout: int = 5):
    try:
        # 支持http/https和端口
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        socket.create_connection((host, port), timeout=timeout)
        return True
    except Exception as e:
        print(f"网络连接失败: {e}，请检查模型URL和网络环境。")
        return False

def check_api_key_stream(config: ModelConfig):
    try:
        # 只在openai/thirdparty类型下设置api_key
        if config.api_type in ("openai", "thirdparty"):
            try:
                from openai import error as openai_error
            except ImportError:
                openai_error = None
            openai.api_key = config.api_key or None
            openai.base_url = config.model_url.rstrip("/v1/chat/completions")
        else:
            # 本地部署如vllm/ollama等，openai模块可不设置api_key
            openai.api_key = None
            openai.base_url = config.model_url.rstrip("/v1/chat/completions")
        start_time = time.time()
        first_token_time = None
        content = ''
        try:
            stream = openai.ChatCompletion.create(
                model=config.model_name,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
                temperature=0.1,
                stream=True
            )
            for chunk in stream:
                if 'choices' in chunk and chunk['choices']:
                    delta = chunk['choices'][0].get('delta', {})
                    token_piece = delta.get('content', '')
                    if token_piece:
                        if first_token_time is None:
                            first_token_time = time.time()
                        content += token_piece
            end_time = time.time()
            if first_token_time is None:
                print("模型接口无响应或未返回任何Token，请检查模型服务是否正常、API Key是否有效。")
                return False
            if not content.strip():
                print("模型接口响应内容为空，可能API Key无效、模型未加载或服务异常。")
                return False
            print(f"模型接口流式输出正常，首Token超时: {first_token_time - start_time:.3f}s，总耗时: {end_time - start_time:.3f}s。内容片段: {content[:30]}")
            return True
        except Exception as e:
            # openai/thirdparty类型下，优先识别openai.error
            if config.api_type in ("openai", "thirdparty") and 'openai_error' in locals() and openai_error:
                if isinstance(e, openai_error.AuthenticationError):
                    print("API Key 无效或未授权，请检查API Key配置。")
                    return False
                if isinstance(e, openai_error.Timeout):
                    print("模型接口请求超时，请检查服务状态和timeout设置。")
                    return False
            # 其它情况直接输出异常内容
            print(f"API Key 检查异常: {e}，请检查API Key、模型URL、网络环境和模型服务状态。")
            return False
    except Exception as e:
        print(f"API Key 检查异常: {e}，请检查API Key、模型URL、网络环境和模型服务状态。")
        return False

def check_matplotlib_fonts():
    # 检查是否有常用中文字体
    font_list = [f.name for f in fm.fontManager.ttflist]
    for font in ["SimHei", "DejaVu Sans", "Arial Unicode MS"]:
        if font in font_list:
            print(f"matplotlib已检测到可用中文字体: {font}")
            return True
    print("警告：matplotlib未检测到常用中文字体，图表可能出现乱码。建议安装SimHei或DejaVu Sans字体。")
    return False

def run_self_check(config: ModelConfig):
    print("\n[自检] 开始依赖包检查...")
    if not check_dependencies():
        sys.exit(1)
    print("[自检] 依赖包检查通过")

    print("[自检] 检查matplotlib中文字体...")
    check_matplotlib_fonts()

    print("[自检] 检查网络连通性...")
    if not check_network(config.model_url):
        sys.exit(1)
    print("[自检] 网络连通性正常")

    print("[自检] 检查API Key及模型接口(流式)...")
    if not check_api_key_stream(config):
        sys.exit(1)
    print("[自检] API Key及模型接口检查通过\n") 
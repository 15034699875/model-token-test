import importlib.util
import sys
import socket
import requests
from config import ModelConfig
import matplotlib.font_manager as fm

def check_dependencies():
    required = ["aiohttp", "matplotlib"]
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
        host = url.split('//')[-1].split('/')[0].split(':')[0]
        socket.create_connection((host, 80), timeout=timeout)
        return True
    except Exception as e:
        print(f"网络连接失败: {e}")
        return False

def check_api_key(config: ModelConfig):
    try:
        headers = {"Content-Type": "application/json"}
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"
        # 构造不同API类型的请求体
        if config.api_type in ('openai', 'thirdparty'):
            payload = {"model": config.model_name, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1, "temperature": 0.1, "stream": False}
        elif config.api_type == 'vllm':
            payload = {"model": config.model_name, "prompt": "ping", "max_tokens": 1, "temperature": 0.1, "stream": False}
        elif config.api_type == 'ollama':
            payload = {"model": config.model_name, "prompt": "ping", "options": {"num_predict": 1, "temperature": 0.1}}
        else:
            print(f"不支持的API类型: {config.api_type}")
            return False
        resp = requests.post(config.model_url, headers=headers, json=payload, timeout=10)
        # 检查编码
        try:
            resp_text = resp.content.decode('utf-8')
        except Exception:
            print("模型接口返回内容非UTF-8编码，疑似乱码！")
            return False
        if resp.status_code == 401:
            print("API Key 无效或未授权！")
            return False
        elif resp.status_code != 200:
            print(f"API Key 检查失败，HTTP状态码: {resp.status_code}, 响应: {resp_text}")
            return False
        # 检查内容是否乱码
        if '\ufffd' in resp_text:
            print("模型接口返回内容疑似乱码！")
            return False
        print("模型接口返回内容正常，编码为UTF-8。")
        return True
    except Exception as e:
        print(f"API Key 检查异常: {e}")
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

    print("[自检] 检查API Key及模型接口...")
    if not check_api_key(config):
        sys.exit(1)
    print("[自检] API Key及模型接口检查通过\n") 
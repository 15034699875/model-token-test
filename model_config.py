from dataclasses import dataclass

SUPPORTED_API_TYPES = [
    'openai',      # 标准OpenAI接口
    'thirdparty',  # 兼容OpenAI格式的第三方接口
    'vllm',        # 本地vllm推理
    'ollama'       # 本地Ollama推理
]

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
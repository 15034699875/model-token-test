import json
import os
from dataclasses import dataclass, asdict, field
from typing import List, Dict

CONFIG_FILE = 'config.json'

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

@dataclass
class ConfigManager:
    models: List[ModelConfig] = field(default_factory=list)
    active_index: int = 0

    @classmethod
    def load(cls, file_path: str = CONFIG_FILE) -> 'ConfigManager':
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                models = [ModelConfig(**m) for m in data.get('models', [])]
                active_index = data.get('active_index', 0)
                return cls(models=models, active_index=active_index)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
        # 默认配置
        return cls(models=[ModelConfig(
            name='默认OpenAI',
            api_type='openai',
            model_url='http://localhost:8000/v1/chat/completions',
            model_name='gpt-3.5-turbo',
            api_key='your-api-key-here',
        )], active_index=0)

    def save(self, file_path: str = CONFIG_FILE):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'models': [asdict(m) for m in self.models],
                    'active_index': self.active_index
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def interactive_menu(self):
        while True:
            print("\n【模型配置管理】")
            for idx, m in enumerate(self.models):
                flag = '（当前）' if idx == self.active_index else ''
                print(f"  [{idx}] {m.name} | 类型: {m.api_type} | 地址: {m.model_url} {flag}")
            print("  [a] 添加新配置  [e] 编辑当前配置  [s] 切换当前配置  [d] 删除配置  [q] 退出")
            op = input("请选择操作: ").strip().lower()
            if op == 'a':
                self.add_model()
            elif op == 'e':
                self.edit_model(self.active_index)
            elif op == 's':
                idx = input("输入要切换的配置编号: ").strip()
                if idx.isdigit() and 0 <= int(idx) < len(self.models):
                    self.active_index = int(idx)
                    print(f"已切换到配置[{idx}] {self.models[self.active_index].name}")
                else:
                    print("编号无效")
            elif op == 'd':
                if len(self.models) <= 1:
                    print("至少保留一个配置！")
                else:
                    idx = input("输入要删除的配置编号: ").strip()
                    if idx.isdigit() and 0 <= int(idx) < len(self.models):
                        del self.models[int(idx)]
                        self.active_index = 0
                        print("已删除并切换到第一个配置")
                    else:
                        print("编号无效")
            elif op == 'q':
                self.save()
                print("配置已保存到 config.json\n")
                break
            else:
                print("无效操作，请重新选择。")

    def add_model(self):
        print("\n添加新模型配置：")
        name = input("配置名称: ").strip() or f"模型{len(self.models)+1}"
        print(f"支持类型: {SUPPORTED_API_TYPES}")
        api_type = input("接口类型: ").strip().lower()
        if api_type not in SUPPORTED_API_TYPES:
            print("类型无效，使用 openai")
            api_type = 'openai'
        model_url = input("模型URL: ").strip()
        model_name = input("模型名称: ").strip()
        api_key = input("API Key: ").strip()
        max_tokens = input("最大Token数[2000]: ").strip()
        temperature = input("温度[0.7]: ").strip()
        timeout = input("超时时间[60]: ").strip()
        m = ModelConfig(
            name=name,
            api_type=api_type,
            model_url=model_url,
            model_name=model_name,
            api_key=api_key,
            max_tokens=int(max_tokens) if max_tokens.isdigit() else 2000,
            temperature=float(temperature) if temperature else 0.7,
            timeout=int(timeout) if timeout.isdigit() else 60
        )
        self.models.append(m)
        self.active_index = len(self.models) - 1
        print(f"已添加并切换到新配置[{self.active_index}] {name}")

    def edit_model(self, idx):
        m = self.models[idx]
        print(f"\n编辑配置[{idx}] {m.name}")
        for field in m.__dataclass_fields__:
            old = getattr(m, field)
            new = input(f"{field} [{old}]: ").strip()
            if new:
                try:
                    if field == 'max_tokens' or field == 'timeout':
                        setattr(m, field, int(new))
                    elif field == 'temperature':
                        setattr(m, field, float(new))
                    else:
                        setattr(m, field, new)
                except Exception as e:
                    print(f"字段 {field} 修改失败: {e}")
        print("修改完成。") 
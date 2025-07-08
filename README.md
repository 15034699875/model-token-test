# 模型Token输出速率测试工具

## 项目简介
本工具用于测试大语言模型API的Token输出速率，支持并发测试、自动报告生成、交互式配置和自检。

---

## 目录结构与文件说明

- `main.py`                —— 统一入口，负责流程控制、交互、异常处理
- `config.py`              —— 配置管理模块，支持加载、保存、交互式修改
- `self_check.py`          —— 自检模块，检查依赖、网络、API Key等
- `model_token_rate_test.py` —— 核心测试逻辑，负责并发请求与报告生成
- `requirements.txt`       —— 依赖包列表
- `config.json`            —— 用户配置文件（自动生成）

> 其余如 `quick_start.py`、`test_tool.py`、`config_example.py` 为历史/演示文件，可忽略。

---

## 安装依赖

建议使用 Python 3.8+，并提前安装依赖：

```bash
pip install -r requirements.txt
```

如遇依赖缺失，程序会在自检时提示。

---

## 配置说明

首次运行或需修改配置时，支持交互式修改：

- `model_url`：模型API地址
- `model_name`：模型名称
- `api_key`：API密钥
- `max_tokens`：最大Token数
- `temperature`：采样温度
- `timeout`：超时时间（秒）

配置会自动保存到 `config.json`，下次启动自动加载。

---

## 使用方法

1. **运行主程序**

```bash
python main.py
```

2. **按提示完成配置、依赖和API自检**

3. **输入并发数列表（如 1,2,4,8,10），回车可用默认**

4. **等待测试完成，自动生成报告和图表**

- 文本报告：`token_rate_report_时间戳.txt`
- 图表报告：`token_rate_chart_时间戳.png`

---

## 常见报错与自检说明

- **依赖缺失**：自检会提示缺少的包名，请按提示 `pip install 包名` 安装。
- **网络异常**：自检会检测API地址连通性，失败时请检查网络或API地址。
- **API Key无效**：自检会检测API Key有效性，失败时请在配置中重新填写。
- **测试中断**：可用 Ctrl+C 中断测试。

---

## 代码结构原则

- 每个文件只负责单一功能，互不混杂。
- 配置、主逻辑、自检、入口完全分离，便于维护和扩展。
- 冗余/演示代码已移除，主流程清晰。

---

## 其他说明

如需自定义测试内容、并发策略等，可在 `model_token_rate_test.py` 中修改 `test_prompts` 或相关逻辑。

如有问题请提交 issue 或联系开发者。 
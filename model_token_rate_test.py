#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型Token输出速率测试工具
支持并发测试、报告生成、结果保存等功能
"""

import asyncio
import aiohttp
import json
import time
import random
import os
from datetime import datetime
from typing import List, Dict, Any
import matplotlib.pyplot as plt
from dataclasses import dataclass
import logging

@dataclass
class TestResult:
    concurrency: int
    total_tokens: int
    total_time: float
    tokens_per_second: float
    success_count: int
    error_count: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float

class TokenRateTester:
    def __init__(self, config, output_dir='outputs'):
        self.config = config
        self.output_dir = output_dir
        self.results: List[TestResult] = []
        self.test_prompts = [
            "请详细描述人工智能的发展历程，从图灵测试开始，到现在的深度学习时代，包括重要的里程碑事件、关键技术突破、以及未来发展趋势。请尽可能详细地阐述每个阶段的特点和影响。",
            "请写一篇关于气候变化的长篇文章，包括全球变暖的原因、影响、解决方案，以及各国在应对气候变化方面的政策和行动。请详细分析科学证据和实际案例。",
            "请详细解释量子计算的基本原理、发展现状、应用前景，以及与传统计算的差异。包括量子比特、量子纠缠、量子算法等核心概念的解释。",
            "请写一篇关于区块链技术的全面介绍，包括其工作原理、应用场景、优缺点分析，以及在不同行业的实际应用案例。请详细说明技术细节和商业价值。",
            "请详细描述机器学习的基本概念、算法分类、应用领域，以及在实际项目中的实施流程。包括监督学习、无监督学习、强化学习等不同类型的详细说明。",
            "请写一篇关于生物技术的长篇文章，包括基因编辑、合成生物学、生物制药等领域的最新进展，以及这些技术对人类社会的潜在影响和伦理考虑。",
            "请详细解释云计算的概念、服务模式、部署模式，以及在企业数字化转型中的作用。包括IaaS、PaaS、SaaS等不同服务模式的详细对比。",
            "请写一篇关于可再生能源的全面分析，包括太阳能、风能、水能、生物质能等不同能源形式的技术特点、发展现状、成本分析，以及在全球能源转型中的作用。",
            "请详细描述物联网技术的基本架构、应用场景、发展趋势，以及在大数据、人工智能时代的地位和作用。包括传感器技术、通信协议、数据处理等关键技术。",
            "请写一篇关于数字经济的深度分析，包括数字化转型、数字支付、电子商务、数字营销等领域的发展现状和未来趋势，以及对企业经营模式的影响。"
        ]
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def get_random_prompt(self) -> str:
        return random.choice(self.test_prompts)

    async def call_model_api(self, session: aiohttp.ClientSession, prompt: str) -> Dict[str, Any]:
        api_type = getattr(self.config, 'api_type', 'openai')
        headers = {"Content-Type": "application/json"}
        if getattr(self.config, 'api_key', None):
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        # 构造不同API类型的请求体
        if api_type in ('openai', 'thirdparty'):
            payload = {
                "model": self.config.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "stream": False
            }
        elif api_type == 'vllm':
            payload = {
                "model": self.config.model_name,
                "prompt": prompt,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "stream": False
            }
        elif api_type == 'ollama':
            payload = {
                "model": self.config.model_name,
                "prompt": prompt,
                "options": {"num_predict": self.config.max_tokens, "temperature": self.config.temperature}
            }
        else:
            return {'success': False, 'error': f'不支持的API类型: {api_type}', 'response_time': 0}
        start_time = time.time()
        try:
            async with session.post(
                self.config.model_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                response_bytes = await response.read()
                end_time = time.time()
                try:
                    response_text = response_bytes.decode('utf-8')
                except Exception:
                    return {'success': False, 'error': '返回内容非UTF-8编码，疑似乱码', 'response_time': end_time - start_time}
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        # 解析不同API类型的返回
                        if api_type in ('openai', 'thirdparty'):
                            content = data['choices'][0]['message']['content']
                            usage = data.get('usage', {})
                            tokens = usage.get('total_tokens', 0)
                        elif api_type == 'vllm':
                            content = data['text'] if 'text' in data else data.get('output', '')
                            tokens = data.get('num_tokens', 0)
                        elif api_type == 'ollama':
                            content = data.get('response', '')
                            tokens = data.get('eval_count', 0)
                        else:
                            content = str(data)
                            tokens = 0
                        # 检查内容是否乱码（简单检测）
                        if '\ufffd' in content:
                            return {'success': False, 'error': '返回内容疑似乱码', 'response_time': end_time - start_time}
                        return {
                            'success': True,
                            'content': content,
                            'tokens': tokens,
                            'response_time': end_time - start_time,
                            'raw_response': response_text
                        }
                    except Exception as e:
                        return {'success': False, 'error': f'解析响应失败: {e}', 'response_time': end_time - start_time}
                else:
                    return {
                        'success': False,
                        'error': f"HTTP {response.status}: {response_text}",
                        'response_time': end_time - start_time
                    }
        except Exception as e:
            end_time = time.time()
            return {
                'success': False,
                'error': str(e),
                'response_time': end_time - start_time
            }

    async def test_concurrency(self, concurrency: int) -> TestResult:
        self.logger.info(f"开始测试并发数: {concurrency}")
        async with aiohttp.ClientSession() as session:
            tasks = [self.call_model_api(session, self.get_random_prompt()) for _ in range(concurrency)]
            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            total_tokens = 0
            success_count = 0
            error_count = 0
            response_times = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    error_count += 1
                    self.logger.error(f"任务 {i} 异常: {response}")
                elif isinstance(response, dict) and response.get('success'):
                    success_count += 1
                    total_tokens += response.get('tokens', 0)
                    response_times.append(response.get('response_time', 0))
                elif isinstance(response, dict):
                    error_count += 1
                    error_msg = response.get('error', '未知错误')
                    self.logger.error(f"任务 {i} 失败: {error_msg}")
                else:
                    error_count += 1
                    self.logger.error(f"任务 {i} 返回了意外的响应类型: {type(response)}")
            total_time = end_time - start_time
            tokens_per_second = total_tokens / total_time if total_time > 0 else 0
            result = TestResult(
                concurrency=concurrency,
                total_tokens=total_tokens,
                total_time=total_time,
                tokens_per_second=tokens_per_second,
                success_count=success_count,
                error_count=error_count,
                avg_response_time=sum(response_times) / len(response_times) if response_times else 0,
                min_response_time=min(response_times) if response_times else 0,
                max_response_time=max(response_times) if response_times else 0
            )
            self.results.append(result)
            self.logger.info(f"并发数 {concurrency} 测试完成: {tokens_per_second:.2f} tokens/s")
            return result

    def generate_report(self, timestamp: str = None):
        if not timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_text = self.generate_text_report()
        os.makedirs(self.output_dir, exist_ok=True)
        report_filename = os.path.join(self.output_dir, f"token_rate_report_{timestamp}.txt")
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_text)
        self.generate_chart_report(str(timestamp))
        self.logger.info(f"报告已生成: {report_filename}")
        self.logger.info(f"图表已生成: {os.path.join(self.output_dir, f'token_rate_chart_{timestamp}.png')}")
        return report_text

    def generate_text_report(self) -> str:
        report = []
        report.append("=" * 60)
        report.append("模型Token输出速率测试报告")
        report.append("=" * 60)
        report.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"模型URL: {self.config.model_url}")
        report.append(f"模型名称: {self.config.model_name}")
        report.append(f"最大Token数: {self.config.max_tokens}")
        report.append(f"温度参数: {self.config.temperature}")
        report.append("")
        total_requests = sum(r.success_count + r.error_count for r in self.results)
        total_success = sum(r.success_count for r in self.results)
        total_errors = sum(r.error_count for r in self.results)
        success_rate = (total_success / total_requests * 100) if total_requests > 0 else 0
        report.append("总体统计:")
        report.append(f"  总请求数: {total_requests}")
        report.append(f"  成功请求: {total_success}")
        report.append(f"  失败请求: {total_errors}")
        report.append(f"  成功率: {success_rate:.2f}%")
        report.append("")
        report.append("详细测试结果:")
        report.append("-" * 60)
        report.append(f"{'并发数':<8} {'Token/s':<12} {'总Token':<10} {'总时间(s)':<12} {'成功率':<10} {'平均响应时间(s)':<15}")
        report.append("-" * 60)
        for result in self.results:
            total_requests = result.success_count + result.error_count
            success_rate = (result.success_count / total_requests * 100) if total_requests > 0 else 0
            report.append(
                f"{result.concurrency:<8} "
                f"{result.tokens_per_second:<12.2f} "
                f"{result.total_tokens:<10} "
                f"{result.total_time:<12.2f} "
                f"{success_rate:<10.2f}% "
                f"{result.avg_response_time:<15.2f}"
            )
        report.append("-" * 60)
        report.append("")
        report.append("性能分析:")
        best_concurrency = max(self.results, key=lambda x: x.tokens_per_second)
        report.append(f"  最佳并发数: {best_concurrency.concurrency} (Token/s: {best_concurrency.tokens_per_second:.2f})")
        if len(self.results) > 1:
            baseline = self.results[0]
            scalability = []
            for result in self.results[1:]:
                expected_tokens = baseline.tokens_per_second * result.concurrency
                actual_tokens = result.tokens_per_second * result.concurrency
                efficiency = (actual_tokens / expected_tokens * 100) if expected_tokens > 0 else 0
                scalability.append(f"  并发数{result.concurrency}: 效率 {efficiency:.1f}%")
            report.append("  扩展性分析:")
            for s in scalability:
                report.append(s)
        report.append("")
        report.append("=" * 60)
        return "\n".join(report)

    def generate_chart_report(self, timestamp: str):
        if not self.results:
            return
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'模型Token输出速率测试报告 - {self.config.model_name}', fontsize=16)
        concurrency_levels = [r.concurrency for r in self.results]
        tokens_per_second = [r.tokens_per_second for r in self.results]
        total_tokens = [r.total_tokens for r in self.results]
        avg_response_times = [r.avg_response_time for r in self.results]
        success_rates = [(r.success_count / (r.success_count + r.error_count) * 100) if (r.success_count + r.error_count) > 0 else 0 for r in self.results]
        ax1.plot(concurrency_levels, tokens_per_second, 'bo-', linewidth=2, markersize=8)
        ax1.set_xlabel('并发数')
        ax1.set_ylabel('Token输出速率 (tokens/s)')
        ax1.set_title('Token输出速率 vs 并发数')
        ax1.grid(True, alpha=0.3)
        ax2.bar(concurrency_levels, total_tokens, color='skyblue', alpha=0.7)
        ax2.set_xlabel('并发数')
        ax2.set_ylabel('总Token数')
        ax2.set_title('总Token数 vs 并发数')
        ax2.grid(True, alpha=0.3)
        ax3.plot(concurrency_levels, avg_response_times, 'ro-', linewidth=2, markersize=8)
        ax3.set_xlabel('并发数')
        ax3.set_ylabel('平均响应时间 (s)')
        ax3.set_title('平均响应时间 vs 并发数')
        ax3.grid(True, alpha=0.3)
        ax4.bar(concurrency_levels, success_rates, color='lightgreen', alpha=0.7)
        ax4.set_xlabel('并发数')
        ax4.set_ylabel('成功率 (%)')
        ax4.set_title('成功率 vs 并发数')
        ax4.set_ylim(0, 100)
        ax4.grid(True, alpha=0.3)
        plt.tight_layout()
        chart_path = os.path.join(self.output_dir, f'token_rate_chart_{timestamp}.png')
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close() 
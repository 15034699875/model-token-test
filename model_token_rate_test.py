#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型Token输出速率测试工具
支持并发测试、报告生成、结果保存等功能
"""

import openai
import time
import random
import os
from datetime import datetime
from typing import List, Dict, Any
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
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
    first_token_timeouts: list = field(default_factory=list)
    avg_first_token_timeout: float = 0.0
    min_first_token_timeout: float = 0.0
    max_first_token_timeout: float = 0.0

class TokenRateTester:
    def __init__(self, config, output_dir='outputs', logger=None):
        self.config = config
        self.output_dir = output_dir
        self.logger = logger
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

    def call_model_api(self, prompt: str) -> dict:
        api_key = self.config.api_key if self.config.api_type in ("openai", "thirdparty") else None
        # 自动推断base_url（去除最后一级路径即可）
        from urllib.parse import urlparse
        parsed = urlparse(self.config.model_url)
        base_url = self.config.model_url.rsplit("/", 2)[0] if self.config.model_url.endswith("/completions") else self.config.model_url.rsplit("/", 1)[0]
        client = openai.OpenAI(api_key=api_key or None, base_url=base_url)
        start_time = time.time()
        first_token_time = None
        total_tokens = 0
        content = ''
        try:
            stream = client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                stream=True
            )
            for chunk in stream:
                token_piece = getattr(chunk.choices[0].delta, 'content', '')
                if token_piece:
                    if first_token_time is None:
                        first_token_time = time.time()
                    content += token_piece
                    total_tokens += 1
            end_time = time.time()
            if first_token_time is None:
                first_token_time = end_time
            return {
                'success': True,
                'content': content,
                'tokens': total_tokens,
                'response_time': end_time - start_time,
                'first_token_timeout': first_token_time - start_time,
                'raw_response': '[streamed]'
            }
        except Exception as e:
            end_time = time.time()
            return {
                'success': False,
                'error': str(e),
                'response_time': end_time - start_time
            }

    def test_concurrency(self, concurrency: int) -> TestResult:
        self.logger.info(f"开始测试并发数: {concurrency}")
        import concurrent.futures
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(self.call_model_api, self.get_random_prompt()) for _ in range(concurrency)]
            responses = [f.result() for f in futures]
        end_time = time.time()
        total_tokens = 0
        success_count = 0
        error_count = 0
        response_times = []
        first_token_timeouts = []
        error_msgs = []
        for i, response in enumerate(responses):
            if isinstance(response, dict) and response.get('success'):
                success_count += 1
                total_tokens += response.get('tokens', 0)
                response_times.append(response.get('response_time', 0))
                first_token_timeouts.append(response.get('first_token_timeout', 0))
            elif isinstance(response, dict):
                error_count += 1
                error_msg = response.get('error', '未知错误')
                self.logger.error(f"任务 {i} 失败: {error_msg}")
                error_msgs.append(f"任务 {i} 失败: {error_msg}")
            else:
                error_count += 1
                self.logger.error(f"任务 {i} 返回了意外的响应类型: {type(response)}")
                error_msgs.append(f"任务 {i} 返回了意外的响应类型: {type(response)}")
        total_time = end_time - start_time
        tokens_per_second = total_tokens / total_time if total_time > 0 else 0
        avg_first_token_timeout = sum(first_token_timeouts) / len(first_token_timeouts) if first_token_timeouts else 0
        min_first_token_timeout = min(first_token_timeouts) if first_token_timeouts else 0
        max_first_token_timeout = max(first_token_timeouts) if first_token_timeouts else 0
        result = TestResult(
            concurrency=concurrency,
            total_tokens=total_tokens,
            total_time=total_time,
            tokens_per_second=tokens_per_second,
            success_count=success_count,
            error_count=error_count,
            avg_response_time=sum(response_times) / len(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            first_token_timeouts=first_token_timeouts,
            avg_first_token_timeout=avg_first_token_timeout,
            min_first_token_timeout=min_first_token_timeout,
            max_first_token_timeout=max_first_token_timeout
        )
        self.results.append(result)
        self.logger.info(f"并发数 {concurrency} 测试完成: {tokens_per_second:.2f} tokens/s")
        if error_msgs:
            self.logger.error(f"并发数 {concurrency} 失败任务详情：\n" + "\n".join(error_msgs))
            if success_count == 0:
                self.logger.error(f"并发数 {concurrency} 下全部任务失败，测试已终止，请检查API Key、网络、模型服务等配置。")
                raise RuntimeError(f"并发数 {concurrency} 下全部任务失败，测试终止。")
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
        report.append(f"{'并发数':<8} {'Token/s':<12} {'总Token':<10} {'总时间(s)':<12} {'成功率':<10} {'平均响应时间(s)':<15} {'首Token超时(s)':<15}")
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
                f"{result.avg_response_time:<15.2f} "
                f"{result.avg_first_token_timeout:<15.2f}"
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
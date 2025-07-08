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
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from dataclasses import dataclass
import logging

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestConfig:
    """测试配置"""
    model_url: str = "http://localhost:8000/v1/chat/completions"
    model_name: str = "gpt-3.5-turbo"
    api_key: str = "your-api-key-here"
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 60

@dataclass
class TestResult:
    """测试结果"""
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
    """Token输出速率测试器"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.results: List[TestResult] = []
        
        # 长文本测试问题模板
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
    
    def get_random_prompt(self) -> str:
        """获取随机测试问题"""
        return random.choice(self.test_prompts)
    
    async def call_model_api(self, session: aiohttp.ClientSession, prompt: str) -> Dict[str, Any]:
        """调用模型API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }
        
        payload = {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "stream": False
        }
        
        start_time = time.time()
        try:
            async with session.post(
                self.config.model_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                response_text = await response.text()
                end_time = time.time()
                
                if response.status == 200:
                    response_data = json.loads(response_text)
                    content = response_data['choices'][0]['message']['content']
                    usage = response_data.get('usage', {})
                    tokens = usage.get('total_tokens', 0)
                    
                    return {
                        'success': True,
                        'content': content,
                        'tokens': tokens,
                        'response_time': end_time - start_time,
                        'raw_response': response_text
                    }
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
        """测试指定并发数下的性能"""
        logger.info(f"开始测试并发数: {concurrency}")
        
        async with aiohttp.ClientSession() as session:
            # 创建并发任务
            tasks = []
            for i in range(concurrency):
                prompt = self.get_random_prompt()
                task = self.call_model_api(session, prompt)
                tasks.append(task)
            
            # 执行并发请求
            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # 分析结果
            total_tokens = 0
            success_count = 0
            error_count = 0
            response_times = []
            
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    error_count += 1
                    logger.error(f"任务 {i} 异常: {response}")
                elif isinstance(response, dict) and response.get('success'):
                    success_count += 1
                    total_tokens += response.get('tokens', 0)
                    response_times.append(response.get('response_time', 0))
                    
                    # 保存响应内容
                    content = response.get('content', '')
                    if content:
                        self.save_response_content(i, concurrency, content)
                elif isinstance(response, dict):
                    error_count += 1
                    error_msg = response.get('error', '未知错误')
                    logger.error(f"任务 {i} 失败: {error_msg}")
                else:
                    error_count += 1
                    logger.error(f"任务 {i} 返回了意外的响应类型: {type(response)}")
            
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
            logger.info(f"并发数 {concurrency} 测试完成: {tokens_per_second:.2f} tokens/s")
            
            return result
    
    def save_response_content(self, task_id: int, concurrency: int, content: str):
        """保存响应内容到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"responses/concurrency_{concurrency}_task_{task_id}_{timestamp}.txt"
        
        os.makedirs("responses", exist_ok=True)
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"并发数: {concurrency}\n")
                f.write(f"任务ID: {task_id}\n")
                f.write(f"时间戳: {timestamp}\n")
                f.write(f"内容长度: {len(content)} 字符\n")
                f.write("-" * 50 + "\n")
                f.write(content)
        except Exception as e:
            logger.error(f"保存响应内容失败: {e}")
    
    async def run_all_tests(self):
        """运行所有并发测试"""
        concurrency_levels = [1, 2, 4, 8, 10]
        
        logger.info("开始Token输出速率测试")
        logger.info(f"模型URL: {self.config.model_url}")
        logger.info(f"模型名称: {self.config.model_name}")
        
        for concurrency in concurrency_levels:
            try:
                await self.test_concurrency(concurrency)
                # 添加间隔避免API限制
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"并发数 {concurrency} 测试失败: {e}")
    
    def generate_report(self):
        """生成测试报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 生成文本报告
        report_text = self.generate_text_report()
        report_filename = f"token_rate_report_{timestamp}.txt"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        # 生成图表报告
        self.generate_chart_report(timestamp)
        
        logger.info(f"报告已生成: {report_filename}")
        logger.info(f"图表已生成: token_rate_chart_{timestamp}.png")
        
        return report_text
    
    def generate_text_report(self) -> str:
        """生成文本格式的报告"""
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
        
        # 总体统计
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
        
        # 详细结果
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
        
        # 性能分析
        report.append("性能分析:")
        best_concurrency = max(self.results, key=lambda x: x.tokens_per_second)
        report.append(f"  最佳并发数: {best_concurrency.concurrency} (Token/s: {best_concurrency.tokens_per_second:.2f})")
        
        if len(self.results) > 1:
            # 计算扩展性
            baseline = self.results[0]  # 并发数1作为基准
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
        """生成图表报告"""
        if not self.results:
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'模型Token输出速率测试报告 - {self.config.model_name}', fontsize=16)
        
        # 提取数据
        concurrency_levels = [r.concurrency for r in self.results]
        tokens_per_second = [r.tokens_per_second for r in self.results]
        total_tokens = [r.total_tokens for r in self.results]
        avg_response_times = [r.avg_response_time for r in self.results]
        success_rates = [(r.success_count / (r.success_count + r.error_count) * 100) if (r.success_count + r.error_count) > 0 else 0 for r in self.results]
        
        # 1. Token输出速率 vs 并发数
        ax1.plot(concurrency_levels, tokens_per_second, 'bo-', linewidth=2, markersize=8)
        ax1.set_xlabel('并发数')
        ax1.set_ylabel('Token输出速率 (tokens/s)')
        ax1.set_title('Token输出速率 vs 并发数')
        ax1.grid(True, alpha=0.3)
        
        # 2. 总Token数 vs 并发数
        ax2.bar(concurrency_levels, total_tokens, color='skyblue', alpha=0.7)
        ax2.set_xlabel('并发数')
        ax2.set_ylabel('总Token数')
        ax2.set_title('总Token数 vs 并发数')
        ax2.grid(True, alpha=0.3)
        
        # 3. 平均响应时间 vs 并发数
        ax3.plot(concurrency_levels, avg_response_times, 'ro-', linewidth=2, markersize=8)
        ax3.set_xlabel('并发数')
        ax3.set_ylabel('平均响应时间 (s)')
        ax3.set_title('平均响应时间 vs 并发数')
        ax3.grid(True, alpha=0.3)
        
        # 4. 成功率 vs 并发数
        ax4.bar(concurrency_levels, success_rates, color='lightgreen', alpha=0.7)
        ax4.set_xlabel('并发数')
        ax4.set_ylabel('成功率 (%)')
        ax4.set_title('成功率 vs 并发数')
        ax4.set_ylim(0, 100)
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'token_rate_chart_{timestamp}.png', dpi=300, bbox_inches='tight')
        plt.close()

def main():
    """主函数"""
    print("模型Token输出速率测试工具")
    print("=" * 50)
    
    # 配置测试参数
    config = TestConfig()
    
    # 可以在这里修改配置
    # config.model_url = "http://your-model-server:8000/v1/chat/completions"
    # config.model_name = "your-model-name"
    # config.api_key = "your-api-key"
    
    print(f"当前配置:")
    print(f"  模型URL: {config.model_url}")
    print(f"  模型名称: {config.model_name}")
    print(f"  最大Token数: {config.max_tokens}")
    print(f"  温度参数: {config.temperature}")
    print()
    
    # 确认配置
    confirm = input("是否使用当前配置开始测试? (y/n): ").lower().strip()
    if confirm != 'y':
        print("请修改配置后重新运行程序")
        return
    
    # 创建测试器并运行测试
    tester = TokenRateTester(config)
    
    try:
        # 运行异步测试
        asyncio.run(tester.run_all_tests())
        
        # 生成报告
        report = tester.generate_report()
        
        print("\n" + "=" * 50)
        print("测试完成！")
        print("=" * 50)
        print(report)
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        logger.error(f"测试失败: {e}")

if __name__ == "__main__":
    main() 
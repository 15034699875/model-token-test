import asyncio
import os
import sys
import logging
from datetime import datetime
from config import ConfigManager
from self_check import run_self_check
from model_token_rate_test import TokenRateTester

OUTPUT_DIR = 'outputs'
LOG_FILE = os.path.join(OUTPUT_DIR, f'run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# 日志初始化
os.makedirs(OUTPUT_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def print_banner():
    logger.info("\n==============================")
    logger.info("  模型Token输出速率测试工具  ")
    logger.info("==============================\n")

def safe_self_check(model_cfg):
    try:
        run_self_check(model_cfg)
        return True
    except SystemExit:
        logger.error("自检未通过，禁止进入测试流程。请检查配置后重试。")
        return False
    except Exception as e:
        logger.error(f"自检异常: {e}")
        return False

def main():
    print_banner()
    # 加载配置
    config_mgr = ConfigManager.load()
    while True:
        logger.info("1. 配置管理  2. 开始测试  3. 退出")
        op = input("请选择操作: ").strip()
        if op == '1':
            config_mgr.interactive_menu()
            # 配置变更后自动自检
            model_cfg = config_mgr.models[config_mgr.active_index]
            logger.info(f"配置变更后对当前模型[{model_cfg.name}]进行自检...")
            if not safe_self_check(model_cfg):
                continue
        elif op == '2':
            model_cfg = config_mgr.models[config_mgr.active_index]
            logger.info(f"\n当前模型配置: [{config_mgr.active_index}] {model_cfg.name} | 类型: {model_cfg.api_type}")
            for field in model_cfg.__dataclass_fields__:
                logger.info(f"  {field}: {getattr(model_cfg, field)}")
            logger.info("\n[步骤1] 正在自检...")
            if not safe_self_check(model_cfg):
                continue
            logger.info("[步骤2] 请输入并发数列表（如 1,2,4,8,10，回车默认 [1,2,4,8,10]）")
            default_levels = [1, 2, 4, 8, 10]
            levels_input = input("并发数: ").strip()
            if levels_input:
                try:
                    concurrency_levels = [int(x) for x in levels_input.split(',') if x.strip().isdigit()]
                except Exception:
                    logger.warning("输入格式有误，使用默认并发数列表。")
                    concurrency_levels = default_levels
            else:
                concurrency_levels = default_levels
            logger.info("\n[步骤3] 开始Token输出速率测试\n")
            try:
                tester = TokenRateTester(model_cfg, output_dir=OUTPUT_DIR, logger=logger)
                for concurrency in concurrency_levels:
                    asyncio.run(tester.test_concurrency(concurrency))
                    asyncio.run(asyncio.sleep(2))
                report = tester.generate_report()
                logger.info("\n==============================")
                logger.info("测试完成！报告摘要：")
                logger.info("==============================")
                logger.info(report)
                logger.info(f"\n所有输出结果已保存到: {os.path.abspath(OUTPUT_DIR)}\n")
            except Exception as e:
                logger.error(f"测试过程中发生错误: {e}")
                logger.info(f"详细日志请查看: {LOG_FILE}")
        elif op == '3':
            logger.info("感谢使用，再见！")
            break
        else:
            logger.warning("无效操作，请重新选择。\n")

if __name__ == "__main__":
    main() 
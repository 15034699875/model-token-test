import asyncio
import os
from config import ConfigManager
from self_check import run_self_check
from model_token_rate_test import TokenRateTester

OUTPUT_DIR = 'outputs'

def print_banner():
    print("\n==============================")
    print("  模型Token输出速率测试工具  ")
    print("==============================\n")

def main():
    print_banner()
    # 加载配置
    config_mgr = ConfigManager.load()
    while True:
        print("1. 配置管理  2. 开始测试  3. 退出")
        op = input("请选择操作: ").strip()
        if op == '1':
            config_mgr.interactive_menu()
        elif op == '2':
            model_cfg = config_mgr.models[config_mgr.active_index]
            print(f"\n当前模型配置: [{config_mgr.active_index}] {model_cfg.name} | 类型: {model_cfg.api_type}")
            for field in model_cfg.__dataclass_fields__:
                print(f"  {field}: {getattr(model_cfg, field)}")
            print("\n[步骤1] 正在自检...")
            run_self_check(model_cfg)
            print("[步骤2] 请输入并发数列表（如 1,2,4,8,10，回车默认 [1,2,4,8,10]）")
            default_levels = [1, 2, 4, 8, 10]
            levels_input = input("并发数: ").strip()
            if levels_input:
                try:
                    concurrency_levels = [int(x) for x in levels_input.split(',') if x.strip().isdigit()]
                except Exception:
                    print("输入格式有误，使用默认并发数列表。")
                    concurrency_levels = default_levels
            else:
                concurrency_levels = default_levels
            print("\n[步骤3] 开始Token输出速率测试\n")
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            try:
                tester = TokenRateTester(model_cfg, output_dir=OUTPUT_DIR)
                for concurrency in concurrency_levels:
                    asyncio.run(tester.test_concurrency(concurrency))
                    asyncio.run(asyncio.sleep(2))
                report = tester.generate_report()
                print("\n==============================")
                print("测试完成！报告摘要：")
                print("==============================")
                print(report)
                print(f"\n所有输出结果已保存到: {os.path.abspath(OUTPUT_DIR)}\n")
            except KeyboardInterrupt:
                print("\n测试被用户中断")
            except Exception as e:
                print(f"\n测试过程中发生错误: {e}")
        elif op == '3':
            print("感谢使用，再见！")
            break
        else:
            print("无效操作，请重新选择。\n")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-

# Copyright (c) 2025 shmilee

import os
import sys
import argparse
from pathlib import Path

# 导入服务器启动函数
from .server import run_server


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description="图片分析系统服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s ./App-DescTags/config.yaml
  %(prog)s /path/to/your/config.yaml
  
配置文件说明:
  配置文件应为 YAML 格式，包含服务器配置和 AI 分析器配置。
  参考示例: App-DescTags/config.yaml
"""
    )
    parser.add_argument("config", type=str,
                        help="配置文件路径 (YAML 格式)")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"错误: 配置文件不存在: {config_path}")
        print("请使用 --help 查看使用说明")
        sys.exit(1)
    if not config_path.is_file():
        print(f"错误: 配置文件不是文件: {config_path}")
        sys.exit(1)
    # 检查文件扩展名
    if config_path.suffix.lower() not in ['.yaml', '.yml']:
        print(f"警告: 配置文件可能不是 YAML 格式: {config_path}")
        choice = input("是否继续? (y/N): ").strip().lower()
        if choice != 'y':
            print("操作已取消")
            sys.exit(0)
    print(f"使用配置文件: {config_path.absolute()}")
    # 启动服务器
    run_server(str(config_path.absolute()))


if __name__ == "__main__":
    main()

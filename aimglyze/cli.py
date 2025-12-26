# -*- coding: utf-8 -*-

# Copyright (c) 2025 shmilee

import os
import sys
import argparse
from pathlib import Path

# 导入服务器启动函数
from .server import run_server, cleanup_cache, cleanup_low_confidence_uploads


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description="图片分析系统服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s server ./App-DescTags/config.yaml
  %(prog)s clean-cache ./App-DescTags/config.yaml
  %(prog)s clean-uploads ./App-DescTags/config.yaml --confidence 0.5
  
子命令说明:
  server: 启动服务器
  clean-cache: 清理过期缓存
  clean-uploads: 清理低置信度的上传文件
"""
    )

    subparsers = parser.add_subparsers(dest='command', help='子命令')
    # server 子命令
    server_parser = subparsers.add_parser('server', help='启动服务器')
    server_parser.add_argument("config", type=str,
                               help="配置文件路径 (YAML 格式)")
    # clean-cache 子命令
    cache_parser = subparsers.add_parser('clean-cache', help='清理过期缓存')
    cache_parser.add_argument("config", type=str,
                              help="配置文件路径 (YAML 格式)")
    # clean-uploads 子命令
    uploads_parser = subparsers.add_parser('clean-uploads', help='清理低置信度的上传文件')
    uploads_parser.add_argument("config", type=str,
                                help="配置文件路径 (YAML 格式)")
    uploads_parser.add_argument("--confidence", type=float, default=0.5,
                                help="置信度阈值，低于此值的文件将被清理 (默认: 0.5)")
    uploads_parser.add_argument("--dry-run", action="store_true",
                                help="模拟运行，不实际删除文件")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    # 检查配置文件
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"错误: 配置文件不存在: {config_path}")
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

    # 执行相应命令
    if args.command == 'server':
        # 启动服务器
        run_server(str(config_path.absolute()))
    elif args.command == 'clean-cache':
        # 清理缓存
        print("清理过期缓存...")
        cleanup_cache(str(config_path.absolute()))
        print("缓存清理完成")
    elif args.command == 'clean-uploads':
        # 清理低置信度的上传文件
        print(f"清理置信度低于 {args.confidence} 的上传文件...")
        if args.dry_run:
            print("模拟运行模式 - 不会实际删除文件")
        cleanup_low_confidence_uploads(str(config_path.absolute()),
                                       args.confidence, args.dry_run)
        print("上传文件清理完成")


if __name__ == "__main__":
    main()

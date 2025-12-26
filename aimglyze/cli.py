# -*- coding: utf-8 -*-

# Copyright (c) 2025 shmilee

import os
import sys
import argparse
from pathlib import Path
import importlib.resources as resources

# 导入服务器启动函数
from .server import run_server, cleanup_cache, cleanup_low_confidence_uploads

# 应用别名映射
APP_ALIASES = {
    'desc-tags': 'App-DescTags/config.yaml',
    'task-score': 'App-TaskScore/config.yaml',
}


def resolve_config_path(config_arg: str):
    """
    解析配置文件路径：
    1. 如果是别名，返回包内的配置文件路径
    2. 如果是文件路径，返回绝对路径
    """
    # 检查是否是别名
    if config_arg.lower() in APP_ALIASES:
        alias = config_arg.lower()
        resource_path = APP_ALIASES[alias]
        # 尝试从包资源中获取
        try:
            with resources.path('aimglyze.apps', resource_path) as config_path:
                if config_path.exists():
                    print(f"找到应用别名 '{alias}' -> {config_path}")
                    return str(config_path)
                else:
                    raise FileNotFoundError(f"应用配置未找到: {config_path}")
        except Exception as e:
            print(f"无法加载应用配置 '{alias}': {str(e)}")
            # 尝试在开发环境中查找
            dev_path = Path(__file__).parent.parent / 'apps' / resource_path
            if dev_path.exists():
                print(f"在开发环境中找到: {dev_path}")
                return str(dev_path)
            else:
                raise FileNotFoundError(f"应用配置未找到: {resource_path}")
    # 否则当作文件路径处理
    config_path = Path(config_arg)
    if not config_path.exists():
        # 尝试在当前目录下查找
        if not config_path.is_absolute():
            current_dir = Path.cwd() / config_path
            if current_dir.exists():
                config_path = current_dir
    return str(config_path.absolute())


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description="图片分析系统服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s server desc-tags                    # 使用App-DescTags应用别名
  %(prog)s server task-score                   # 使用App-TaskScore应用别名
  %(prog)s server ./App-DescTags/config.yaml   # 使用配置文件路径
  %(prog)s clean-cache desc-tags               # 清理缓存
  %(prog)s clean-uploads task-score            # 清理低置信度的上传文件

支持的别名:
  desc-tags     - App-DescTags图片分析应用
  task-score    - App-TaskScore学生评价表分析应用
"""
    )

    subparsers = parser.add_subparsers(dest='command', help='子命令')
    # server 子命令
    server_parser = subparsers.add_parser('server', help='启动服务器')
    server_parser.add_argument("config", type=str,
                               help="配置文件路径或应用别名 (desc-tags, task-score)")
    # clean-cache 子命令
    cache_parser = subparsers.add_parser('clean-cache', help='清理过期缓存')
    cache_parser.add_argument("config", type=str,
                              help="配置文件路径或应用别名")
    # clean-uploads 子命令
    uploads_parser = subparsers.add_parser('clean-uploads', help='清理低置信度的上传文件')
    uploads_parser.add_argument("config", type=str,
                                help="配置文件路径或应用别名")
    uploads_parser.add_argument("--confidence", type=float, default=0.5,
                                help="置信度阈值，低于此值的文件将被清理 (默认: 0.5)")
    uploads_parser.add_argument("--dry-run", action="store_true",
                                help="模拟运行，不实际删除文件")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        # 解析配置文件路径
        config_path = resolve_config_path(args.config)
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)
    # 检查配置文件是否存在
    if not os.path.exists(config_path):
        print(f"错误: 配置文件不存在: {config_path}")
        sys.exit(1)
    # 检查文件扩展名
    config_path_obj = Path(config_path)
    if config_path_obj.suffix.lower() not in ['.yaml', '.yml']:
        print(f"警告: 配置文件可能不是 YAML 格式: {config_path_obj}")
        choice = input("是否继续? (y/N): ").strip().lower()
        if choice != 'y':
            print("操作已取消")
            sys.exit(0)

    # 执行相应命令
    if args.command == 'server':
        # 启动服务器
        run_server(config_path)
    elif args.command == 'clean-cache':
        # 清理缓存
        print("清理过期缓存...")
        cleanup_cache(config_path)
        print("缓存清理完成")
    elif args.command == 'clean-uploads':
        # 清理低置信度的上传文件
        print(f"清理置信度低于 {args.confidence} 的上传文件...")
        if args.dry_run:
            print("模拟运行模式 - 不会实际删除文件")
        cleanup_low_confidence_uploads(config_path,
                                       args.confidence, args.dry_run)
        print("上传文件清理完成")


if __name__ == "__main__":
    main()

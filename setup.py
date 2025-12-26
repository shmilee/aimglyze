# -*- coding: utf-8 -*-

# Copyright (c) 2025 shmilee

from setuptools import setup, find_packages
import os

# 读取README文件
with open("./README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取requirements.txt
install_requires = []
if os.path.exists("./requirements.txt"):
    with open("./requirements.txt", "r", encoding="utf-8") as f:
        install_requires = [
            line.strip() for line in f if line.strip() and not line.startswith("#")]


setup(
    name="aimglyze",
    version="0.2.3",
    author="shmilee",
    author_email="shmilee.zju@gmail.com",
    description="AI图片分析器，支持多模型（DeepSeek, Gemini, ZhipuAI等）",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shmilee/aimglyze",
    # package_dir={'aimglyze': 'aimglyze'},
    packages=["aimglyze"],
    # include_package_data=True, # Warning: Package 'aimglyze.apps' is absent
    package_data={
        'aimglyze': [
            "apps/**/*.html",
            "apps/**/*.css",
            "apps/**/*.js",
            "apps/**/*.ico",
            "apps/**/*.json",
            "apps/**/*.yaml",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Multimedia :: Graphics",
        "Intended Audience :: Developers",
    ],
    python_requires=">=3.10",
    install_requires=install_requires,
    extras_require={
        "full": [
            "google-genai>=0.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "aimglyze=aimglyze.cli:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/shmilee/aimglyze/issues",
        "Source": "https://github.com/shmilee/aimglyze",
    },
    keywords=[
        "ai",
        "image-analysis",
        "deepseek",
        "gemini",
        "zhipuai",
        "multimodal",
    ],
    license="MIT",
)

# AI 图像分析系统 (aimglyze)

一个基于 AI 的图像分析与识别应用框架，支持灵活的多应用架构。

## 名称含义

**aimglyze** 是三个英文单词的组合：
- **AI**：人工智能，代表系统的核心技术
- **image**：图像，代表系统的主要处理对象
- **analyze**：分析，代表系统的核心功能

组合意为 **"AI 图像分析系统"**，准确表达了项目的核心定位。

## 应用概览

### 1. App-DescTags (图片分析应用)
**功能**: 通用图片分析与描述生成
- 上传任意图片，AI 自动分析图片内容
- 生成图片名称、详细描述和相关标签
- 支持图片预览、缩略图查看
- 适用于图片内容识别、标签生成等通用场景

### 2. App-TaskScore (学生评价表分析应用)
**功能**: 学生评价表分析与评估
- 上传学生评价表图片，AI 自动解析评分数据
- 生成多维度的学习分析报告（分数概览、优势分析、改进建议）
- 可视化数据展示（雷达图、分数对比）
- 专为教育评估设计的业务应用

## 系统架构

### 后端核心

后端是系统的核心部分，采用模块化设计，支持灵活扩展：

#### 1. 分析器模块 (`analyzer.py`)
- **多AI服务商支持**：集成了智谱AI、Google Gemini、DeepSeek等多种AI服务
- **统一的API接口**：所有分析器实现相同的接口，便于切换和扩展
- **流式输出处理**：支持AI模型的流式响应，实时显示分析过程
- **JSON修复机制**：自动修复AI返回的JSON格式问题，提高鲁棒性

#### 2. 服务器模块 (`server.py`)
- **灵活的配置系统**：通过YAML配置文件管理应用设置
- **智能文件管理**：基于文件哈希值避免重复保存，节省存储空间
- **结果缓存机制**：缓存分析结果1小时，避免重复分析相同图片
- **健康检查接口**：实时监控服务器状态，确保服务可用性

#### 3. 配置系统
- **应用独立配置**：每个应用有自己的配置文件，互不影响
- **运行时动态加载**：支持热修改配置，无需重启服务器
- **环境变量集成**：支持通过环境变量配置API密钥等敏感信息

### 前端架构

系统采用前后端分离架构，前端作为静态资源由后端服务器提供：
- **响应式设计**：自动适配桌面端和移动端
- **主题支持**：支持亮色/暗色主题切换
- **模块化组件**：可复用的UI组件，便于开发新应用

## 功能特性

### 核心功能
- 📷 支持图片上传（拖拽或选择文件）
- 🤖 基于AI自动分析图片内容
- 📊 动态展示分析结果
- 🎨 支持亮色/暗色主题切换
- 📱 响应式设计，支持移动设备
- 💾 结果导出为JSON格式
- 🖨️ 打印优化支持
- 🔄 实时服务器状态监控

### 业务应用特有功能 (App-TaskScore)
- 📋 评价表结构化解析
- 🎯 多维度的技能评估
- 📈 雷达图可视化分析
- 📝 详细的学习分析报告
- 🏆 优势与改进建议识别

## 项目结构

```
.
├── aimglyze/                  # 核心Python包（后端）
│   ├── analyzer.py            # AI分析器（支持多平台）
│   ├── server.py              # 后端服务器
│   ├── cli.py                 # 命令行接口
│   └── __init__.py
├── App-DescTags/              # 图片分析应用
│   ├── config.yaml            # 应用配置文件
│   ├── frontend/              # 前端文件
│   └── sample-msg.json        # 示例数据
├── App-TaskScore/             # 学生评价表分析应用
│   ├── config.yaml            # 应用配置文件
│   ├── frontend/              # 前端文件
│   ├── sample-msg.json        # 示例数据
│   └── uploads/               # 上传文件存储目录
├── logos/                     # 应用图标资源
├── requirements.txt
├── setup.py
├── MANIFEST.in
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 根据使用的AI服务商设置API密钥环境变量
# 智谱AI (默认配置)
export ZAI_API_KEY=your_zhipu_api_key_here

# DeepSeek
export DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Google Gemini
export GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. 启动应用

#### 启动 App-DescTags (图片分析应用)
```bash
python -m aimglyze.cli App-DescTags/config.yaml
```
访问: http://localhost:8080

#### 启动 App-TaskScore (学生评价表分析应用)
```bash
python -m aimglyze.cli App-TaskScore/config.yaml
```
访问: http://localhost:8080

### 3. 修改配置

编辑对应的 `config.yaml` 文件，可调整：

**AI模型参数** (支持多种AI服务商):
- `ZhipuAnalyzer` - 智谱AI (默认)
- `DeepseekAnalyzer` - DeepSeek
- `GeminiAnalyzer` - Google Gemini
- 其他兼容 OpenAI API 的服务

**服务器配置**:
- `host`: 服务器监听地址 (默认: 127.0.0.1)
- `port`: 服务器端口 (默认: 8080)
- `save_upload`: 是否保存上传文件
- `upload_dir`: 上传文件存储目录
- `max_upload_size`: 最大上传文件大小 (MB)

**前端设置**:
- `title`: 页面标题
- `theme`: 主题 (light/dark)
- `show_sample_data`: 是否显示"加载示例"按钮

## API 接口

两个应用共享相同的后端API接口：

* `GET /api/config`: 获取系统配置
* `GET /api/sample`: 获取示例数据
* `POST /api/analyze`: 上传图片并分析
* `GET /api/results/{cache_key}`: 获取缓存的分析结果
* `GET /api/health`: 服务器健康检查

## 扩展开发

### 创建新应用

1. **复制应用模板**：复制现有应用目录作为基础
2. **修改配置文件**：调整AI提示词、前端配置等
3. **定制前端界面**：根据业务需求修改HTML/CSS/JS
4. **启动新应用**：使用对应配置文件启动服务器

### 添加新AI服务商

1. **继承Analyzer类**：实现 `set_AiClient` 和必要的方法
2. **注册到AnalyzerMap**：在 `AnalyzerMap` 字典中添加新类
3. **更新配置文件**：在配置文件中指定新的分析器类名

## 注意事项

1. **API密钥**: 确保有可用的 AI API 密钥并正确设置环境变量
2. **文件大小**: 上传文件大小受配置中的 `max_upload_size` 限制
3. **图片质量**: 确保图片清晰可读，特别是评价表应用
4. **结果缓存**: 分析结果会缓存1小时，避免重复分析相同图片
5. **存储权限**: 如果启用文件保存，确保 `uploads` 目录有写入权限
6. **应用选择**: 根据需求选择启动对应的应用，两个应用配置独立

## 许可证 MIT

本项目仅供学习交流使用。

* 图标 `logos/aimglyze-light.png` 由 ChatGPT 生成。
* 服务器代码 `aimglyze/server.py` 初始版本由 DeepSeek 生成。
* 前端界面的初始版本由 DeepSeek 生成。

## 更新日志

### v0.2.0 (2025-12-25)
* 新增 App-TaskScore 学生评价表分析应用
* 支持评价表结构化解析和多维度评估
* 添加雷达图可视化分析

### v0.1.2 (2025-12-24)
* 修改 Web 界面布局，桌面端改为左右排布
* 根据上传图片的哈希值保存文件，避免重复保存
* 添加示例数据标识

### v0.1.0 (2025-12-23)
* 初始版本发布 (App-DescTags)
* 支持图片上传和 AI 分析
* 完整的 Web 界面
* 双主题支持
* 数据导出功能

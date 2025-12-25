#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2025 shmilee

import os
import sys
import json
import yaml
import base64
import mimetypes
import hashlib
import time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from io import BytesIO
import threading

# 导入现有的分析器模块
from .analyzer import get_analyzer_config, AnalyzerMap


class AnalysisServer(object):
    """分析服务器"""

    def __init__(self, config_path):
        if config_path is None or not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件未找到: {config_path}")
        self.config_path = os.path.abspath(config_path)
        self.config_dir = os.path.dirname(self.config_path)
        print(f"配置文件: {self.config_path}")
        # 从配置文件中读取或默认
        self.config = self.load_config(self.config_path)

        # 初始化分析器
        analyzer_config = get_analyzer_config(self.config_path)
        analyzer_class = AnalyzerMap[analyzer_config['analyzer']]
        self.analyzer = analyzer_class(**analyzer_config['setting'])
        # 缓存分析结果
        self.results_cache = {}

        # 前端根目录可以是绝对路径或相对于配置文件所在目录的相对路径
        frontend_root = self.config['server'].get('frontend_root')
        if not os.path.isabs(frontend_root):
            frontend_root = os.path.join(self.config_dir, frontend_root)
        self.frontend_root = Path(frontend_root)
        print(f"前端根目录: {self.frontend_root}")
        # 确保前端目录存在
        if not os.path.exists(self.frontend_root):
            raise FileNotFoundError(f"前端目录不存在: {self.frontend_root}")

        # 检查示例文件
        sample_file = self.config['server'].get('sample_file')
        if not os.path.isabs(sample_file):
            sample_file = Path(os.path.join(self.config_dir, sample_file))
        self.sample_file = Path(sample_file)
        if not os.path.exists(self.sample_file):
            print(f"警告, 示例文件不存在: {self.sample_file}")
            self.sample_file = None

        # 获取上传保存配置
        self.save_upload = self.config['server'].get('save_upload')
        # 存储文件哈希映射
        self.file_hash_map = {}
        # 如果启用上传保存功能，确保上传目录存在并扫描已有文件
        if self.save_upload:
            upload_dir = self.config['server'].get('upload_dir')
            if not os.path.isabs(upload_dir):
                upload_dir = Path(os.path.join(self.config_dir, upload_dir))
            self.upload_dir = Path(upload_dir)
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            print(f"上传目录: {self.upload_dir}")
            # 启动时扫描已有文件，重建哈希映射
            self.scan_existing_files()
        else:
            self.upload_dir = None
            print("上传保存功能已禁用，上传的文件将不会被保存")

    def load_config(self, config_path):
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 设置默认值
        server_config = config.get('server', {})
        server_config.setdefault('host', '127.0.0.1')
        server_config.setdefault('port', 8080)
        server_config.setdefault('frontend_root', './frontend')
        server_config.setdefault('sample_file', './sample-msg.json')
        server_config.setdefault('save_upload', False)  # 上传保存开关
        server_config.setdefault('upload_dir', './uploads')
        server_config.setdefault('max_upload_size', 10)
        server_config.setdefault('allowed_extensions', [
                                 '.jpg', '.jpeg', '.png', '.webp'])
        server_config.setdefault('debug', False)  # 调试开关

        frontend_config = config.get('frontend', {})
        frontend_config.setdefault('title', '图片分析系统')
        frontend_config.setdefault('subtitle', '基于AI的图片分析与描述')
        frontend_config.setdefault('theme', 'light')
        frontend_config.setdefault('show_sample_data', True)

        config['server'] = server_config
        config['frontend'] = frontend_config

        return config

    def get_file_hash(self, image_data):
        """计算文件的哈希值"""
        return hashlib.md5(image_data).hexdigest()

    def scan_existing_files(self):
        """扫描上传目录中已存在的文件，重建文件哈希映射"""
        if not self.save_upload or self.upload_dir is None:
            return

        print(f"正在扫描上传目录: {self.upload_dir}")
        # 获取允许的文件扩展名
        allowed_extensions = self.config['server']['allowed_extensions']
        # 遍历上传目录中的所有文件
        for file_path in self.upload_dir.iterdir():
            if file_path.is_file():
                # 检查文件扩展名是否在允许的列表中
                file_ext = file_path.suffix.lower()
                if allowed_extensions and file_ext not in allowed_extensions:
                    print(f"跳过非允许扩展名文件: {file_path.name}")
                    continue
                # 从文件名中提取哈希值（{hash}{extension}）
                file_stem = file_path.stem  # 获取不带扩展名的文件名
                # 读取文件内容计算哈希值进行验证
                try:
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                    actual_hash = self.get_file_hash(file_data)
                    # 验证文件名中的哈希值是否与实际文件内容匹配
                    if file_stem != actual_hash:
                        print(f"警告: 文件 {file_path.name} 的哈希值不匹配，跳过")
                        continue
                    # 添加到哈希映射中
                    self.file_hash_map[actual_hash] = str(file_path)
                    print(f"已添加到哈希映射: {actual_hash} -> {file_path}")
                except Exception as e:
                    print(f"处理文件 {file_path.name} 时出错: {str(e)}")
        print(f"扫描完成，找到 {len(self.file_hash_map)} 个有效文件")

    def save_uploaded_file(self, image_data, mime_type, file_hash):
        """保存上传的文件，如果已存在则不重复保存"""
        # 如果上传保存功能禁用，直接返回None
        if not self.save_upload:
            return None
        # 检查是否已存在相同哈希的文件
        if file_hash in self.file_hash_map:
            existing_file = self.file_hash_map[file_hash]
            print(f"文件已存在，使用现有文件: {existing_file}")
            return existing_file

        # 生成文件名
        extension = mimetypes.guess_extension(mime_type) or '.jpg'
        filename = f"{file_hash}{extension}"
        filepath = self.upload_dir / filename
        # 保存文件
        with open(filepath, 'wb') as f:
            f.write(image_data)
        # 更新哈希映射
        self.file_hash_map[file_hash] = str(filepath)
        print(f"文件已保存: {filepath}")
        return str(filepath)

    def analyze_image(self, image_data, mime_type):
        """分析图片并返回结果"""
        try:
            # 生成缓存键
            cache_key = self.get_file_hash(image_data)
            # 检查缓存
            if cache_key in self.results_cache:
                print(f"使用缓存结果: {cache_key}")
                return self.results_cache[cache_key]

            # 执行分析
            print("开始分析图片...")
            start_time = time.time()
            result = self.analyzer.chat(image_data, mime_type)
            elapsed = time.time() - start_time
            print(f"分析完成，耗时: {elapsed:.2f}秒")

            # 缓存结果（有效期1小时）
            self.results_cache[cache_key] = {
                'result': result,
                'timestamp': time.time(),
                'cache_key': cache_key
            }
            # 清理过期缓存
            self.clean_cache()

            return {'result': result, 'cache_key': cache_key}

        except Exception as e:
            print(f"分析失败: {str(e)}")
            return {'error': str(e)}

    def clean_cache(self, max_age=3600):
        """清理过期缓存"""
        now = time.time()
        expired_keys = [
            key for key, data in self.results_cache.items()
            if now - data['timestamp'] > max_age
        ]
        for key in expired_keys:
            del self.results_cache[key]
        if expired_keys:
            print(f"清理了 {len(expired_keys)} 个过期缓存")


# aimglyze-light-16x16.ico
DEFAULT_FAVICON = base64.b64decode(
    """AAABAAEAEBAAAAEACABoBQAAFgAAACgAAAAQAAAAIAAAAAEACAAAAAAAAAEAABMLAAATCwAAAAEA
AAABAADLhD0Ay4U+ANaALwDdjDsA0YtBANGKQQDKgzwAz4g/AP+mRQD/uFgA8ncfABIAAACcSxMA
gDoJAKFNFACaSRMA/8k/APdvCAB5NggAfDgHANOQSADVkEUA1pFFANeVSwDXlUoA15RJANeUSgDX
lEoA1pRKAMmEPgDRiUAA1Y5EANqZUQDbnFUA3J9ZANqWSwDbmU8A25pRANuZTgDalUgA2ZNHANWP
RQDPiUEAyoA4AM6FPADVjEAAz4Y8AL90MADGeTEAzX81AMJ3MQC/cCsAw3MsAMh3LgDAcSsAvGom
AL5tKADEcSgAvGomALllIgC+bCQAxXImALdkIgC2YiAAv2skAMFuIwCyXh8AtF4eAL9rIwC0YB4A
r1scALFbHAC9ZyEArFYYAKtXGgCwWxsAt18cAKlTFgCnUxcAq1YYALRbGgCnUhYAo1AVAKJQFgCv
VxgAlUwWAKNNEgCnURUAsVcYAGwxCAB4NwkAlEYSAKROFACrUxYAsFcYALNZGQC0WhkAslgZAK9W
FwCqUxYAnUwTAIc/DABxMgQAhT4OAJBEEQCQRRIAkUYSAI9FEQCORBEAjEMQAIA8DgDfpV8A8b5v
AOu/fwD11Z0A57p+ANqocwDZqXYA2qVpANyaTgDZkkYAzItHAN+rZgDzv2oA7sJ8AP3clgD+3psA
5bd6ANeXSwDYnVYA2qFXANeUSQDShTkAxodFAMWLSQDOmVcA2KVjAO/EfAD1zYQA7caGAN2saQDj
s3MA4rR6ANuocADMfTMAtnc1AKtxLwC9kF8A58mXAOrUnwD51pQA9taZAN/ElgDbwZYA6cqQAO3J
lADOhDcAtHErAJleHwC5k2cAzdq0AJDY2ADu2pgA2bJyANywcADktm4A161vAMyrfwDMhz0AwHMo
AKlmIwCwhlkA5+PBALbXuADSx5IA1p9SAO3QowDXrHAAv7hxAL2bXQDDhkUAzoQxAMd5KAC9hEgA
u8iTAHykRgCbn1sAvX4+AM+rfgC/kl4AkI1TAKqAPwC7fkEAzH4uAM+EMQDGhkEAip1YAE6CFwB8
hD4AtoZTAL6UaADEmGUAtn05AMSPSwC2fUUAxXInANKKNgDKhjsArMGOAILJggCLsHgAtZhkAL2P
VwDLnV8A1atsAMWfaQCmZzMAvWQfAM6AMADNiDUAu5NhALOUZQCofUwAl2EnAJ9qMACldUAAnXA9
AK6DSwCuai0AuF4bAMFpIQDLeykAyXwoAM2CKQDKgCgAxHwoALt4LACzcikAol8YAHtCEQCKVyYA
uF0bAL9nIADHdScAyXksAMt7KwDOgSsAy3wqAMZ1JwC1YBwAj0UPAP///wAAAAAAAAAAAAAAAAAA
AAAADg8QZ2hpamlra2xtbhESEwxbXF1eX2BQUGFiY2RlZg0KV1jx8vP09fb3+Pn6WVoLU1Tl5ufo
6err7O3u7/BVVk9Q2drb3N3e3+Dh4uPkUVJLTM3Oz9DR0tPU1dbX2E1OR0jBwsPExcbHyMnKy8xJ
SkNEtba3uLm6u7y9vr/ARUY/QKmqq6ytrq+wsbKztEFCOzydnp+goaKjpKWmp6g9Pjc4kZKTlJWW
l5iZmpucOTozNIWGh4iJiouMjY6PkDU2LzB5ent8fX5/gIGCg4QxMggrLG9wcXJzdHV2d3gtLgkG
HR4fICEiIyQlJicoKSoHAAECFBUWFhcYGRobHAMEBeAHAACAAQAAgAEAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAQAAgAEAAOAHAAA="""
)


class RequestHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""

    def __init__(self, *args, **kwargs):
        self.server_instance = kwargs.pop('server_instance')
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        # API路由处理
        if path == '/api/config':
            self.send_config()
        elif path == '/api/sample':
            self.send_sample_data()
        elif path == '/api/health':
            self.send_health_check()
        elif path.startswith('/api/results/'):
            self.get_cached_result(path)
        else:
            if path == '/favicon.ico':
                self.send_favicon()
            else:
                # 前端文件服务
                self.serve_frontend_file(path)

    def do_POST(self):
        """处理POST请求"""
        if self.path == '/api/analyze':
            self.handle_upload()
        else:
            self.send_error(404, "Not Found")

    def send_favicon(self):
        """发送favicon.ico文件"""
        try:
            # 前端目录中是否存在 favicon.ico
            favicon_path = Path(os.path.join(
                self.server_instance.frontend_root, 'favicon.ico'))
            if favicon_path.exists():
                with open(favicon_path, 'rb') as f:
                    favicon_data = f.read()
            else:
                # 使用默认的favicon.ico
                favicon_data = DEFAULT_FAVICON
            self.send_response(200)
            self.send_header('Content-Type', 'image/x-icon')
            self.send_header('Content-Length', str(len(favicon_data)))
            self.send_header('Cache-Control', 'public, max-age=86400')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(favicon_data)
        except Exception as e:
            self.send_error(500,  str(e))

    def serve_frontend_file(self, path):
        """提供前端静态文件"""
        try:
            # 将URL路径转换为文件系统路径
            if path == '/':
                filepath = 'index.html'
            else:
                # 移除开头的斜杠
                filepath = path[1:] if path.startswith('/') else path
            # 构建完整路径
            full_path = os.path.join(
                self.server_instance.frontend_root, filepath)
            # 如果文件不存在，尝试index.html（用于SPA路由）
            # if not os.path.exists(full_path):
            #    full_path = os.path.join(
            #        self.server_instance.frontend_root, 'index.html')
            if not os.path.exists(full_path):
                self.send_error(404, f"File not found: {path}")
                return

            with open(full_path, 'rb') as f:
                content = f.read()

            # 猜测内容类型
            content_type = self.guess_content_type(full_path)

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content)

        except Exception as e:
            self.send_error(500, str(e))

    def guess_content_type(self, filepath):
        """猜测文件类型"""
        mime_type, _ = mimetypes.guess_type(filepath)
        return mime_type or 'application/octet-stream'

    def send_config(self):
        """发送配置信息"""
        config = self.server_instance.config
        response = {
            'frontend': config['frontend'],
            'allowed_extensions': config['server']['allowed_extensions'],
            'max_upload_size': config['server']['max_upload_size'],
            'save_upload': config['server']['save_upload']  # 上传保存开关状态
        }
        self.send_json(response)

    def send_sample_data(self):
        """发送示例数据"""
        try:
            sample_file = self.server_instance.sample_file
            if sample_file is None:
                self.send_error(404, "Sample data file not found")
                return
            with open(sample_file, 'r', encoding='utf-8') as f:
                sample_data = json.load(f)
            # 添加示例标记
            sample_data['is_sample'] = True
            sample_data['timestamp'] = time.time()
            self.send_json(sample_data)
        except Exception as e:
            self.send_error(500, f"Failed to load sample data: {str(e)}")

    def send_health_check(self):
        """发送健康检查响应"""
        response = {
            'status': 'ok',
            'timestamp': time.time()
        }
        self.send_json(response)

    def get_cached_result(self, path):
        """获取缓存的分析结果"""
        try:
            cache_key = path.split('/')[-1]
            if cache_key in self.server_instance.results_cache:
                data = self.server_instance.results_cache[cache_key]
                self.send_json(data)
            else:
                self.send_error(404, "Result not found")
        except Exception as e:
            self.send_error(500, str(e))

    def handle_upload(self):
        """处理文件上传和分析"""
        try:
            # 检查内容类型
            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' not in content_type:
                self.send_error(400, "Expected multipart/form-data")
                return
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "Empty request body")
                return

            # 解析multipart/form-data
            post_data = self.rfile.read(content_length)
            # 简化的multipart解析（实际应用中建议使用email.parser或第三方库）
            boundary = content_type.split('boundary=')[1].encode()
            parts = post_data.split(b'--' + boundary)

            image_data = None
            mime_type = None
            for part in parts:
                if b'Content-Disposition: form-data; name="file"' in part:
                    # 提取文件数据
                    header_end = part.find(b'\r\n\r\n')
                    if header_end != -1:
                        image_data = part[header_end + 4:]
                        # 去掉结尾的\r\n
                        if image_data.endswith(b'\r\n'):
                            image_data = image_data[:-2]
                        # 提取MIME类型
                        headers = part[:header_end].decode(
                            'utf-8', errors='ignore')
                        for line in headers.split('\r\n'):
                            if line.lower().startswith('content-type:'):
                                mime_type = line.split(': ')[1].strip()
                                break
                        break

            if not image_data or not mime_type:
                self.send_error(400, "No file uploaded")
                return

            # 检查文件大小
            max_size = self.server_instance.config['server']['max_upload_size'] * 1024 * 1024
            if len(image_data) > max_size:
                self.send_error(
                    413, f"File too large (max {max_size/1024/1024}MB)")
                return

            # 计算文件哈希
            file_hash = self.server_instance.get_file_hash(image_data)
            # 保存文件（如果启用上传功能）
            filepath = None
            if self.server_instance.save_upload:
                filepath = self.server_instance.save_uploaded_file(
                    image_data, mime_type, file_hash)

            # 分析图片
            result = self.server_instance.analyze_image(image_data, mime_type)
            # 在结果中添加文件信息
            if 'result' in result:
                result['file_info'] = {
                    'hash': file_hash,
                    'path': filepath,
                    'size': len(image_data),
                    'mime_type': mime_type,
                    'saved': filepath is not None  # 标记文件是否被保存
                }

            # 返回结果
            self.send_json(result)

        except Exception as e:
            print(f"上传处理失败: {str(e)}")
            self.send_error(500, str(e))

    def send_json(self, data):
        """发送JSON响应"""
        response = json.dumps(data, ensure_ascii=False).encode('utf-8')

        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(response)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response)

    def send_error(self, code, message):
        """发送错误响应"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        error_data = {
            'error': True,
            'code': code,
            'message': message
        }

        self.wfile.write(json.dumps(error_data).encode())

    def log_message(self, format, *args):
        """自定义日志格式"""
        # 检查是否为健康检查请求
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/api/health':
            # 只有在调试模式下才打印健康检查日志
            if self.server_instance.config['server'].get('debug', False):
                print(f"[{self.log_date_time_string()}] {format % args}")
        else:
            # 其他请求正常打印日志
            print(f"[{self.log_date_time_string()}] {format % args}")


def run_server(config_path):
    """启动服务器"""
    try:
        # 创建服务器实例
        server = AnalysisServer(config_path)
        server_config = server.config['server']

        # 创建HTTP服务器
        handler_class = lambda *args, **kwargs: RequestHandler(
            *args, **kwargs, server_instance=server)
        httpd = HTTPServer(
            (server_config['host'], server_config['port']), handler_class)

        print(f"服务器启动在 http://{server_config['host']}:{server_config['port']}")
        print("按 Ctrl+C 停止服务器")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器正在停止...")
            httpd.server_close()
            print("服务器已停止")
            sys.exit(0)

    except Exception as e:
        print(f"启动服务器失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    run_server('./App-DescTags/config.yaml')

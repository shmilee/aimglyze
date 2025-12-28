# -*- coding: utf-8 -*-

# Copyright (c) 2025 shmilee

import os
import sys
import signal
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog

# 版本信息
VERSION = "0.2.4"


class ApplicationGUI(object):
    """简易GUI图形界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("图片分析系统")
        self.root.geometry("600x550")
        # 设置窗口图标
        try:
            img = tk.PhotoImage(file=self.get_icon_path())
            self.root.tk.call('wm', 'iconphoto', root._w, "-default", img)
            # self.root.iconbitmap(self.get_icon_path())
        except Exception as e:
            print(e)
        # 应用配置
        self.apps = {
            "desc-tags": "图片描述标签分析",
            "task-score": "学生任务评分分析",
            "custom": "自定义配置文件"
        }
        # 当前选择的应用
        self.selected_app = tk.StringVar(value="desc-tags")
        # 自定义配置文件路径
        self.custom_config_path = tk.StringVar()
        # 服务器进程
        self.server_process = None
        # 初始化界面
        self.setup_ui()

    def get_icon_path(self):
        """获取图标路径"""
        # 尝试在当前目录查找
        icon_paths = [
            "logos/aimglyze-light-256x256.png",
            # "apps/App-DescTags/frontend/favicon.ico"
        ]
        here = os.path.dirname(os.path.abspath(__file__))
        for path in icon_paths:
            path = os.path.join(here, path)
            # print(os.path.exists(path), path)
            if os.path.exists(path):
                return path
        return None

    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # 标题行（居中）
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=2, pady=(0, 15))
        # 标题容器，用于居中显示
        title_container = ttk.Frame(title_frame)
        title_container.pack(expand=True)
        # 标题（居中）
        title_label = ttk.Label(
            title_container,
            text="图片分析系统",
            font=("Arial", 16, "bold")
        )
        title_label.pack(side=tk.LEFT)
        # 版本信息（小字，在标题旁边，居中）
        version_label = ttk.Label(
            title_container,
            text=f"v{VERSION}",
            font=("Arial", 9, "italic")
        )
        version_label.pack(side=tk.LEFT, padx=(5, 0))

        # 应用选择和操作按钮并排
        # 左侧：应用选择
        app_frame = ttk.LabelFrame(main_frame, text="选择应用", padding="10")
        app_frame.grid(row=1, column=0, sticky=(
            tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        app_frame.columnconfigure(0, weight=1)  # 让应用选择区域可以扩展
        # 应用选择单选按钮
        row = 0
        for app_key, app_name in self.apps.items():
            if app_key == "custom":
                # 自定义配置文件选项
                custom_frame = ttk.Frame(app_frame)
                custom_frame.grid(row=row, column=0, sticky=tk.W, pady=(5, 0))
                rb = ttk.Radiobutton(
                    custom_frame,
                    text=app_name,
                    variable=self.selected_app,
                    value=app_key,
                    command=self.on_custom_selected
                )
                rb.pack(side=tk.LEFT)
                # 文件选择按钮
                select_button = ttk.Button(
                    custom_frame,
                    text="选择文件",
                    command=self.select_config_file,
                    width=8
                )
                select_button.pack(side=tk.LEFT, padx=(5, 0))
                # 显示选中的文件路径
                self.custom_path_label = ttk.Label(
                    app_frame,
                    textvariable=self.custom_config_path,
                    font=("Arial", 9),
                    foreground="gray",
                    wraplength=250  # 限制换行长度
                )
                self.custom_path_label.grid(
                    row=row+1, column=0, sticky=tk.W, pady=(2, 0))
                row += 2
            else:
                rb = ttk.Radiobutton(
                    app_frame,
                    text=app_name,
                    variable=self.selected_app,
                    value=app_key,
                    command=self.on_app_selected
                )
                rb.grid(row=row, column=0, sticky=tk.W, pady=2)
                row += 1

        # 右侧：操作按钮和状态栏
        button_frame = ttk.LabelFrame(main_frame, text="操作", padding="10")
        button_frame.grid(row=1, column=1, sticky=(
            tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        # 配置按钮框架的网格
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.rowconfigure(0, weight=0)
        button_frame.rowconfigure(1, weight=0)
        button_frame.rowconfigure(2, weight=0)  # 状态框行

        # 启动服务按钮（左上方）
        self.start_button = ttk.Button(
            button_frame,
            text="启动服务",
            command=self.start_server,
            width=12
        )
        self.start_button.grid(row=0, column=0, padx=2,
                               pady=2, sticky=tk.W+tk.E)
        # 停止服务按钮（左下方）
        self.stop_button = ttk.Button(
            button_frame,
            text="停止服务",
            command=self.stop_server,
            width=12,
            state=tk.DISABLED
        )
        self.stop_button.grid(row=1, column=0, padx=2,
                              pady=2, sticky=tk.W+tk.E)
        # 清理缓存按钮（右上方）
        clean_cache_button = ttk.Button(
            button_frame,
            text="清理缓存",
            command=self.clean_cache,
            width=12
        )
        clean_cache_button.grid(row=0, column=1, padx=2,
                                pady=2, sticky=tk.W+tk.E)
        # 清理上传文件按钮（右下方）
        clean_uploads_button = ttk.Button(
            button_frame,
            text="清理上传文件",
            command=self.clean_uploads,
            width=12
        )
        clean_uploads_button.grid(
            row=1, column=1, padx=2, pady=2, sticky=tk.W+tk.E)

        # 服务状态框（位于服务按钮下方，左列）
        service_status_container = ttk.Frame(button_frame)
        service_status_container.grid(
            row=2, column=0, pady=(6, 2), sticky=(tk.W, tk.E))
        # 创建服务状态指示器容器
        service_status_frame = ttk.Frame(
            service_status_container, relief="ridge", borderwidth=0.5)
        service_status_frame.pack(pady=2)
        # 服务状态指示器（彩色圆点）
        self.service_status_canvas = tk.Canvas(
            service_status_frame, width=50, height=20)
        self.service_status_canvas.pack(side=tk.LEFT, padx=(18, 0))
        self.service_status_indicator = self.service_status_canvas.create_oval(
            5, 5, 15, 15,
            fill="blue"  # 蓝色表示就绪
        )
        # 服务状态标签
        self.service_status_label = ttk.Label(
            service_status_frame,
            text="服务就绪",
            font=("Arial", 9)
        )
        self.service_status_label.pack(side=tk.LEFT, padx=(0, 22))

        # 清理状态框（位于清理按钮下方，右列）
        clean_status_container = ttk.Frame(button_frame)
        clean_status_container.grid(
            row=2, column=1, pady=(6, 2), sticky=(tk.W, tk.E))
        # 创建清理状态指示器容器
        clean_status_frame = ttk.Frame(
            clean_status_container, relief="ridge", borderwidth=0.5)
        clean_status_frame.pack(pady=2)
        # 清理状态指示器（彩色圆点）
        self.clean_status_canvas = tk.Canvas(
            clean_status_frame, width=50, height=20)
        self.clean_status_canvas.pack(side=tk.LEFT, padx=(18, 0))
        self.clean_status_indicator = self.clean_status_canvas.create_oval(
            5, 5, 15, 15,
            fill="blue"  # 蓝色表示就绪
        )
        # 清理状态标签
        self.clean_status_label = ttk.Label(
            clean_status_frame,
            text="清理就绪",
            font=("Arial", 9)
        )
        self.clean_status_label.pack(side=tk.LEFT, padx=(0, 22))

        # 日志输出部分（放在最下面）
        log_frame = ttk.LabelFrame(main_frame, text="日志输出", padding="10")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(
            tk.W, tk.E, tk.N, tk.S), pady=(10, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        # 配置网格权重，让日志区域可以扩展
        main_frame.rowconfigure(2, weight=1)
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            wrap=tk.WORD
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # 清空日志按钮（放在日志框内部右上角）
        # 创建一个容器框架来放置按钮
        button_container = ttk.Frame(log_frame)
        button_container.grid(row=0, column=0, sticky=tk.NE, padx=20, pady=5)
        clear_button = ttk.Button(
            button_container,
            text="清空日志",
            command=self.clear_log,
            width=8
        )
        clear_button.pack()

    def on_app_selected(self):
        """当选择预设应用时"""
        # 清空自定义文件路径显示
        self.custom_config_path.set("")

    def on_custom_selected(self):
        """当选择自定义配置文件时"""
        # 如果还没有选择文件，自动弹出文件选择对话框
        if not self.custom_config_path.get():
            self.select_config_file()

    def select_config_file(self):
        """选择配置文件"""
        file_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[
                ("YAML配置文件", "*.yaml;*.yml"),
                ("所有文件", "*.*")
            ],
            initialdir="."
        )
        if file_path:
            # 验证文件扩展名
            if not file_path.lower().endswith(('.yaml', '.yml')):
                # 询问是否继续
                response = messagebox.askyesno(
                    "警告",
                    f"选择的文件 '{os.path.basename(file_path)}' 不是YAML格式文件。\n是否继续使用此文件？"
                )
                if not response:
                    return
            # 检查文件是否存在
            if os.path.exists(file_path):
                self.custom_config_path.set(file_path)
                self.log_message(f"已选择配置文件: {file_path}")
            else:
                messagebox.showerror("错误", f"文件不存在: {file_path}")

    def get_config_argument(self):
        """获取配置参数"""
        app_alias = self.selected_app.get()
        if app_alias == "custom":
            # 自定义配置文件
            config_path = self.custom_config_path.get()
            if not config_path:
                messagebox.showwarning("警告", "请先选择配置文件")
                return None
            if not os.path.exists(config_path):
                messagebox.showerror("错误", f"配置文件不存在: {config_path}")
                return None
            return config_path
        else:
            # 应用别名
            return app_alias

    def log_message(self, message):
        """添加日志消息"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.update()

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)

    def update_service_status(self, status, color="blue"):
        """更新服务状态"""
        self.service_status_label.config(text=status)
        self.service_status_canvas.itemconfig(
            self.service_status_indicator, fill=color)
        self.service_status_canvas.update()

    def update_clean_status(self, status, color="blue"):
        """更新清理状态"""
        self.clean_status_label.config(text=status)
        self.clean_status_canvas.itemconfig(
            self.clean_status_indicator, fill=color)
        self.clean_status_canvas.update()

    def start_server(self):
        """启动服务器"""
        if self.server_process and self.server_process.poll() is None:
            messagebox.showwarning("警告", "服务器已经在运行中！")
            return
        # 获取配置参数
        config_arg = self.get_config_argument()
        if config_arg is None:
            return
        # 显示启动的应用
        if config_arg in self.apps:
            app_name = self.apps[config_arg]
        else:
            app_name = f"自定义配置文件: {os.path.basename(config_arg)}"
        self.log_message(f"启动 {app_name} 服务...")
        self.update_service_status("启动中...", "yellow")
        # 禁用启动按钮，启用停止按钮
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        # 在新线程中启动服务器，避免阻塞GUI
        thread = threading.Thread(
            target=self.run_server_command,
            args=(config_arg,),
            daemon=True
        )
        thread.start()

    def run_server_command(self, config_arg):
        """执行服务器启动命令"""
        try:
            # 构建命令
            command = [sys.executable, "-u", "-X", "utf8", "-m",
                       "aimglyze.cli", "server", config_arg]
            # 启动子进程
            self.server_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
            )
            self.log_message(f"服务器已启动，PID: {self.server_process.pid}")
            self.update_service_status("运行中", "green")
            # 实时读取输出
            for line in iter(self.server_process.stdout.readline, ''):
                if line:
                    self.log_message(line.strip())
            # 进程结束时
            return_code = self.server_process.wait()
            self.server_process = None
            # 在GUI线程中更新状态
            self.root.after(0, self.on_server_stopped, return_code)
        except Exception as e:
            self.root.after(0, self.on_server_error, str(e))

    def on_server_stopped(self, return_code):
        """服务器停止时的回调"""
        if return_code in [0, -signal.SIGTERM]:
            self.log_message("服务器正常停止")
            self.update_service_status("已停止", "orange")
        else:
            self.log_message(f"服务器异常退出，返回码: {return_code}")
            self.update_service_status("异常停止", "red")
        # 恢复按钮状态
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def on_server_error(self, error_msg):
        """服务器错误时的回调"""
        self.log_message(f"启动服务器时出错: {error_msg}")
        self.update_service_status("启动失败", "red")
        # 恢复按钮状态
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def stop_server(self):
        """停止服务器"""
        if self.server_process and self.server_process.poll() is None:
            self.log_message("正在停止服务器...")
            self.update_service_status("停止中...", "orange")
            # 发送终止信号
            self.server_process.terminate()
            # 等待进程结束（超时5秒）
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # 强制终止
                self.server_process.kill()
                self.log_message("强制终止服务器进程")
            self.log_message("服务器已停止")
            self.update_service_status("已停止", "orange")
            # 恢复按钮状态
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
        else:
            messagebox.showinfo("提示", "服务器未在运行")

    def clean_cache(self):
        """清理缓存"""
        # 获取配置参数
        config_arg = self.get_config_argument()
        if config_arg is None:
            return
        self.log_message("清理缓存...")
        self.update_clean_status("清理中...", "yellow")
        # 在新线程中执行清理操作
        thread = threading.Thread(
            target=self.run_clean_command,
            args=("clean-cache", config_arg),
            daemon=True
        )
        thread.start()

    def clean_uploads(self):
        """清理上传文件"""
        # 获取配置参数
        config_arg = self.get_config_argument()
        if config_arg is None:
            return
        # 弹出确认对话框
        confirm = messagebox.askyesno(
            "确认",
            "将清理置信度低于0.5的上传文件。\n是否继续？"
        )
        if not confirm:
            return
        self.log_message("清理上传文件...")
        self.update_clean_status("清理中...", "yellow")
        # 在新线程中执行清理操作
        thread = threading.Thread(
            target=self.run_clean_command,
            args=("clean-uploads", config_arg),
            daemon=True
        )
        thread.start()

    def run_clean_command(self, command_type, config_arg):
        """执行清理命令"""
        try:
            # 构建命令
            command = [sys.executable, "-u", "-X", "utf8", "-m",
                       "aimglyze.cli", command_type, config_arg]
            # 执行命令
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60,
                encoding='utf-8',
                errors='replace',
            )
            # 在GUI线程中显示结果
            self.root.after(0, self.on_clean_completed, command_type, result)
        except subprocess.TimeoutExpired:
            error_msg = "清理操作超时"
            self.root.after(0, self.on_clean_error, command_type, error_msg)
        except Exception as e:
            self.root.after(0, self.on_clean_error, command_type, str(e))

    def on_clean_completed(self, command_type, result):
        """清理完成时的回调"""
        if result.returncode == 0:
            self.log_message(result.stdout)
            self.update_clean_status("清理完成", "green")
        else:
            self.log_message(f"错误: {result.stderr}")
            self.update_clean_status("清理失败", "red")

    def on_clean_error(self, command_type, error_msg):
        """清理错误时的回调"""
        self.log_message(f"{command_type} 出错: {error_msg}")
        self.update_clean_status("清理失败", "red")


def main():
    """主函数"""
    try:
        # 创建主窗口
        root = tk.Tk()
        # 创建应用程序
        app = ApplicationGUI(root)
        # 设置窗口关闭事件

        def on_closing():
            # 如果服务器在运行，提示用户
            if app.server_process and app.server_process.poll() is None:
                response = messagebox.askyesno(
                    "确认退出",
                    "服务器正在运行，退出将停止服务器。\n是否继续退出？"
                )
                if response:
                    # 停止服务器
                    app.stop_server()
                    root.destroy()
            else:
                root.destroy()
        root.protocol("WM_DELETE_WINDOW", on_closing)
        # 运行主循环
        root.mainloop()
    except Exception as e:
        print(f"启动GUI时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

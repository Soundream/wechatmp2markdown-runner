#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import platform
import subprocess
import threading
import socket
import time
import tempfile
import atexit
import signal
import psutil
from pathlib import Path

# 导入PyQt6
try:
    from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
    from PyQt6.QtGui import QIcon, QAction, QCursor
    from PyQt6.QtCore import QObject, QTimer
except ImportError:
    print("错误: 请先安装PyQt6")
    print("可以使用以下命令安装: pip install PyQt6")
    sys.exit(1)

# 检查端口是否被占用
def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# 检查服务器是否在运行
def check_server_running(port=5001):
    """检查服务器是否在运行"""
    try:
        import urllib.request
        import urllib.error
        try:
            response = urllib.request.urlopen(f"http://localhost:{port}/status", timeout=2)
            return True
        except (urllib.error.URLError, ConnectionRefusedError):
            return False
    except Exception:
        return False

# 向服务器发送URL
def send_url_to_server(url, port=5001):
    """向服务器发送URL"""
    import json
    import urllib.request
    import urllib.error

    try:
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({"url": url}).encode('utf-8')
        req = urllib.request.Request(f"http://localhost:{port}/download", data=data, headers=headers, method='POST')
        response = urllib.request.urlopen(req, timeout=2)
        
        if response.status == 200:
            return True
        return False
    except Exception as e:
        print(f"发送URL出错: {str(e)}")
        return False

# 主托盘应用类
class WechatArticleDownloaderTray:
    def __init__(self, custom_icon=None):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # 设置应用名称
        self.app.setApplicationName("微信公众号文章下载器")
        
        # 保存自定义图标路径
        self.custom_icon = custom_icon
        
        # 设置托盘图标
        self.setup_tray()
        
        # 服务进程
        self.server_process = None
        
    def setup_tray(self):
        """设置系统托盘"""
        # 加载图标
        self.tray_icon = QSystemTrayIcon()
        try:
            # 如果有自定义图标，优先使用
            if self.custom_icon and os.path.exists(self.custom_icon):
                icon_path = self.custom_icon
                print(f"使用自定义图标: {icon_path}")
            else:
                # 尝试使用项目中的ICO图标
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        "web_extension/icons/white-bg-icon.ico")
                
                # 如果找不到，尝试使用默认图标
                if not os.path.exists(icon_path):
                    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                           "web_extension/icons/icon.ico")
            
            if os.path.exists(icon_path):
                self.tray_icon.setIcon(QIcon(icon_path))
            else:
                # 如果找不到任何图标，使用系统默认图标
                print("找不到有效的图标文件，使用系统默认图标")
                self.tray_icon.setIcon(QIcon.fromTheme("application-x-executable"))
                
        except Exception as e:
            print(f"加载图标出错: {e}")
            self.tray_icon.setIcon(QIcon.fromTheme("application-x-executable"))
        
        # 创建简化的托盘菜单
        self.menu = QMenu()
        
        # 退出选项
        self.exit_action = QAction("退出")
        self.exit_action.triggered.connect(self.exit_app)
        self.menu.addAction(self.exit_action)
        
        # 设置右键菜单
        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.show()
    
    def ensure_server_running(self, url=None):
        """确保服务器运行，如有需要则启动服务器"""
        # 检查服务是否已在运行
        if check_server_running():
            print("服务已在运行")
            # 如果提供了URL，发送给服务器
            if url:
                self.send_url(url)
            return True
            
        # 如果服务未运行，尝试启动服务
        print("服务未运行，正在启动...")
        
        # 检查端口是否被占用
        if is_port_in_use(5001) and not check_server_running():
            print("端口5001被占用但服务不可用，尝试释放端口...")
            # 尝试释放端口
            self.release_port()
            if is_port_in_use(5001):
                print("无法释放端口5001")
                return False
        
        # 启动simple_server
        server_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                   "simple_server.py")
        
        try:
            # 根据操作系统启动服务
            if platform.system() == "Windows":
                self.server_process = subprocess.Popen(
                    [sys.executable, server_script],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                self.server_process = subprocess.Popen(
                    [sys.executable, server_script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
            # 等待服务启动
            for attempt in range(5):
                if check_server_running():
                    print("服务已成功启动")
                    # 如果提供了URL，发送给服务器
                    if url:
                        self.send_url(url)
                    return True
                time.sleep(0.5)
                
            print("服务启动超时")
            return False
            
        except Exception as e:
            print(f"启动服务出错: {str(e)}")
            return False
    
    def release_port(self):
        """尝试释放端口"""
        try:
            if platform.system() == "Windows":
                # Windows上使用taskkill命令
                subprocess.run(
                    ["taskkill", "/F", "/IM", "python.exe", "/T"],
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
            else:
                # macOS/Linux上使用pkill命令
                subprocess.run(
                    ["pkill", "-f", "simple_server.py"],
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
            time.sleep(1)  # 等待进程终止
        except Exception as e:
            print(f"释放端口出错: {str(e)}")
    
    def send_url(self, url):
        """发送URL到服务器"""
        # 确保URL是字符串
        url = str(url)
        print(f"接收到URL: {url}")
        
        # 启动线程发送URL
        threading.Thread(
            target=lambda: send_url_to_server(url),
            daemon=True
        ).start()
    
    def handle_message(self, message):
        """处理来自浏览器扩展的消息"""
        # 检查消息是否包含URL
        if isinstance(message, dict) and 'url' in message:
            url = message['url']
            # 确保服务运行并发送URL
            self.ensure_server_running(url)
        elif isinstance(message, str) and message.startswith('http'):
            # 直接作为URL处理
            self.ensure_server_running(message)
    
    def show_message(self, title, message):
        """显示消息通知"""
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 2000)
    
    def exit_app(self):
        """退出应用"""
        # 如果服务是由本应用启动的，尝试停止服务
        if self.server_process:
            try:
                self.server_process.terminate()
            except:
                pass
        
        # 退出应用
        QApplication.quit()
    
    def run(self):
        """运行应用"""
        # 显示欢迎消息
        self.tray_icon.showMessage(
            "公众号文章下载器",
            "已在后台运行，可通过浏览器扩展下载文章",
            QSystemTrayIcon.MessageIcon.Information,
            3000  # 显示3秒
        )
        
        # 运行应用
        sys.exit(self.app.exec())

# 检查应用是否已经在运行
def is_app_already_running(lock_socket_port=12345):
    """检查应用是否已经在运行"""
    try:
        # 尝试绑定到特定端口，如果绑定失败则表明应用已经运行
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', lock_socket_port))
        sock.listen(1)
        # 成功绑定，应用没有在运行
        return False, sock
    except socket.error:
        # 绑定失败，说明端口被占用，应用已在运行
        return True, None

# 终止同名进程
def terminate_other_instances():
    """终止其他同名进程"""
    current_pid = os.getpid()
    current_process = psutil.Process(current_pid)
    current_name = current_process.name()
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] == current_name and proc.info['pid'] != current_pid:
                print(f"发现同名进程 {proc.info['pid']}，正在终止...")
                if platform.system() == "Windows":
                    subprocess.run(["taskkill", "/F", "/PID", str(proc.info['pid'])], 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    os.kill(proc.info['pid'], signal.SIGTERM)
                time.sleep(1)  # 等待进程终止
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

# 主函数
def main():
    """主函数"""
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='微信公众号文章下载器系统托盘应用')
    parser.add_argument('--icon', help='指定自定义图标路径')
    parser.add_argument('--force', action='store_true', help='强制启动，关闭其他实例')
    args = parser.parse_args()
    
    # 检查是否已有实例在运行
    already_running, lock_socket = is_app_already_running()
    
    if already_running:
        print("检测到微信公众号文章下载器已经在运行")
        if args.force:
            print("使用--force参数，正在终止其他实例...")
            terminate_other_instances()
            time.sleep(1)  # 等待进程完全终止
            # 重新检查是否可以启动
            already_running, lock_socket = is_app_already_running()
            if already_running:
                print("无法终止其他实例，退出程序")
                sys.exit(1)
        else:
            print("如需强制启动新实例并关闭旧实例，请使用 --force 参数")
            sys.exit(1)
    
    # 保持锁定状态
    if lock_socket:
        # 当应用退出时关闭socket
        atexit.register(lock_socket.close)
    
    # 运行系统托盘应用
    tray_app = WechatArticleDownloaderTray(custom_icon=args.icon)
    tray_app.run()

if __name__ == "__main__":
    main()
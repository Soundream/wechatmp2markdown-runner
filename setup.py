import os
import sys
import subprocess
import platform
import argparse
import webbrowser
import time
import signal
import threading
import socket
import urllib.request
import urllib.error
from pathlib import Path


def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def check_server_running(port=5001):
    """检查服务器是否正在运行"""
    try:
        response = urllib.request.urlopen(f"http://localhost:{port}/status")
        return True
    except urllib.error.URLError:
        return False


def install_dependencies():
    """安装依赖"""
    print("正在安装必要依赖...")
    subprocess.run([sys.executable, "-m", "pip", "install", "flask", "flask-cors"])
    print("依赖安装完成！")


def start_server():
    """启动服务器"""
    server_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.py")
    if is_port_in_use(5001):
        print("检测到端口5001已被占用，可能服务已经在运行。")
        if check_server_running():
            print("服务器已经在运行中。")
            return True
        else:
            print("端口被占用但服务不可用，请关闭占用端口的程序后重试。")
            return False
            
    # 使用Popen启动服务器作为后台进程
    system = platform.system()
    if system == "Windows":
        server_process = subprocess.Popen(
            [sys.executable, server_script],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:  # macOS或Linux
        server_process = subprocess.Popen(
            [sys.executable, server_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    
    # 等待服务器启动
    print("正在启动服务器...")
    attempts = 0
    while attempts < 10:
        if check_server_running():
            print("服务器已成功启动!")
            return True
        time.sleep(1)
        attempts += 1
    
    print("服务器未能在预期时间内启动，请检查日志。")
    return False


def open_extension_installation(browser_choice='both'):
    """打开浏览器扩展安装页面
    
    Args:
        browser_choice: 选择打开哪个浏览器的扩展页面 'chrome', 'edge', 或 'both'
    """
    system = platform.system()
    extension_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_extension")
    
    if browser_choice in ['chrome', 'both']:
        print("1. 请手动打开Chrome并访问edge://extensions")
        print("2. 开启右上角的'开发者模式'")
        print(f"3. 点击'加载已解压的扩展程序'并选择以下文件夹: \n   {extension_path}")
    
    if browser_choice in ['edge', 'both']:
        print("1. 请手动打开Edge并访问edge://extensions")
        print("2. 开启左侧的'开发人员模式'")
        print(f"3. 点击'加载解压缩的扩展'并选择以下文件夹: \n   {extension_path}")

def setup_autostart():
    """配置开机自启动"""
    system = platform.system()
    script_path = os.path.abspath(__file__)
    
    if system == "Windows":
        # 创建批处理文件
        startup_dir = os.path.join(os.environ["APPDATA"], "Microsoft\\Windows\\Start Menu\\Programs\\Startup")
        bat_path = os.path.join(startup_dir, "wechat_article_downloader.bat")
        
        with open(bat_path, "w") as f:
            f.write(f'@echo off\n"{sys.executable}" "{script_path}" --server-only\n')
            
        print(f"已创建开机自启动脚本: {bat_path}")
        
    elif system == "Darwin":  # macOS
        # 创建plist文件
        home_dir = str(Path.home())
        launch_agents_dir = os.path.join(home_dir, "Library/LaunchAgents")
        os.makedirs(launch_agents_dir, exist_ok=True)
        
        plist_path = os.path.join(launch_agents_dir, "com.wechatarticle.downloader.plist")
        
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.wechatarticle.downloader</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{script_path}</string>
        <string>--server-only</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>'''
        
        with open(plist_path, "w") as f:
            f.write(plist_content)
            
        # 加载启动项
        subprocess.run(["launchctl", "load", plist_path])
        print(f"已创建开机自启动配置: {plist_path}")
    else:
        print("当前系统不支持配置开机自启动，请手动添加。")


def main():
    parser = argparse.ArgumentParser(description='微信公众号文章下载器一键配置工具')
    parser.add_argument('--install-deps', action='store_true', help='仅安装依赖')
    parser.add_argument('--server-only', action='store_true', help='仅启动服务器')
    parser.add_argument('--setup-autostart', action='store_true', help='设置开机自启动')
    parser.add_argument('--browser', choices=['chrome', 'edge', 'both'], help='选择浏览器扩展安装')
    args = parser.parse_args()
    
    if args.install_deps:
        install_dependencies()
        return
        
    if args.setup_autostart:
        setup_autostart()
        return
        
    if args.server_only:
        start_server()
        # 如果只是启动服务器，让进程继续运行
        try:
            while True:
                time.sleep(86400)  # 睡眠一天
        except KeyboardInterrupt:
            print("服务已停止")
        return
        
    if args.browser:
        open_extension_installation(args.browser)
        return
    
    # 完整设置流程
    print("=== 微信公众号文章下载器一键配置工具 ===")
    
    # 步骤1: 安装依赖
    install_deps = input("是否需要安装依赖 (Flask, Flask-CORS)? (y/n): ").lower()
    if install_deps == 'y':
        install_dependencies()
    
    # 步骤2: 启动服务器
    start_server_input = input("是否开启下载服务? (y/n): ").lower()
    if start_server_input == 'y':
        server_started = start_server()
        if not server_started:
            print("服务启动失败，请检查日志并再次启动server.py。")
    
    # 步骤3: 安装浏览器扩展
    install_extension = input("是否需要安装浏览器扩展? (chrome/edge/n): ").lower()
    if install_extension in ['chrome', 'edge', 'c', 'e']:
        browser_choice = 'chrome' if install_extension in ['chrome', 'c'] else 'edge'
        open_extension_installation(browser_choice)
    elif install_extension == 'y':
        open_extension_installation('both')
    
    # 步骤4: 配置开机自启动
    auto_start = input("是否设置开机自启动服务器? (y/n): ").lower()
    if auto_start == 'y':
        setup_autostart()
    
    print("\n=== 配置完成! ===")
    print("如需下载文章，请:")
    print("1. 确保服务器已启动")
    print("2. 打开微信公众号文章")
    print("3. 点击浏览器扩展图标并选择'下载当前页面'")
    print("4. 如果不再需要该服务，可直接关闭命令行终端")


if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import platform
import subprocess
import shutil
import time
import importlib.util
from pathlib import Path

def print_header():
    """打印安装脚本头部"""
    print("\n" + "="*50)
    print(" 微信公众号文章下载器 - 系统托盘版安装程序")
    print("="*50 + "\n")

def check_python_version():
    """检查Python版本"""
    print("检查Python版本...")
    major, minor = sys.version_info.major, sys.version_info.minor
    
    if major < 3 or (major == 3 and minor < 9):
        print(f"错误: 需要Python 3.9或更高版本，当前版本为{major}.{minor}")
        return False
    
    print(f"✓ Python版本兼容: {major}.{minor}")
    return True

def install_dependencies():
    """安装依赖"""
    print("\n安装必要依赖...")
    
    # 安装PyQt（安静模式）
    print("正在安装PyQt6...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "PyQt6"], 
                      check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        print("✓ PyQt6安装成功")
    except subprocess.CalledProcessError:
        print("! PyQt6安装失败，尝试安装PyQt5...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "PyQt5"], 
                          check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            print("✓ PyQt5安装成功")
        except subprocess.CalledProcessError:
            print("错误: 无法安装PyQt，请手动安装: pip install PyQt6")
            return False
    
    return True

def check_files():
    """检查必要文件"""
    print("\n检查必要文件...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    required_files = [
        ("simple_server.py", "轻量级服务器"),
        ("tray_app.py", "系统托盘应用")
    ]
    
    all_files_present = True
    for filename, description in required_files:
        file_path = os.path.join(current_dir, filename)
        if os.path.exists(file_path):
            print(f"✓ {description}已找到: {filename}")
        else:
            print(f"✗ 缺少{description}: {filename}")
            all_files_present = False
    
    # 检查图标文件
    icon_path = os.path.join(current_dir, "web_extension", "icons", "icon.ico")
    if os.path.exists(icon_path):
        print("✓ 图标文件已找到")
    else:
        print("! 未找到图标文件，将使用系统默认图标")
    
    return all_files_present

def get_tray_app_functions():
    """动态导入tray_app.py中的自启动相关函数"""
    try:
        # 获取tray_app.py的路径
        tray_app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tray_app.py")
        
        # 检查文件是否存在
        if not os.path.exists(tray_app_path):
            print(f"错误: 找不到文件 {tray_app_path}")
            return None, None
        
        # 动态导入模块
        spec = importlib.util.spec_from_file_location("tray_app", tray_app_path)
        tray_app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tray_app)
        
        # 返回需要的函数
        return tray_app.setup_autostart, tray_app.check_autostart_status
    except Exception as e:
        print(f"导入tray_app.py时出错: {str(e)}")
        return None, None

def check_old_autostart():
    """检查并移除旧版本的自启动设置"""
    print("\n检查旧版本自启动...")
    system = platform.system()
    old_autostart_removed = False
    
    if system == "Windows":
        # Windows下检查旧版本的开机自启动批处理文件
        startup_dir = os.path.join(os.environ["APPDATA"], "Microsoft\\Windows\\Start Menu\\Programs\\Startup")
        old_bat_path = os.path.join(startup_dir, "wechat_article_downloader_light.bat")
        
        if os.path.exists(old_bat_path):
            try:
                os.remove(old_bat_path)
                old_autostart_removed = True
                print(f"✓ 已删除旧版本的开机自启动设置: {old_bat_path}")
            except Exception as e:
                print(f"! 无法删除旧版本的开机自启动设置: {str(e)}")
    
    elif system == "Darwin":  # macOS
        # macOS下检查旧版本的plist文件
        home_dir = str(Path.home())
        old_plist_path = os.path.join(home_dir, "Library/LaunchAgents/com.wechatarticle.downloader.light.plist")
        
        if os.path.exists(old_plist_path):
            try:
                # 先卸载启动项
                subprocess.run(["launchctl", "unload", old_plist_path], capture_output=True)
                # 删除文件
                os.remove(old_plist_path)
                old_autostart_removed = True
                print(f"✓ 已删除旧版本的开机自启动设置: {old_plist_path}")
            except Exception as e:
                print(f"! 无法删除旧版本的开机自启动设置: {str(e)}")
    
    if not old_autostart_removed:
        print("✓ 未检测到旧版本的开机自启动设置")
    
    return True

def create_desktop_shortcut(create=True, icon_path=None):
    """创建桌面快捷方式
    
    Args:
        create (bool): 是否创建桌面快捷方式
        icon_path (str): 自定义图标路径
    """
    if not create:
        print("\n跳过创建桌面快捷方式")
        return True
        
    print("\n创建桌面快捷方式...")
    system = platform.system()
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tray_app.py")
    
    # 确定图标路径
    if not icon_path:
        # 使用默认图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               "web_extension/icons/white-bg-icon.ico")
    
    if system == "Windows":
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_path = os.path.join(desktop_path, "微信公众号文章下载器.bat")
        
        # Windows批处理文件中可以传递图标路径参数
        with open(shortcut_path, "w") as f:
            f.write(f'@echo off\nstart /min "" "{sys.executable}" "{script_path}" --icon "{icon_path}"\n')
        
        print(f"✓ 已在桌面创建快捷方式: {shortcut_path}")
    
    elif system == "Darwin":  # macOS
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_path = os.path.join(desktop_path, "微信公众号文章下载器.command")
        
        # macOS脚本中可以传递图标路径参数
        with open(shortcut_path, "w") as f:
            f.write(f'#!/bin/bash\n"{sys.executable}" "{script_path}" --icon "{icon_path}"\n')
        
        # 设置可执行权限
        os.chmod(shortcut_path, 0o755)
        
        print(f"✓ 已在桌面创建快捷方式: {shortcut_path}")
    
    else:
        print("! 当前系统不支持创建桌面快捷方式")
        return False
    
    return True

def start_application():
    """启动应用程序"""
    print("\n现在启动应用程序...")
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tray_app.py")
    
    # 启动应用程序
    if platform.system() == "Windows":
        subprocess.Popen([sys.executable, script_path], 
                       creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        subprocess.Popen([sys.executable, script_path],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    
    print("✓ 应用程序已启动，请查看系统托盘图标")
    return True

def main():
    """主函数"""
    print_header()
    
    # 检查Python版本
    if not check_python_version():
        input("\n按回车键退出...")
        sys.exit(1)
    
    # 安装依赖
    if not install_dependencies():
        input("\n安装依赖失败，按回车键退出...")
        sys.exit(1)
    
    # 检查文件
    if not check_files():
        input("\n文件检查失败，按回车键退出...")
        sys.exit(1)
    
    # 检查旧版本自启动
    check_old_autostart()
    
    # 询问是否创建桌面快捷方式
    create_shortcut = input("\n是否创建桌面快捷方式? (y/n, 默认y): ").strip().lower()
    create_shortcut = create_shortcut == "" or create_shortcut == "y"
    
    # 如果用户选择创建快捷方式，询问是否使用自定义图标
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                     "web_extension/icons/icon.ico")
             
    # 创建桌面快捷方式
    create_desktop_shortcut(create=create_shortcut, icon_path=icon_path)
    
    # 询问是否设置开机自启动
    autostart_choice = input("\n是否设置开机自启动? (y/n, 默认y): ").strip().lower()
    if autostart_choice == "" or autostart_choice == "y":
        print("\n配置开机自启动...")
        
        # 获取tray_app.py中的函数
        setup_autostart, _ = get_tray_app_functions()
        
        if setup_autostart and setup_autostart(True):
            print("✓ 开机自启动设置成功")
        else:
            print("! 开机自启动设置失败，可能是由于权限问题或找不到相关函数")
    else:
        print("\n跳过设置开机自启动")
    
    # 询问是否立即启动应用
    print("\n安装完成！")
    choice = input("是否立即启动应用? (y/n, 默认y): ").strip().lower()
    if choice == "" or choice == "y":
        start_application()
    
    print("\n感谢使用微信公众号文章下载器！")
    print("应用将在系统托盘中运行，点击托盘图标可以查看菜单")
    input("\n按回车键退出安装程序...")

if __name__ == "__main__":
    main()

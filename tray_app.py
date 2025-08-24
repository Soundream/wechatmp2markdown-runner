#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import platform
import subprocess
import signal
import threading
import socket
import time
from pathlib import Path

# 尝试导入PyQt6，如果不可用，则尝试PyQt5
try:
    from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
    from PyQt6.QtGui import QIcon, QAction, QCursor
    from PyQt6.QtCore import QObject, pyqtSignal, QTimer
    PYQT_VERSION = 6
except ImportError:
    try:
        from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
        from PyQt5.QtGui import QIcon, QAction, QCursor
        from PyQt5.QtCore import QObject, pyqtSignal, QTimer
        PYQT_VERSION = 5
    except ImportError:
        print("错误: 请先安装PyQt6或PyQt5")
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
        response = urllib.request.urlopen(f"http://localhost:{port}/status")
        return True
    except (urllib.error.URLError, ConnectionRefusedError):
        return False

# 配置开机自启动
def setup_autostart(enable=True):
    """配置开机自启动"""
    system = platform.system()
    # 获取当前脚本路径
    script_path = os.path.abspath(__file__)
    app_name = "wechat_article_downloader"  # 与旧版本保持一致
    
    # Windows系统
    if system == "Windows":
        startup_dir = os.path.join(os.environ["APPDATA"], 
                                  "Microsoft\\Windows\\Start Menu\\Programs\\Startup")
        bat_path = os.path.join(startup_dir, f"{app_name}.bat")
        
        if enable:
            # 创建批处理文件
            with open(bat_path, "w") as f:
                f.write(f'@echo off\nstart /min "" "{sys.executable}" "{script_path}"\n')
            print(f"已启用开机自启动")
            return True
        else:
            # 删除批处理文件
            if os.path.exists(bat_path):
                os.remove(bat_path)
                print("已禁用开机自启动")
                return True
    
    # macOS系统
    elif system == "Darwin":
        home_dir = str(Path.home())
        launch_agents_dir = os.path.join(home_dir, "Library/LaunchAgents")
        os.makedirs(launch_agents_dir, exist_ok=True)
        plist_path = os.path.join(launch_agents_dir, f"com.{app_name}.plist")
        
        if enable:
            # 创建plist文件
            plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{app_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{script_path}</string>
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
            print(f"已启用开机自启动")
            return True
        else:
            # 卸载并删除启动项
            if os.path.exists(plist_path):
                subprocess.run(["launchctl", "unload", plist_path])
                os.remove(plist_path)
                print("已禁用开机自启动")
                return True
    
    return False

# 检查自启动状态
def check_autostart_status():
    """检查自启动状态"""
    system = platform.system()
    app_name = "wechat_article_downloader"  # 与旧版本保持一致
    
    if system == "Windows":
        startup_dir = os.path.join(os.environ["APPDATA"], 
                                  "Microsoft\\Windows\\Start Menu\\Programs\\Startup")
        bat_path = os.path.join(startup_dir, f"{app_name}.bat")
        return os.path.exists(bat_path)
    
    elif system == "Darwin":
        home_dir = str(Path.home())
        plist_path = os.path.join(home_dir, 
                                 f"Library/LaunchAgents/com.{app_name}.plist")
        return os.path.exists(plist_path)
    
    return False

# 进程通信信号
class Signals(QObject):
    status_update = pyqtSignal(str)
    server_started = pyqtSignal()
    server_stopped = pyqtSignal()

# 主托盘应用类
class WechatArticleDownloaderTray:
    def __init__(self, custom_icon=None):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # 设置应用名称
        self.app.setApplicationName("微信公众号文章下载器")
        
        # 保存自定义图标路径
        self.custom_icon = custom_icon
        
        # 初始自启动状态检查
        self.autostart_enabled = check_autostart_status()
        
        # 设置托盘图标
        self.setup_tray()
        
        # 设置信号
        self.signals = Signals()
        
        # 设置服务状态
        self.server_process = None
        self.server_running = False
        
        # 服务状态检查定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_service_status)
        self.status_timer.start(5000)  # 每5秒检查一次服务状态
        
        # 初始状态检查
        QTimer.singleShot(1000, self.check_service_status)
        
        # 确保初始状态下的按钮正确连接到正确的函数
        try:
            self.start_action.triggered.disconnect()
        except TypeError:
            # 初始化时可能还没有连接
            pass
        self.start_action.triggered.connect(self.start_service)
    
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
        
        # 创建隐藏的操作用于状态追踪
        self.status_action = QAction("服务状态：检查中...")
        self.status_action.setVisible(False)
        self.menu.addAction(self.status_action)
        
        self.start_action = QAction("启动服务")
        self.start_action.setVisible(False)
        self.menu.addAction(self.start_action)
        
        self.autostart_action = QAction("开机自启动")
        self.autostart_action.setCheckable(True)
        self.autostart_action.setChecked(self.autostart_enabled)
        self.autostart_action.setVisible(False)
        self.menu.addAction(self.autostart_action)
        
        # 退出选项
        self.exit_action = QAction("退出")
        self.exit_action.triggered.connect(self.exit_app)
        self.menu.addAction(self.exit_action)
        
        # 创建一个简单轻量级菜单，替代标准上下文菜单
        self.lightweight_menu = QMenu()
        exit_action = QAction("退出")
        exit_action.triggered.connect(self.quick_exit)
        self.lightweight_menu.addAction(exit_action)
        
        # 不设置标准上下文菜单，而是手动处理右键事件
        self.tray_icon.show()
        
        # 设置点击托盘图标的行为
        self.tray_icon.activated.connect(self.tray_icon_activated)
    
    def tray_icon_activated(self, reason):
        """处理托盘图标的点击事件"""
        # 检测右键点击
        if reason == QSystemTrayIcon.ActivationReason.Context:
            # 快速显示轻量级菜单，不进行任何状态检查
            self.show_lightweight_menu()
        # 左键点击不做任何处理
    
    def show_lightweight_menu(self):
        """显示轻量级菜单"""
        # 获取鼠标位置
        cursor_pos = QCursor.pos()
        # 在当前鼠标位置显示菜单，不进行任何状态检查或阻塞操作
        self.lightweight_menu.popup(cursor_pos)
    
    def quick_exit(self):
        """快速退出，不进行确认或等待，立即启动退出过程"""
        # 立即隐藏菜单和托盘图标，给用户立即反馈
        self.lightweight_menu.hide()
        self.tray_icon.setVisible(False)
        
        # 在后台线程中处理退出操作
        threading.Thread(target=self._background_exit, daemon=True).start()
        # 立即退出主UI线程
        QTimer.singleShot(10, QApplication.quit)
    
    def _background_exit(self):
        """在后台停止服务"""
        try:
            # 尝试停止服务
            if self.server_running:
                self._stop_service_thread()
        except:
            # 忽略任何错误
            pass
    
    def check_service_status(self):
        """检查服务状态"""
        server_running = check_server_running()
        if server_running != self.server_running:
            self.server_running = server_running
            self.update_service_status()
    
    def update_service_status(self):
        """更新服务状态显示"""
        if self.server_running:
            self.status_action.setText("服务状态：运行中")
            self.start_action.setText("停止服务")
            try:
                self.start_action.triggered.disconnect()
            except TypeError:
                pass
            self.start_action.triggered.connect(self.stop_service)
        else:
            self.status_action.setText("服务状态：已停止")
            self.start_action.setText("启动服务")
            try:
                self.start_action.triggered.disconnect()
            except TypeError:
                pass
            self.start_action.triggered.connect(self.start_service)
    
    def start_service(self):
        """启动服务"""
        self.status_action.setText("服务状态：正在启动...")
        QApplication.processEvents()
        
        # 在新线程中启动服务
        threading.Thread(target=self._start_service_thread, daemon=True).start()
    
    def _start_service_thread(self):
        """在独立线程中启动服务"""
        try:
            # 获取simple_server.py的路径
            server_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                       "simple_server.py")
            
            # 检查端口是否已被占用
            if is_port_in_use(5001):
                self.signals.status_update.emit("端口5001已被占用，无法启动服务")
                return
            
            # 启动服务
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
            for _ in range(5):
                if check_server_running():
                    self.signals.server_started.emit()
                    return
                time.sleep(1)
            
            self.signals.status_update.emit("服务启动超时，请检查日志")
        except Exception as e:
            self.signals.status_update.emit(f"启动服务出错: {str(e)}")
    
    def stop_service(self):
        """停止服务"""
        self.status_action.setText("服务状态：正在停止...")
        QApplication.processEvents()
        
        # 在新线程中停止服务
        threading.Thread(target=self._stop_service_thread, daemon=True).start()
    
    def _stop_service_thread(self):
        """在独立线程中停止服务"""
        try:
            # 尝试通过进程终止
            if self.server_process:
                if platform.system() == "Windows":
                    self.server_process.terminate()
                else:
                    self.server_process.kill()
            
            # 尝试终止所有运行中的simple_server进程
            if platform.system() == "Windows":
                subprocess.run(["taskkill", "/F", "/IM", "python.exe", "/T"], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # 查找并终止进程
                try:
                    pids = subprocess.check_output(
                        ["pgrep", "-f", "simple_server.py"], 
                        text=True
                    ).strip().split("\n")
                    
                    for pid in pids:
                        if pid:
                            os.kill(int(pid), signal.SIGTERM)
                except:
                    pass
            
            # 等待服务停止
            for _ in range(5):
                if not check_server_running():
                    self.signals.server_stopped.emit()
                    return
                time.sleep(1)
            
            self.signals.status_update.emit("无法停止服务，请手动终止进程")
        except Exception as e:
            self.signals.status_update.emit(f"停止服务出错: {str(e)}")
    
    def toggle_autostart(self, checked):
        """切换开机自启动状态"""
        try:
            if checked:
                success = setup_autostart(True)
            else:
                success = setup_autostart(False)
            
            if success:
                self.autostart_enabled = checked
            else:
                # 恢复复选框状态
                self.autostart_action.setChecked(self.autostart_enabled)
                self.show_message("设置失败", "无法配置开机自启动，请检查权限")
        except Exception as e:
            self.autostart_action.setChecked(self.autostart_enabled)
            self.show_message("设置出错", f"配置开机自启动时出错: {str(e)}")
    
    def show_message(self, title, message):
        """显示消息通知"""
        self.tray_icon.showMessage(title, message)
    
    def exit_app(self):
        """退出应用"""
        if self.server_running:
            reply = QMessageBox.question(
                None, "确认退出", 
                "服务正在运行中，确定要退出吗？\n退出后将无法下载微信公众号文章。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
            
            # 停止服务
            self.stop_service()
            # 等待一会儿确保服务已停止
            time.sleep(1)
        
        # 退出应用
        QApplication.quit()
    
    def run(self):
        """运行应用"""
        # 连接信号到槽
        self.signals.status_update.connect(lambda msg: self.status_action.setText(f"服务状态：{msg}"))
        self.signals.server_started.connect(lambda: self.update_service_status())
        self.signals.server_stopped.connect(lambda: self.update_service_status())
        
        # 显示欢迎消息
        self.tray_icon.showMessage(
            "公众号web下载器",
            "已在后台运行，可以通过浏览器扩展下载文章",
            QSystemTrayIcon.MessageIcon.Information,
            2000  # 显示2秒
        )
        
        # 无论服务状态如何，直接启动服务
        QTimer.singleShot(1000, self.start_service)
        
        # 运行应用
        sys.exit(self.app.exec())

# 初始化时询问是否开启自启动
def prompt_autostart():
    """询问用户是否启用开机自启动"""
    print("\n=== 微信公众号文章下载器系统托盘应用 ===\n")
    print("此应用将在系统托盘中运行，提供微信公众号文章下载服务")
    
    # 检查是否已经配置了自启动
    current_status = check_autostart_status()
    if current_status:
        return True
    
    # 询问是否启用自启动
    choice = input("\n是否设置开机自启动? (默认启用，y/n): ").strip().lower()
    if choice == "" or choice == "y":
        if setup_autostart(True):
            print("已设置开机自启动")
        else:
            print("无法设置开机自启动，可能没有足够权限")
        return True
    else:
        print("未设置开机自启动，您需要手动启动应用才能使用下载功能")
        return False

# 主函数
def main():
    """主函数"""
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='微信公众号文章下载器系统托盘应用')
    parser.add_argument('--quiet', '-q', action='store_true', help='安静模式，不显示欢迎提示')
    parser.add_argument('--icon', help='指定自定义图标路径')
    args = parser.parse_args()
    
    # 如果不是安静模式，询问自启动
    if not args.quiet:
        prompt_autostart()
    
    # 运行系统托盘应用
    tray_app = WechatArticleDownloaderTray(custom_icon=args.icon)
    tray_app.run()

if __name__ == "__main__":
    main()

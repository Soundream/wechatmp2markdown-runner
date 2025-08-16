import subprocess
import platform
import json
import os
import sys


def get_browser_active_tab_info():
    """
    获取当前活跃浏览器标签页的标题和URL，支持Mac和Windows系统。
    注意：在非GUI环境下调用此函数将返回空结果。
    
    Returns:
        tuple: (title, url)
    """
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return _get_macos_browser_tab_info()
    elif system == "Windows":  # Windows
        return _get_windows_browser_tab_info()
    else:
        print("当前系统不支持自动获取浏览器URL，请手动传入URL参数")
        return '', ''


def _get_macos_browser_tab_info():
    """
    使用AppleScript获取macOS上浏览器标签页信息
    """
    # 先尝试Chrome
    chrome_script = '''
    tell application "Google Chrome"
        set theTab to active tab of front window
        set theTitle to title of theTab
        set theUrl to URL of theTab
        return theTitle & linefeed & theUrl
    end tell
    '''
    try:
        result = subprocess.run(['osascript', '-e', chrome_script], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n', 1)
            if len(lines) == 2:
                return lines[0], lines[1]
    except Exception:
        pass
    
    # 再尝试Edge
    edge_script = '''
    tell application "Microsoft Edge"
        set theTab to active tab of front window
        set theTitle to title of theTab
        set theUrl to URL of theTab
        return theTitle & linefeed & theUrl
    end tell
    '''
    try:
        result = subprocess.run(['osascript', '-e', edge_script], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n', 1)
            if len(lines) == 2:
                return lines[0], lines[1]
    except Exception:
        pass
    
    return '', ''


def _get_windows_browser_tab_info():
    """
    在Windows系统上尝试获取浏览器标签页信息
    注意：Windows无法直接获取，通常需要通过插件提供URL
    """
    # Windows无法像macOS那样直接通过脚本获取浏览器URL
    # 这里可以扩展其他方法尝试获取浏览器URL（如通过第三方库）
    print("Windows系统暂不支持自动获取浏览器URL，请通过命令行参数或插件传入URL")
    return '', ''


def clean_url(raw_url):
    """
    清洗并提取 URL 的核心部分。
    
    Args:
        raw_url (str): 原始的、可能带有空格和换行的 URL 字符串。
    
    Returns:
        str: 核心 URL 字符串。
    """
    if not raw_url:
        return ''
        
    # 1. 去除所有首尾的空白字符
    trimmed_url = raw_url.strip()
    
    # 2. 以问号 (?) 为分隔符，只取第一部分
    core_url = trimmed_url.split('?')[0]
    
    return core_url


# 兼容旧版本调用
get_chrome_active_tab_info = get_browser_active_tab_info

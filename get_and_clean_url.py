import subprocess


def get_chrome_active_tab_info():
    """
    使用 AppleScript 获取当前聚焦的 Chrome 标签页的标题和 URL（仅限 macOS）。
    Returns:
        tuple: (title, url)
    """
    script = '''
    tell application "Google Chrome"
        set theTab to active tab of front window
        set theTitle to title of theTab
        set theUrl to URL of theTab
        return theTitle & linefeed & theUrl
    end tell
    '''
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n', 1)
    if len(lines) == 2:
        return lines[0], lines[1]
    else:
        return '', ''
    
def clean_url(raw_url):
    """
    清洗并提取 URL 的核心部分。
    
    Args:
        raw_url (str): 原始的、可能带有空格和换行的 URL 字符串。
    
    Returns:
        str: 核心 URL 字符串。
    """
    # 1. 去除所有首尾的空白字符
    trimmed_url = raw_url.strip()
    
    # 2. 以问号 (?) 为分隔符，只取第一部分
    core_url = trimmed_url.split('?')[0]
    
    return core_url

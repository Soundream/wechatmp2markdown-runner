import os
import platform

from download_wechat_article import download_wechat_article
from get_and_clean_url import get_chrome_active_tab_info, clean_url


title, raw_url = get_chrome_active_tab_info()
print(f"\n当前标签页标题: {title}\n")

cleaned_url = clean_url(raw_url)


if platform.system() == "Darwin":  # macOS
    app_path = '/Users/intern/Documents/GitHub/wechatmp2markdown-runner'
elif platform.system() == "Windows":
    app_path = r'C:\Users\intern\Documents\GitHub\wechatmp2markdown-runner'
else:
    app_path = os.path.abspath('./wechatmp2markdown-runner')  # 其他系统默认


# 调用函数
download_wechat_article(
    url=cleaned_url,
    app_path=app_path,
)


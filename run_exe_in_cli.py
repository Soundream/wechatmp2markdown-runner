import os
import platform
import argparse
import sys

from download_wechat_article import download_wechat_article
from get_and_clean_url import get_browser_active_tab_info, clean_url


def main():
    # 创建命令行解析器
    parser = argparse.ArgumentParser(description='下载微信公众号文章并转为Markdown')
    parser.add_argument('--url', '-u', type=str, help='微信公众号文章URL，如果不提供则尝试从浏览器获取')
    parser.add_argument('--output', '-o', type=str, default='./downloads', help='保存文件的输出路径')
    parser.add_argument('--image-mode', '-i', type=str, default='save', choices=['save', 'base64'], help='图片保存模式：保存为文件或base64编码')
    parser.add_argument('--app-path', '-p', type=str, help='应用程序路径，默认自动检测')
    args = parser.parse_args()

    # 获取URL：优先使用命令行参数，否则尝试从浏览器获取
    raw_url = args.url
    title = "未知标题"
    
    if not raw_url:
        title, raw_url = get_browser_active_tab_info()
        print(f"\n当前标签页标题: {title}\n")
        
        if not raw_url:
            print("错误: 未能获取URL。请指定--url参数或确保浏览器正在运行并聚焦于微信公众号文章页面。")
            sys.exit(1)
    
    cleaned_url = clean_url(raw_url)
    print(f"处理URL: {cleaned_url}\n")

    # 应用路径：优先使用命令行参数，否则自动检测
    if args.app_path:
        app_path = args.app_path
    else:
        # 自动检测应用路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        if platform.system() == "Darwin":  # macOS
            executable = "wechatmp2markdown-v1.1.11_osx_amd64"
        elif platform.system() == "Windows":  # Windows
            executable = "wechatmp2markdown-v1.1.11_windows_amd64.exe"
        else:  # Linux或其他
            executable = "wechatmp2markdown-v1.1.11_linux_amd64"
            
        # 检查可执行文件是否存在于当前目录
        if not os.path.exists(os.path.join(script_dir, executable)) and platform.system() == "Windows":
            # Windows可能使用了没有.exe后缀的文件名
            executable = "wechatmp2markdown-v1.1.11_windows_amd64"
            
        # 如果当前目录中没有可执行文件，尝试使用script_dir作为app_path
        app_path = script_dir

    # 调用下载函数
    download_wechat_article(
        url=cleaned_url,
        app_path=app_path,
        output_path=args.output,
        image_mode=args.image_mode
    )

    print("\n处理完成！")


if __name__ == "__main__":
    main()


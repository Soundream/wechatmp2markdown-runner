import subprocess
import os
import shlex

debug = False

def download_wechat_article(url, app_path, output_path='./downloads', image_mode='save'):
    """
    下载微信公众号文章并将其保存为Markdown文件。

    Args:
        url (str): 微信文章的完整URL。
        output_path (str): 保存文件的目录路径。
        image_mode (str): 图片保存模式，可选 'save' 或 'base64'。
    """
    # 构造 CLI 命令
    command = [
        './wechatmp2markdown-v1.1.11_osx_amd64',  # 你的 CLI 工具名称
        url,
        output_path,
        f'--image={image_mode}',
    ]

    print("执行CLI命令", shlex.join(command), "\n")

    downloads_path = os.path.join(app_path, 'downloads')
    os.makedirs(downloads_path, exist_ok=True)
    
    # 运行命令
    try:
        result = subprocess.run(command, 
                                cwd=app_path,
                                check=True, capture_output=True, text=True)
        print("\n下载成功！") if debug else None

    except subprocess.CalledProcessError as e:
        print("下载失败。") if debug else None

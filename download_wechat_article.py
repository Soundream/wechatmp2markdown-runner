import subprocess
import os
import shlex
import platform

debug = False

def download_wechat_article(url, app_path, output_path='./downloads', image_mode='save'):
    """
    下载微信公众号文章并将其保存为Markdown文件。

    Args:
        url (str): 微信文章的完整URL。
        app_path (str): 应用程序所在路径。
        output_path (str): 保存文件的目录路径。
        image_mode (str): 图片保存模式，可选 'save' 或 'base64'。
    """
    system = platform.system()
    
    # 确定可执行文件名称
    if system == "Darwin":  # macOS
        executable = "wechatmp2markdown-v1.1.11_osx_amd64"
    elif system == "Windows":  # Windows
        executable = "wechatmp2markdown-v1.1.11_win64.exe"
    else:  # Linux或其他系统
        executable = "wechatmp2markdown-v1.1.11_linux_amd64"
        
    # 在Windows系统上，处理命令行参数的特殊情况
    if system == "Windows":
        # 使用cmd.exe明确执行命令，避免PowerShell参数解析问题
        command = [
            "cmd.exe",
            "/c",
            os.path.join(app_path, executable),
            url,
            output_path,
            f'--image={image_mode}',
        ]
    else:
        # Unix系统需要加上./前缀来执行当前目录下的可执行文件
        command = [
            f'./{executable}',
            url,
            output_path,
            f'--image={image_mode}',
        ]
    
    # 输出调试信息
    print(f"执行CLI命令: {shlex.join(command)}\n")
    
    # 确保输出目录存在
    # 判断output_path是否为相对路径
    if not os.path.isabs(output_path):
        # 如果是相对路径，转换为相对于app_path的完整路径
        downloads_path = os.path.join(app_path, output_path)
    else:
        # 如果已经是绝对路径，直接使用
        downloads_path = output_path
        
    os.makedirs(downloads_path, exist_ok=True)
    
    # 运行命令
    try:
        print(f"工作目录: {app_path}")
        print(f"检查可执行文件: {os.path.exists(os.path.join(app_path, executable))}")
        
        # 设置debug为True以显示所有输出
        debug = True
        
        result = subprocess.run(command, 
                              cwd=app_path,
                              check=True, capture_output=True, text=True)
        print("\n下载成功！")
        print("输出结果:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"下载失败: {e}")
        print("错误输出:")
        print(e.stderr)
        print("\n尝试诊断问题:")
        # 检查文件是否存在
        if not os.path.exists(os.path.join(app_path, executable)):
            print(f"错误: 可执行文件 '{executable}' 不存在于 '{app_path}'")
        # 检查目录权限
        try:
            test_file = os.path.join(downloads_path, "test_write.txt")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            print(f"输出目录 '{downloads_path}' 可写入")
        except Exception as write_error:
            print(f"错误: 无法写入输出目录 '{downloads_path}': {write_error}")

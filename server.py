from flask import Flask, request, jsonify
from flask_cors import CORS
import platform
import os
from download_wechat_article import download_wechat_article
from get_and_clean_url import clean_url

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        # 同时支持Chrome和Edge的扩展
        "origins": ["chrome-extension://*", "extension://*", "edge-extension://*", "moz-extension://*"],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# 获取脚本所在目录作为应用路径
app_path = os.path.dirname(os.path.abspath(__file__))

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.json
        url = data.get('url')
        if not url:
            return jsonify({'status': 'error', 'message': '未提供URL'}), 400
            
        cleaned_url = clean_url(url)
        download_wechat_article(url=cleaned_url, app_path=app_path)
        return jsonify({'status': 'success', 'message': '下载成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'下载失败: {str(e)}'})

@app.route('/status', methods=['GET'])
def status():
    """检查服务器状态"""
    return jsonify({
        'status': 'running', 
        'app_path': app_path,
        'platform': platform.system()
    })

def main():
    """主函数，启动Flask服务器"""
    print(f"Flask服务器启动中，应用路径: {app_path}")
    print(f"运行平台: {platform.system()}")
    # 默认在5001端口运行，如果有需要可以添加参数支持
    app.run(host='127.0.0.1', port=5001)

if __name__ == '__main__':
    main()
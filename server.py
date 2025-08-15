from flask import Flask, request, jsonify
from flask_cors import CORS
import platform
import os
from download_wechat_article import download_wechat_article
from get_and_clean_url import clean_url

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["chrome-extension://*"],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

if platform.system() == "Darwin":  # macOS
    app_path = '/Users/intern/Documents/GitHub/wechatmp2markdown-runner'
elif platform.system() == "Windows":
    app_path = r'C:\Users\intern\Documents\GitHub\wechatmp2markdown-runner'
else:
    app_path = os.path.abspath('./wechatmp2markdown-runner')

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
        return jsonify({'status': 'error', 'message': '下载失败'})

if __name__ == '__main__':
    print("Flask server starting...")
    app.run(port=5001)
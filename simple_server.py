import http.server
import socketserver
import json
import socket
import threading
import time
import os
import sys
import platform
import struct
from urllib.parse import parse_qs
from pathlib import Path
from download_wechat_article import download_wechat_article
from get_and_clean_url import clean_url

# 服务器是否常驻（不自动关闭）
IS_PERMANENT_SERVER = True

# 默认端口和超时时间
DEFAULT_PORT = 5001
DEFAULT_TIMEOUT_MINUTES = 15

# 全局变量
shutdown_timer = None
server_instance = None
is_server_running = False

class DownloadRequestHandler(http.server.BaseHTTPRequestHandler):
    """处理下载请求的HTTP处理器"""
    
    def _set_response_headers(self, content_type='application/json'):
        """设置HTTP响应头"""
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_OPTIONS(self):
        """处理预检请求"""
        self._set_response_headers()
        self.wfile.write(b'')
    
    def do_GET(self):
        """处理GET请求，主要用于状态检查"""
        global shutdown_timer
        
        # 重置关闭计时器
        if shutdown_timer:
            shutdown_timer.cancel()
            start_shutdown_timer()
            
        if self.path == '/status':
            self._set_response_headers()
            response = {
                'status': 'running', 
                'app_path': os.path.dirname(os.path.abspath(__file__)),
                'platform': platform.system()
            }
            self.wfile.write(json.dumps(response).encode())
        elif self.path.startswith('/download-status/'):
            # 提取下载ID
            download_id = self.path.split('/download-status/')[1]
            self._set_response_headers()
            
            # 在实际应用中，这里应该查询存储的下载状态
            # 简化实现，返回通用消息
            response = {
                'status': 'unknown',
                'message': '此功能尚未完全实现，请查看控制台日志获取下载状态'
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self._set_response_headers()
            response = {'status': 'error', 'message': '未知路径'}
            self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """处理POST请求，用于下载文章"""
        global shutdown_timer
        
        # 重置关闭计时器
        if shutdown_timer:
            shutdown_timer.cancel()
            start_shutdown_timer()
            
        if self.path == '/download':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode())
                url = data.get('url')
                timeout = data.get('timeout', DEFAULT_TIMEOUT_MINUTES)
                
                if not url:
                    self._set_response_headers()
                    response = {'status': 'error', 'message': '未提供URL'}
                    self.wfile.write(json.dumps(response).encode())
                    return
                    
                # 生成唯一下载ID用于状态跟踪
                import uuid
                download_id = str(uuid.uuid4())
                
                # 立即返回响应，表示已接收请求
                self._set_response_headers()
                response = {
                    'status': 'received', 
                    'message': '请求已接收，正在处理下载',
                    'download_id': download_id
                }
                self.wfile.write(json.dumps(response).encode())
                
                # 在新线程中处理下载，不阻塞响应
                threading.Thread(
                    target=self._handle_download,
                    args=(url, timeout, download_id)
                ).start()
                
            except json.JSONDecodeError:
                self._set_response_headers()
                response = {'status': 'error', 'message': 'JSON解析错误'}
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                self._set_response_headers()
                response = {'status': 'error', 'message': f'请求处理错误: {str(e)}'}
                self.wfile.write(json.dumps(response).encode())
        else:
            self._set_response_headers()
            response = {'status': 'error', 'message': '未知路径'}
            self.wfile.write(json.dumps(response).encode())
    
    def _handle_download(self, url, timeout, download_id):
        """在后台线程中处理下载请求"""
        try:
            # 更新超时时间
            global DEFAULT_TIMEOUT_MINUTES
            DEFAULT_TIMEOUT_MINUTES = int(timeout)
            
            # 获取应用路径
            app_path = os.path.dirname(os.path.abspath(__file__))
            
            # 清理URL
            cleaned_url = clean_url(url)
            
            # 更新下载状态为处理中
            self._update_download_status(download_id, "processing", "正在下载文章...")
            
            # 执行下载
            result = download_wechat_article(url=cleaned_url, app_path=app_path)
            
            # 下载成功，更新状态
            output_path = os.path.join(app_path, "downloads")
            self._update_download_status(download_id, "completed", "下载完成", {
                "output_path": output_path,
                "article_title": result.get("title", "未知标题")
            })
            
        except Exception as e:
            error_msg = str(e)
            print(f"下载处理错误: {error_msg}")
            # 更新下载状态为失败
            self._update_download_status(download_id, "failed", f"下载失败: {error_msg}")
    
    def _update_download_status(self, download_id, status, message, details=None):
        """更新下载状态，存储在内存中供查询"""
        # 在实际应用中，这里可以使用数据库或文件存储状态
        # 本示例中简单地打印状态信息
        status_info = {
            "download_id": download_id,
            "status": status,
            "message": message,
            "timestamp": time.time()
        }
        
        if details:
            status_info.update(details)
        
        print(f"下载状态更新: {json.dumps(status_info)}")
        
        # 这里可以添加推送通知的逻辑，如WebSocket推送等
        # 简化实现，只在控制台输出

def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_shutdown_timer():
    """开始计时器，超时后关闭服务器"""
    global shutdown_timer, server_instance, is_server_running
    
    # 如果是常驻服务器，则不启动关闭计时器
    if IS_PERMANENT_SERVER:
        print("服务器设置为常驻模式，不会自动关闭")
        return
    
    def shutdown_server():
        global server_instance, is_server_running
        if server_instance:
            print(f"服务器空闲 {DEFAULT_TIMEOUT_MINUTES} 分钟，正在关闭...")
            is_server_running = False
            server_instance.shutdown()
    
    shutdown_timer = threading.Timer(DEFAULT_TIMEOUT_MINUTES * 60, shutdown_server)
    shutdown_timer.daemon = True
    shutdown_timer.start()

def start_server(port=DEFAULT_PORT):
    """启动HTTP服务器"""
    global server_instance, is_server_running
    
    # 检查端口是否已被占用
    if is_port_in_use(port):
        print(f"端口 {port} 已被占用，服务可能已在运行")
        return False
    
    try:
        # 创建HTTP服务器
        server_instance = socketserver.TCPServer(("127.0.0.1", port), DownloadRequestHandler)
        is_server_running = True
        
        # 启动超时关闭计时器（如果不是常驻模式）
        start_shutdown_timer()
        
        if IS_PERMANENT_SERVER:
            print(f"HTTP服务已启动在端口 {port}，服务器设置为常驻模式")
        else:
            print(f"HTTP服务已启动在端口 {port}，闲置 {DEFAULT_TIMEOUT_MINUTES} 分钟后将自动关闭")
        
        # 在主线程中运行服务器
        server_instance.serve_forever()
        
        print("服务器已关闭")
        return True
    
    except Exception as e:
        print(f"启动服务器时出错: {str(e)}")
        return False

def main():
    """主入口函数"""
    import argparse
    global DEFAULT_TIMEOUT_MINUTES
    
    parser = argparse.ArgumentParser(description='轻量级微信文章下载服务器')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='服务器端口号')
    parser.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT_MINUTES, help='自动关闭超时时间(分钟)')
    
    args = parser.parse_args()
    
    DEFAULT_TIMEOUT_MINUTES = args.timeout
    
    start_server(args.port)

if __name__ == '__main__':
    main()

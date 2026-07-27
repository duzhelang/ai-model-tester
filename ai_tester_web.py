#!/usr/bin/env python3
"""AI 模型连通性测试工具 - 网页版（优化启动速度 + 防重复启动 + exe 支持）"""

import http.server
import json
import threading
import webbrowser
import os
import sys
import socket
import time
import tempfile

# ==================== 资源路径（兼容 PyInstaller） ====================
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = sys._MEIPASS
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = SCRIPT_DIR


def resource_path(filename):
    """优先从 exe 同级目录读取（用户可覆盖），否则从打包资源读取"""
    local = os.path.join(SCRIPT_DIR, filename)
    if os.path.exists(local):
        return local
    bundled = os.path.join(BUNDLE_DIR, filename)
    if os.path.exists(bundled):
        return bundled
    return local


# ==================== 锁文件（防重复启动） ====================
LOCK_FILE = os.path.join(tempfile.gettempdir(), "ai_model_tester.lock")


def write_lock(port):
    try:
        with open(LOCK_FILE, "w") as f:
            f.write("%d\n%d" % (port, os.getpid()))
    except Exception:
        pass


def read_lock():
    try:
        with open(LOCK_FILE, "r") as f:
            lines = f.read().strip().split("\n")
            return int(lines[0]), int(lines[1]) if len(lines) > 1 else 0
    except Exception:
        return None, None


def clear_lock():
    try:
        os.remove(LOCK_FILE)
    except Exception:
        pass


def is_process_alive(pid):
    if pid <= 0:
        return False
    try:
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(0x1000, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return True
        else:
            os.kill(pid, 0)
        return False
    except Exception:
        return False


def is_port_listening(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def check_existing():
    """快速检测已有实例：先查锁文件，再验证端口"""
    port, pid = read_lock()
    if port and is_port_listening(port):
        return port
    for p in range(8765, 8770):
        if p != port and is_port_listening(p):
            return p
    return None


def find_available_port():
    for port in range(8765, 8800):
        if not is_port_listening(port):
            return port
    return None


# ==================== HTTP Handler ====================
class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._serve_file("index.html", "text/html; charset=utf-8")
        elif self.path == "/keys.js":
            self._serve_file("keys.js", "application/javascript; charset=utf-8",
                             fallback=b"var LOCAL_API_KEYS = {};")
        else:
            self.send_error(404)

    def _serve_file(self, filename, content_type, fallback=None):
        fpath = resource_path(filename)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            data = content.encode("utf-8")
        except FileNotFoundError:
            if fallback:
                data = fallback
            else:
                self.send_error(404, filename + " not found")
                return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path == "/api/test":
            self.handle_test()
        else:
            self.send_error(404)

    def handle_test(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        params = json.loads(body)

        url = params.get("url", "")
        model = params.get("model", "")
        key = params.get("key", "")
        timeout = int(params.get("timeout", 15))

        result = {
            "url": url, "model": model, "status": "error",
            "response_time": 0, "status_code": None,
            "error": None, "error_type": None, "suggestion": None, "preview": None,
        }

        try:
            import requests as req
        except ImportError:
            result["error"] = "requests 库未安装"
            result["error_type"] = "依赖缺失"
            result["suggestion"] = "运行 pip install requests"
            self._send_json(result)
            return

        headers = {"Content-Type": "application/json", "Authorization": "Bearer " + key}
        if "openrouter.ai" in url:
            headers["HTTP-Referer"] = "https://ai-tester.local"
            headers["X-Title"] = "AI Model Tester"

        payload = {"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 30}

        t0 = time.time()
        try:
            resp = req.post(url, headers=headers, json=payload, timeout=timeout)
            result["response_time"] = int((time.time() - t0) * 1000)
            result["status_code"] = resp.status_code

            if resp.status_code == 200:
                data = resp.json()
                result["status"] = "success"
                try:
                    txt = data["choices"][0]["message"]["content"]
                    result["preview"] = txt[:300] + "..." if len(txt) > 300 else txt
                except Exception:
                    result["preview"] = "响应成功"
            else:
                detail = ""
                try:
                    ed = resp.json()
                    if "error" in ed:
                        detail = ed["error"].get("message", str(ed["error"])) if isinstance(ed["error"], dict) else str(ed["error"])
                except Exception:
                    detail = resp.text[:200]
                result["error"] = "HTTP %d: %s" % (resp.status_code, detail)
                err_map = {401: ("认证失败", "请检查 API Key 是否正确或已过期"),
                           403: ("权限不足", "API Key 可能无权访问该模型"),
                           404: ("模型不存在", "模型名称错误或已下线"),
                           429: ("频率限制", "稍后再试")}
                if resp.status_code in err_map:
                    result["error_type"], result["suggestion"] = err_map[resp.status_code]
                else:
                    result["error_type"] = "HTTP %d" % resp.status_code

        except req.exceptions.Timeout:
            result["response_time"] = int((time.time() - t0) * 1000)
            result["error"] = "请求超时 (%d秒)" % timeout
            result["error_type"] = "网络超时"
            result["suggestion"] = "网络慢或该服务在国内需代理访问"

        except req.exceptions.ConnectionError as e:
            result["response_time"] = int((time.time() - t0) * 1000)
            es = str(e)
            if "NameResolutionError" in es or "getaddrinfo" in es:
                result["error"] = "DNS 解析失败"
                result["error_type"] = "域名无法解析"
                result["suggestion"] = "检查 API 地址是否正确"
            elif "ConnectionRefused" in es:
                result["error"] = "连接被拒绝"
                result["error_type"] = "服务器拒绝"
                result["suggestion"] = "服务器可能宕机"
            elif "SSLError" in es or "CERTIFICATE" in es:
                result["error"] = "SSL 证书错误"
                result["error_type"] = "安全连接失败"
                result["suggestion"] = "可能需要代理或证书问题"
            else:
                result["error"] = "连接失败"
                result["error_type"] = "网络错误"
                result["suggestion"] = "该服务可能需要代理访问（境外服务）"

        except Exception as e:
            result["response_time"] = int((time.time() - t0) * 1000)
            result["error"] = str(e)[:300]
            result["error_type"] = "未知错误"

        self._send_json(result)

    def _send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# ==================== 主入口 ====================
def main():
    existing = check_existing()
    if existing is not None:
        url = "http://localhost:%d" % existing
        print("检测到工具已在运行，正在打开浏览器...")
        print("地址: " + url)
        webbrowser.open(url)
        sys.exit(0)

    port = find_available_port()
    if port is None:
        print("所有端口 8765-8799 均被占用")
        sys.exit(1)

    write_lock(port)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = "http://localhost:%d" % port
    print("AI 模型连通性测试工具")
    print("访问: " + url)
    if port != 8765:
        print("默认端口 8765 被占用，已自动切换到 %d" % port)
    threading.Timer(0.3, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        clear_lock()
        server.server_close()


if __name__ == "__main__":
    main()

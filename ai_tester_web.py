#!/usr/bin/env python3
"""AI 模型连通性测试工具 - 网页版"""

import http.server
import json
import threading
import webbrowser
import os
import sys
import requests
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            fpath = os.path.join(SCRIPT_DIR, "index.html")
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
            except FileNotFoundError:
                self.send_error(404, "index.html not found")
        elif self.path == "/keys.js":
            fpath = os.path.join(SCRIPT_DIR, "keys.js")
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
            except FileNotFoundError:
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"var LOCAL_API_KEYS = {};")
        else:
            self.send_error(404)

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

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
        }
        if "openrouter.ai" in url:
            headers["HTTP-Referer"] = "https://ai-tester.local"
            headers["X-Title"] = "AI Model Tester"

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 30,
        }

        result = {
            "url": url,
            "model": model,
            "status": "error",
            "response_time": 0,
            "status_code": None,
            "error": None,
            "error_type": None,
            "suggestion": None,
            "preview": None,
        }

        t0 = time.time()
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
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
                if resp.status_code == 401:
                    result["error_type"] = "认证失败"
                    result["suggestion"] = "请检查 API Key 是否正确或已过期"
                elif resp.status_code == 403:
                    result["error_type"] = "权限不足"
                    result["suggestion"] = "API Key 可能无权访问该模型"
                elif resp.status_code == 404:
                    result["error_type"] = "模型不存在"
                    result["suggestion"] = "模型名称错误或已下线"
                elif resp.status_code == 429:
                    result["error_type"] = "频率限制"
                    result["suggestion"] = "稍后再试"
                else:
                    result["error_type"] = "HTTP %d" % resp.status_code

        except requests.exceptions.Timeout:
            result["response_time"] = int((time.time() - t0) * 1000)
            result["error"] = "请求超时 (%d秒)" % timeout
            result["error_type"] = "网络超时"
            result["suggestion"] = "网络慢或该服务在国内需代理访问"

        except requests.exceptions.ConnectionError as e:
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

        self.send_json(result)

    def send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def is_port_in_use(port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def is_our_server(port):
    try:
        resp = requests.get("http://127.0.0.1:%d" % port, timeout=2)
        return resp.status_code == 200 and "AI 模型连通性测试" in resp.text
    except Exception:
        return False


def find_available_port(start=8765, end=8799):
    import socket
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return None


def find_existing_server(start=8765, end=8799):
    for port in range(start, end + 1):
        if is_port_in_use(port) and is_our_server(port):
            return port
    return None


def main():
    base_port = 8765

    existing = find_existing_server(base_port, 8799)
    if existing is not None:
        url = "http://localhost:%d" % existing
        print("检测到工具已在运行，正在打开浏览器...")
        print("地址: " + url)
        webbrowser.open(url)
        sys.exit(0)

    port = find_available_port(base_port, 8799)
    if port is None:
        print("所有端口 %d-%d 均被占用" % (base_port, 8799))
        sys.exit(1)

    url = "http://localhost:%d" % port
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print("AI 模型连通性测试工具")
    print("访问: " + url)
    if port != base_port:
        print("默认端口 %d 被占用，已自动切换到 %d" % (base_port, port))
    print("Ctrl+C 停止")
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
        server.server_close()


if __name__ == "__main__":
    main()

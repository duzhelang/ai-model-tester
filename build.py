#!/usr/bin/env python3
"""PyInstaller 打包脚本 - 将 AI 模型测试工具打包为单个 exe"""

import PyInstaller.__main__
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    os.path.join(SCRIPT_DIR, "ai_tester_web.py"),
    "--name=AI-Model-Tester",
    "--onefile",
    "--noconsole",
    "--clean",
    "--add-data=%s;." % os.path.join(SCRIPT_DIR, "index.html"),
    "--add-data=%s;." % os.path.join(SCRIPT_DIR, "keys.js"),
    "--distpath=%s" % os.path.join(SCRIPT_DIR, "dist"),
    "--workpath=%s" % os.path.join(SCRIPT_DIR, "build"),
    "--specpath=%s" % SCRIPT_DIR,
])

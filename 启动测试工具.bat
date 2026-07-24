@echo off
chcp 65001 >nul
cd /d "%~dp0"
python ai_tester_web.py

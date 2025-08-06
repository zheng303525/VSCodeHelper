@echo off
echo VS Code GitHub Copilot Chat 自动监控工具
echo =======================================

REM 检查Python是否已安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python。请先安装Python 3.8或更高版本。
    pause
    exit /b 1
)

REM 检查是否需要安装依赖
if not exist ".venv" (
    echo 正在创建虚拟环境...
    python -m venv .venv
    echo 激活虚拟环境并安装依赖...
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    echo 激活虚拟环境...
    call .venv\Scripts\activate.bat
)

REM 检查Tesseract OCR是否已安装
echo 检查OCR依赖...
python -c "import pytesseract; print('OCR依赖检查通过')" 2>nul
if errorlevel 1 (
    echo 警告: Tesseract OCR未正确安装或配置
    echo 请参考README.md中的安装说明
    echo.
)

echo 启动监控程序...
echo 按 Ctrl+C 可停止监控
echo.
python copilot_monitor.py

pause 
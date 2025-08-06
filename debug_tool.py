#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VS Code Copilot Chat 监控工具调试脚本
帮助诊断为什么监控工具可能不工作
"""

import time
import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import pytesseract
from PIL import Image
import os
import sys

def check_dependencies():
    """检查依赖项是否正确安装"""
    print("🔍 检查依赖项...")
    
    try:
        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")
    except ImportError:
        print("❌ OpenCV 未安装")
        return False
    
    try:
        import pyautogui
        print(f"✅ PyAutoGUI: {pyautogui.__version__}")
    except ImportError:
        print("❌ PyAutoGUI 未安装")
        return False
    
    try:
        import pygetwindow as gw
        print(f"✅ PyGetWindow 已安装")
    except ImportError:
        print("❌ PyGetWindow 未安装")
        return False
    
    try:
        import pytesseract
        # 测试Tesseract是否可用
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract: {version}")
    except Exception as e:
        print(f"❌ Tesseract 配置问题: {e}")
        print("   请确保已安装 Tesseract OCR 并正确配置路径")
        return False
    
    return True

def find_windows():
    """查找所有窗口，特别是VS Code相关的"""
    print("\n🔍 查找窗口...")
    
    all_windows = gw.getAllWindows()
    vscode_windows = []
    
    print(f"总共找到 {len(all_windows)} 个窗口")
    
    for window in all_windows:
        if window.title and len(window.title.strip()) > 0:
            if 'visual studio code' in window.title.lower() or 'vscode' in window.title.lower():
                vscode_windows.append(window)
                print(f"✅ 找到 VS Code 窗口: '{window.title}'")
                print(f"   位置: ({window.left}, {window.top}), 大小: {window.width}x{window.height}")
    
    if not vscode_windows:
        print("❌ 未找到 VS Code 窗口")
        print("   请确保 VS Code 正在运行且窗口标题包含 'Visual Studio Code'")
        
        # 显示所有可能相关的窗口
        print("\n📋 所有活动窗口:")
        for i, window in enumerate(all_windows[:20]):  # 只显示前20个
            if window.title and len(window.title.strip()) > 0:
                print(f"   {i+1}. '{window.title}'")
    
    return vscode_windows

def test_screenshot():
    """测试屏幕截图功能"""
    print("\n📸 测试屏幕截图...")
    
    try:
        # 测试全屏截图
        screenshot = pyautogui.screenshot()
        print(f"✅ 屏幕截图成功: {screenshot.size}")
        
        # 保存测试截图
        test_file = "test_screenshot.png"
        screenshot.save(test_file)
        print(f"✅ 测试截图已保存: {test_file}")
        
        return True
    except Exception as e:
        print(f"❌ 屏幕截图失败: {e}")
        return False

def test_vscode_detection(vscode_windows):
    """测试VS Code窗口检测和截图"""
    if not vscode_windows:
        return False
    
    print("\n🎯 测试 VS Code 窗口检测...")
    
    for i, window in enumerate(vscode_windows):
        try:
            print(f"\n测试窗口 {i+1}: '{window.title}'")
            
            # 激活窗口
            window.activate()
            time.sleep(1)
            
            # 获取窗口位置
            left, top, width, height = window.left, window.top, window.width, window.height
            print(f"窗口区域: ({left}, {top}, {width}, {height})")
            
            # 截取窗口区域
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            
            # 保存窗口截图
            window_file = f"vscode_window_{i+1}.png"
            screenshot.save(window_file)
            print(f"✅ VS Code 窗口截图已保存: {window_file}")
            
            # 截取右半部分（假设聊天区域在右侧）
            img_array = np.array(screenshot)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            chat_area = img_bgr[:, width//2:]
            
            # 保存聊天区域截图
            chat_file = f"chat_area_{i+1}.png"
            cv2.imwrite(chat_file, chat_area)
            print(f"✅ 聊天区域截图已保存: {chat_file}")
            
        except Exception as e:
            print(f"❌ 处理窗口 {i+1} 时出错: {e}")
    
    return True

def test_ocr():
    """测试OCR功能"""
    print("\n📝 测试OCR识别...")
    
    try:
        # 创建一个测试图像
        test_img = Image.new('RGB', (400, 200), color='white')
        from PIL import ImageDraw, ImageFont
        
        draw = ImageDraw.Draw(test_img)
        try:
            # 尝试使用系统字体
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        # 绘制测试文本
        test_text = "GitHub Copilot Chat\nThinking...\nGenerate code"
        draw.text((10, 50), test_text, fill='black', font=font)
        
        # 保存测试图像
        test_img.save("test_ocr_image.png")
        print("✅ 测试OCR图像已创建: test_ocr_image.png")
        
        # 进行OCR识别
        custom_config = r'--oem 3 --psm 6 -l eng'
        recognized_text = pytesseract.image_to_string(test_img, config=custom_config)
        
        print(f"📄 OCR识别结果:")
        print(f"原文: {test_text}")
        print(f"识别: {recognized_text.strip()}")
        
        if "copilot" in recognized_text.lower() or "thinking" in recognized_text.lower():
            print("✅ OCR识别功能正常")
            return True
        else:
            print("⚠️ OCR识别结果可能不准确")
            return False
            
    except Exception as e:
        print(f"❌ OCR测试失败: {e}")
        return False

def test_automation():
    """测试自动化功能（安全测试）"""
    print("\n🤖 测试自动化功能...")
    
    try:
        # 获取当前鼠标位置
        current_pos = pyautogui.position()
        print(f"当前鼠标位置: {current_pos}")
        
        # 测试移动鼠标（安全范围内）
        test_x = current_pos.x + 10
        test_y = current_pos.y + 10
        
        print("移动鼠标到测试位置...")
        pyautogui.moveTo(test_x, test_y, duration=0.5)
        time.sleep(0.5)
        
        # 移回原位置
        pyautogui.moveTo(current_pos.x, current_pos.y, duration=0.5)
        print("✅ 鼠标控制正常")
        
        return True
    except Exception as e:
        print(f"❌ 自动化测试失败: {e}")
        return False

def provide_solutions():
    """提供解决方案建议"""
    print("\n💡 常见问题和解决方案:")
    print()
    print("1️⃣ VS Code 未找到:")
    print("   • 确保 VS Code 正在运行")
    print("   • 确保窗口标题包含 'Visual Studio Code'")
    print("   • 检查 VS Code 是否被最小化")
    print()
    print("2️⃣ Tesseract OCR 问题:")
    print("   • Windows: 下载并安装 Tesseract-OCR")
    print("   • 添加到系统PATH或设置 pytesseract.pytesseract.tesseract_cmd")
    print("   • 下载地址: https://github.com/UB-Mannheim/tesseract/wiki")
    print()
    print("3️⃣ 聊天窗口定位问题:")
    print("   • 确保 GitHub Copilot Chat 面板已打开")
    print("   • 尝试将聊天面板放在VS Code右侧")
    print("   • 检查聊天面板是否可见且不被遮挡")
    print()
    print("4️⃣ OCR识别不准确:")
    print("   • 增加显示器分辨率/缩放比例")
    print("   • 使用较大的字体")
    print("   • 确保足够的对比度")
    print()
    print("5️⃣ 权限问题:")
    print("   • 以管理员身份运行Python脚本")
    print("   • 检查杀毒软件是否阻止了自动化操作")

def main():
    """主函数"""
    print("🚀 VS Code Copilot Chat 监控工具诊断")
    print("=" * 50)
    
    # 检查依赖项
    if not check_dependencies():
        print("\n❌ 依赖项检查失败，请先安装缺失的依赖项")
        return
    
    # 查找窗口
    vscode_windows = find_windows()
    
    # 测试屏幕截图
    test_screenshot()
    
    # 测试VS Code检测
    if vscode_windows:
        test_vscode_detection(vscode_windows)
    
    # 测试OCR
    test_ocr()
    
    # 测试自动化
    test_automation()
    
    # 提供解决方案
    provide_solutions()
    
    print("\n🎯 诊断完成！")
    print("请查看生成的截图文件，并根据上述建议进行调整。")

if __name__ == "__main__":
    main() 
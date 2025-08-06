#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VS Code GitHub Copilot Chat 检测功能测试脚本
用于验证OCR、窗口检测等功能是否正常工作
"""

import sys
import time
import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import pytesseract
from PIL import Image, ImageEnhance
import configparser
import os


def test_dependencies():
    """测试依赖包是否正确安装"""
    print("测试依赖包...")
    
    try:
        import cv2
        print("✅ OpenCV 已安装")
    except ImportError:
        print("❌ OpenCV 未安装")
        return False
    
    try:
        import pyautogui
        print("✅ PyAutoGUI 已安装")
    except ImportError:
        print("❌ PyAutoGUI 未安装")
        return False
    
    try:
        import pygetwindow
        print("✅ PyGetWindow 已安装")
    except ImportError:
        print("❌ PyGetWindow 未安装")
        return False
    
    try:
        import pytesseract
        print("✅ PyTesseract 已安装")
    except ImportError:
        print("❌ PyTesseract 未安装")
        return False
    
    return True


def test_tesseract():
    """测试Tesseract OCR是否正确配置"""
    print("\n测试Tesseract OCR...")
    
    try:
        # 创建一个简单的测试图像
        test_img = np.ones((100, 300, 3), dtype=np.uint8) * 255
        cv2.putText(test_img, "Hello World", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # 保存测试图像
        cv2.imwrite("test_ocr.png", test_img)
        
        # 进行OCR测试
        result = pytesseract.image_to_string(Image.open("test_ocr.png"))
        print(f"OCR测试结果: '{result.strip()}'")
        
        # 清理测试文件
        os.remove("test_ocr.png")
        
        if "Hello" in result or "World" in result:
            print("✅ Tesseract OCR 工作正常")
            return True
        else:
            print("❌ Tesseract OCR 可能存在问题")
            return False
            
    except Exception as e:
        print(f"❌ Tesseract OCR 测试失败: {e}")
        return False


def test_vscode_detection():
    """测试VS Code窗口检测"""
    print("\n测试VS Code窗口检测...")
    
    try:
        windows = gw.getWindowsWithTitle("Visual Studio Code")
        if windows:
            print(f"✅ 找到 {len(windows)} 个VS Code窗口:")
            for i, window in enumerate(windows):
                print(f"  窗口 {i+1}: {window.title}")
                print(f"    位置: ({window.left}, {window.top})")
                print(f"    大小: {window.width} x {window.height}")
                print(f"    最小化: {window.isMinimized}")
            return True
        else:
            print("❌ 未找到VS Code窗口")
            print("请确保VS Code正在运行")
            return False
            
    except Exception as e:
        print(f"❌ 窗口检测失败: {e}")
        return False


def test_screenshot():
    """测试屏幕截图功能"""
    print("\n测试屏幕截图功能...")
    
    try:
        # 截取整个屏幕
        screenshot = pyautogui.screenshot()
        print(f"✅ 截图成功，尺寸: {screenshot.size}")
        
        # 保存测试截图
        screenshot.save("test_screenshot.png")
        print("✅ 测试截图已保存为 test_screenshot.png")
        
        return True
        
    except Exception as e:
        print(f"❌ 截图功能测试失败: {e}")
        return False


def test_vscode_screenshot():
    """测试VS Code窗口截图"""
    print("\n测试VS Code窗口截图...")
    
    try:
        windows = gw.getWindowsWithTitle("Visual Studio Code")
        if not windows:
            print("❌ 未找到VS Code窗口，无法进行截图测试")
            return False
        
        window = windows[0]
        if window.isMinimized:
            window.restore()
            time.sleep(1)
        
        window.activate()
        time.sleep(1)
        
        # 截取VS Code窗口
        left, top, width, height = window.left, window.top, window.width, window.height
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        
        # 保存截图
        screenshot.save("test_vscode_screenshot.png")
        print("✅ VS Code窗口截图已保存为 test_vscode_screenshot.png")
        
        # 测试聊天区域截图（右半部分）
        img_array = np.array(screenshot)
        chat_area = img_array[:, width//2:]
        cv2.imwrite("test_chat_area.png", cv2.cvtColor(chat_area, cv2.COLOR_RGB2BGR))
        print("✅ 聊天区域截图已保存为 test_chat_area.png")
        
        return True
        
    except Exception as e:
        print(f"❌ VS Code截图测试失败: {e}")
        return False


def test_ocr_on_vscode():
    """测试在VS Code截图上进行OCR"""
    print("\n测试VS Code截图OCR识别...")
    
    if not os.path.exists("test_chat_area.png"):
        print("❌ 找不到聊天区域截图，请先运行VS Code截图测试")
        return False
    
    try:
        # 读取聊天区域截图
        image = cv2.imread("test_chat_area.png")
        
        # 预处理图像
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        denoised = cv2.medianBlur(enhanced, 3)
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 保存预处理后的图像
        cv2.imwrite("test_processed.png", binary)
        print("✅ 预处理图像已保存为 test_processed.png")
        
        # 进行OCR识别
        custom_config = r'--oem 3 --psm 6 -l eng+chi_sim'
        text = pytesseract.image_to_string(binary, config=custom_config)
        
        print(f"OCR识别结果:")
        print("-" * 40)
        print(text)
        print("-" * 40)
        
        if text.strip():
            print("✅ OCR识别成功")
            return True
        else:
            print("⚠️  OCR未识别到文本，可能需要调整配置")
            return False
            
    except Exception as e:
        print(f"❌ VS Code OCR测试失败: {e}")
        return False


def test_automation():
    """测试自动化操作（注意：这会实际移动鼠标和输入文本）"""
    print("\n测试自动化操作...")
    print("⚠️  这将在5秒后开始测试鼠标和键盘操作")
    print("如果不想继续，请按Ctrl+C")
    
    try:
        for i in range(5, 0, -1):
            print(f"倒计时: {i}")
            time.sleep(1)
        
        # 获取当前鼠标位置
        original_pos = pyautogui.position()
        print(f"当前鼠标位置: {original_pos}")
        
        # 移动鼠标
        pyautogui.move(100, 0, duration=1)
        print("✅ 鼠标移动测试完成")
        
        # 恢复鼠标位置
        pyautogui.moveTo(original_pos.x, original_pos.y, duration=1)
        
        # 测试文本输入（在当前光标位置）
        print("将输入测试文本...")
        pyautogui.write("test", interval=0.1)
        time.sleep(0.5)
        
        # 删除测试文本
        for _ in range(4):
            pyautogui.press('backspace')
        
        print("✅ 自动化操作测试完成")
        return True
        
    except KeyboardInterrupt:
        print("\n用户取消了自动化测试")
        return False
    except Exception as e:
        print(f"❌ 自动化操作测试失败: {e}")
        return False


def cleanup_test_files():
    """清理测试文件"""
    test_files = [
        "test_screenshot.png",
        "test_vscode_screenshot.png", 
        "test_chat_area.png",
        "test_processed.png"
    ]
    
    print("\n清理测试文件...")
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"已删除: {file}")


def main():
    """主测试函数"""
    print("VS Code GitHub Copilot Chat 检测功能测试")
    print("=" * 50)
    
    tests = [
        ("依赖包检测", test_dependencies),
        ("Tesseract OCR", test_tesseract),
        ("VS Code窗口检测", test_vscode_detection),
        ("屏幕截图功能", test_screenshot),
        ("VS Code窗口截图", test_vscode_screenshot),
        ("OCR文本识别", test_ocr_on_vscode),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except KeyboardInterrupt:
            print("\n测试被用户中断")
            break
        except Exception as e:
            print(f"❌ 测试 {test_name} 时发生异常: {e}")
            results[test_name] = False
    
    # 询问是否测试自动化操作
    if input("\n是否测试自动化操作？(y/N): ").lower().startswith('y'):
        print(f"\n{'='*20} 自动化操作测试 {'='*20}")
        results["自动化操作"] = test_automation()
    
    # 显示测试结果摘要
    print(f"\n{'='*20} 测试结果摘要 {'='*20}")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    # 询问是否清理测试文件
    if input("\n是否清理测试文件？(Y/n): ").lower() != 'n':
        cleanup_test_files()
    
    print("\n测试完成！")
    
    # 给出建议
    failed_tests = [name for name, result in results.items() if not result]
    if failed_tests:
        print(f"\n需要修复的问题:")
        for test in failed_tests:
            print(f"- {test}")
        print("\n请参考README.md中的故障排除部分")
    else:
        print("\n所有测试都通过了！监控工具应该可以正常工作。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n测试程序发生错误: {e}")
    
    input("\n按Enter键退出...") 
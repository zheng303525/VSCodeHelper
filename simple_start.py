#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VS Code Copilot Chat 简化启动器
提供多种无需OCR的监控方案
"""

import os
import sys
import subprocess

def print_banner():
    """打印横幅"""
    print("🚀 VS Code Copilot Chat 监控工具 - 简化版")
    print("=" * 60)
    print("✨ 无需安装OCR软件的解决方案")
    print("=" * 60)

def check_dependencies():
    """检查依赖"""
    print("\n🔍 检查Python依赖...")
    
    dependencies = {
        'pyautogui': '自动化操作库（推荐安装）',
        'pygetwindow': '窗口管理库（推荐安装）', 
        'keyboard': '热键支持库（可选）',
        'pyperclip': '剪贴板操作库（可选）'
    }
    
    available = {}
    for dep, desc in dependencies.items():
        try:
            __import__(dep)
            available[dep] = True
            print(f"✅ {dep}: 已安装 - {desc}")
        except ImportError:
            available[dep] = False
            print(f"❌ {dep}: 未安装 - {desc}")
    
    return available

def install_optional_dependencies():
    """安装可选依赖"""
    print("\n📦 安装推荐依赖库...")
    
    packages = [
        'pyautogui',
        'pygetwindow', 
        'pyperclip'
    ]
    
    for package in packages:
        try:
            print(f"正在安装 {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ {package} 安装成功")
        except subprocess.CalledProcessError:
            print(f"❌ {package} 安装失败")
        except Exception as e:
            print(f"❌ 安装 {package} 时出错: {e}")

def show_options():
    """显示选项菜单"""
    print("\n🎯 可用的监控方案:")
    print()
    
    print("1️⃣  定时器方案 (推荐)")
    print("   • 完全无需额外软件")
    print("   • 定期自动发送continue命令")
    print("   • 支持交互式控制")
    print("   • 最简单可靠")
    print()
    
    print("2️⃣  热键方案")
    print("   • 需要: keyboard库")
    print("   • 全局热键控制")
    print("   • 手动+自动两种模式")
    print("   • 需要管理员权限")
    print()
    
    print("3️⃣  图像检测方案")
    print("   • 需要: pyautogui, pygetwindow")
    print("   • 不需要OCR")
    print("   • 基于像素变化检测")
    print("   • 相对复杂但智能")
    print()
    
    print("4️⃣  安装推荐依赖")
    print("   • 安装pyautogui、pygetwindow等")
    print("   • 启用完整自动化功能")
    print()
    
    print("5️⃣  依赖检查")
    print("   • 检查当前已安装的库")
    print()
    
    print("0️⃣  退出")
    print()

def run_timer_monitor():
    """运行定时器监控"""
    print("🚀 启动定时器监控方案...")
    print("✨ 这是最简单的方案，完全无需额外软件")
    print()
    
    try:
        # 检查文件是否存在
        if not os.path.exists('copilot_timer_monitor.py'):
            print("❌ 找不到 copilot_timer_monitor.py 文件")
            return
        
        # 运行定时器监控
        subprocess.run([sys.executable, 'copilot_timer_monitor.py'])
    except KeyboardInterrupt:
        print("\n✅ 定时器监控已停止")
    except Exception as e:
        print(f"❌ 运行出错: {e}")

def run_hotkey_monitor():
    """运行热键监控"""
    print("🚀 启动热键监控方案...")
    
    try:
        import keyboard
        print("✅ keyboard库已安装")
    except ImportError:
        print("❌ 需要安装keyboard库: pip install keyboard")
        return
    
    try:
        if not os.path.exists('copilot_hotkey_monitor.py'):
            print("❌ 找不到 copilot_hotkey_monitor.py 文件")
            return
        
        print("⚠️  需要管理员权限运行以支持全局热键")
        subprocess.run([sys.executable, 'copilot_hotkey_monitor.py'])
    except KeyboardInterrupt:
        print("\n✅ 热键监控已停止")
    except Exception as e:
        print(f"❌ 运行出错: {e}")

def run_simple_monitor():
    """运行简化图像监控"""
    print("🚀 启动图像检测监控方案...")
    
    # 检查依赖
    missing = []
    try:
        import cv2
    except ImportError:
        missing.append('opencv-python')
    
    try:
        import pyautogui
    except ImportError:
        missing.append('pyautogui')
    
    try:
        import pygetwindow
    except ImportError:
        missing.append('pygetwindow')
    
    if missing:
        print(f"❌ 缺少依赖: {', '.join(missing)}")
        print(f"请安装: pip install {' '.join(missing)}")
        return
    
    try:
        if not os.path.exists('copilot_monitor_simple.py'):
            print("❌ 找不到 copilot_monitor_simple.py 文件")
            return
        
        subprocess.run([sys.executable, 'copilot_monitor_simple.py'])
    except KeyboardInterrupt:
        print("\n✅ 图像监控已停止")
    except Exception as e:
        print(f"❌ 运行出错: {e}")

def main():
    """主函数"""
    print_banner()
    
    while True:
        show_options()
        
        try:
            choice = input("请选择方案 (0-5): ").strip()
            
            if choice == '0':
                print("👋 再见！")
                break
            elif choice == '1':
                run_timer_monitor()
            elif choice == '2':
                run_hotkey_monitor()
            elif choice == '3':
                run_simple_monitor()
            elif choice == '4':
                install_optional_dependencies()
            elif choice == '5':
                check_dependencies()
            else:
                print("❌ 无效选择，请输入0-5")
            
            input("\n按回车键继续...")
            print("\n" + "="*60)
            
        except KeyboardInterrupt:
            print("\n👋 程序被中断，再见！")
            break
        except Exception as e:
            print(f"❌ 出错: {e}")

if __name__ == "__main__":
    main() 
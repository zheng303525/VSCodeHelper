#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VS Code GitHub Copilot Chat 自动监控工具 - 主启动脚本
让用户选择使用命令行版本或GUI版本
"""

import sys
import os


def check_dependencies():
    """检查依赖是否安装"""
    missing_deps = []
    
    try:
        import cv2
    except ImportError:
        missing_deps.append("opencv-python")
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import pyautogui
    except ImportError:
        missing_deps.append("pyautogui")
    
    try:
        import pygetwindow
    except ImportError:
        missing_deps.append("pygetwindow")
    
    try:
        import pytesseract
    except ImportError:
        missing_deps.append("pytesseract")
    
    try:
        from PIL import Image
    except ImportError:
        missing_deps.append("Pillow")
    
    return missing_deps


def show_menu():
    """显示主菜单"""
    print("\n" + "="*60)
    print("    VS Code GitHub Copilot Chat 自动监控工具")
    print("="*60)
    print()
    print("请选择运行模式:")
    print()
    print("1. 命令行版本 (标准)")
    print("   - 基于屏幕截图和OCR识别")
    print("   - 适合正常使用场景")
    print("   - 需要屏幕处于可见状态")
    print()
    print("2. 高级监控版本 (推荐)")
    print("   - 支持锁屏状态下工作")
    print("   - 多种监控策略")
    print("   - 自动防止息屏")
    print("   - 更强的稳定性")
    print()
    print("3. GUI图形界面版本")
    print("   - 友好的图形界面")
    print("   - 可视化监控状态")
    print("   - 便于配置和控制")
    print()
    print("4. 运行功能测试")
    print("   - 测试系统依赖")
    print("   - 验证功能完整性")
    print("   - 故障诊断")
    print()
    print("5. 安装/检查依赖")
    print("   - 检查Python包依赖")
    print("   - 提供安装指导")
    print()
    print("6. 退出")
    print()


def install_dependencies():
    """安装依赖"""
    print("\n检查依赖包...")
    missing_deps = check_dependencies()
    
    if not missing_deps:
        print("✅ 所有依赖包都已安装！")
        return True
    
    print(f"\n❌ 缺少以下依赖包: {', '.join(missing_deps)}")
    print("\n安装建议:")
    print("1. 使用提供的批处理文件: start_monitor.bat")
    print("2. 手动安装:")
    print(f"   pip install {' '.join(missing_deps)}")
    print()
    
    choice = input("是否现在尝试自动安装？(y/N): ")
    if choice.lower().startswith('y'):
        try:
            import subprocess
            print("\n正在安装依赖包...")
            result = subprocess.run([sys.executable, "-m", "pip", "install"] + missing_deps, 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 依赖包安装成功！")
                return True
            else:
                print(f"❌ 安装失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ 安装过程中出错: {e}")
            return False
    
    return False


def run_cli_version():
    """运行标准命令行版本"""
    try:
        print("\n启动标准命令行版本...")
        from copilot_monitor import main
        main()
    except ImportError:
        print("❌ 无法导入监控模块，请检查依赖安装")
        input("按Enter键返回主菜单...")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        input("按Enter键返回主菜单...")


def run_advanced_version():
    """运行高级监控版本"""
    try:
        print("\n启动高级监控版本...")
        print("支持锁屏状态下的持续监控")
        from copilot_monitor_advanced import main
        main()
    except ImportError:
        print("❌ 无法导入高级监控模块，请检查依赖安装")
        input("按Enter键返回主菜单...")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        input("按Enter键返回主菜单...")


def run_gui_version():
    """运行GUI版本"""
    try:
        print("\n启动GUI版本...")
        from copilot_monitor_gui import main
        main()
    except ImportError as e:
        print(f"❌ 无法导入GUI模块: {e}")
        print("请检查tkinter和其他依赖是否正确安装")
        input("按Enter键返回主菜单...")
    except Exception as e:
        print(f"❌ 启动GUI失败: {e}")
        input("按Enter键返回主菜单...")


def run_tests():
    """运行测试"""
    try:
        print("\n启动功能测试...")
        import subprocess
        subprocess.run([sys.executable, "test_detection.py"])
    except FileNotFoundError:
        print("❌ 找不到测试文件 test_detection.py")
    except Exception as e:
        print(f"❌ 运行测试失败: {e}")
    
    input("按Enter键返回主菜单...")


def check_tesseract():
    """检查Tesseract OCR安装"""
    try:
        import pytesseract
        # 尝试获取Tesseract版本
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract OCR 已安装，版本: {version}")
        return True
    except Exception as e:
        print(f"❌ Tesseract OCR 未正确安装或配置: {e}")
        print("\n安装指导:")
        print("1. 下载: https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. 安装到默认路径: C:\\Program Files\\Tesseract-OCR\\")
        print("3. 添加到系统PATH环境变量")
        print("4. 下载中文语言包（可选）")
        return False


def main():
    """主函数"""
    while True:
        try:
            show_menu()
            choice = input("请输入选项 (1-6): ").strip()
            
            if choice == "1":
                # 检查依赖
                missing_deps = check_dependencies()
                if missing_deps:
                    print(f"\n❌ 缺少依赖包: {', '.join(missing_deps)}")
                    print("请先安装依赖包（选项5）")
                    input("按Enter键继续...")
                    continue
                
                run_cli_version()
            
            elif choice == "2":
                # 检查依赖
                missing_deps = check_dependencies()
                if missing_deps:
                    print(f"\n❌ 缺少依赖包: {', '.join(missing_deps)}")
                    print("请先安装依赖包（选项5）")
                    input("按Enter键继续...")
                    continue
                
                run_advanced_version()
            
            elif choice == "3":
                # 检查依赖
                missing_deps = check_dependencies()
                if missing_deps:
                    print(f"\n❌ 缺少依赖包: {', '.join(missing_deps)}")
                    print("请先安装依赖包（选项5）")
                    input("按Enter键继续...")
                    continue
                
                run_gui_version()
            
            elif choice == "4":
                run_tests()
            
            elif choice == "5":
                print("\n" + "="*50)
                print("依赖检查和安装")
                print("="*50)
                
                # 检查Python包依赖
                install_dependencies()
                
                # 检查Tesseract OCR
                print("\n检查Tesseract OCR...")
                check_tesseract()
                
                input("\n按Enter键返回主菜单...")
            
            elif choice == "6":
                print("\n感谢使用！再见！")
                break
            
            else:
                print("\n❌ 无效选项，请重新选择")
                input("按Enter键继续...")
        
        except KeyboardInterrupt:
            print("\n\n用户中断，退出程序")
            break
        except Exception as e:
            print(f"\n❌ 程序出错: {e}")
            input("按Enter键继续...")


if __name__ == "__main__":
    main() 
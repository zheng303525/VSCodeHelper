#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VS Code Copilot Chat 热键监控工具
最简单的方案：通过全局热键手动或自动发送continue命令
无需OCR，无需复杂检测
"""

import time
import logging
import pyautogui
import pygetwindow as gw
import keyboard
import threading
import sys
from typing import Optional

class HotkeyCopilotMonitor:
    """基于热键的Copilot监控器"""
    
    def __init__(self):
        """初始化监控器"""
        self.setup_logging()
        self.running = False
        self.auto_mode = False
        self.last_continue_time = 0
        
        # 设置
        self.vscode_title = 'Visual Studio Code'
        self.continue_command = 'continue'
        self.auto_interval = 120  # 自动模式下的间隔（秒）
        
        # 热键设置
        self.manual_hotkey = 'ctrl+shift+c'  # 手动发送continue
        self.auto_toggle_hotkey = 'ctrl+shift+a'  # 切换自动模式
        self.quit_hotkey = 'ctrl+shift+q'  # 退出程序
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('hotkey_copilot_monitor.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def find_vscode_window(self) -> Optional[gw.Win32Window]:
        """查找VS Code窗口"""
        try:
            windows = gw.getWindowsWithTitle(self.vscode_title)
            for window in windows:
                if window.visible and window.width > 100 and window.height > 100:
                    return window
            return None
        except Exception as e:
            self.logger.error(f"查找VS Code窗口时出错: {e}")
            return None
    
    def send_continue_command(self) -> bool:
        """发送continue命令"""
        try:
            # 查找VS Code窗口
            window = self.find_vscode_window()
            if not window:
                self.logger.warning("未找到VS Code窗口")
                return False
            
            self.logger.info("发送continue命令...")
            
            # 激活VS Code窗口
            window.activate()
            time.sleep(0.3)
            
            # 方法1：尝试使用Copilot Chat的快捷键
            # Ctrl+I 是Copilot Chat的默认快捷键
            pyautogui.hotkey('ctrl', 'i')
            time.sleep(0.5)
            
            # 输入continue命令
            pyautogui.write(self.continue_command, interval=0.03)
            time.sleep(0.3)
            
            # 发送（Enter键）
            pyautogui.press('enter')
            
            self.logger.info(f"✅ continue命令已发送")
            self.last_continue_time = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 发送continue命令失败: {e}")
            return False
    
    def on_manual_hotkey(self):
        """手动热键回调"""
        self.logger.info(f"🔥 检测到手动热键 {self.manual_hotkey}")
        self.send_continue_command()
    
    def on_auto_toggle_hotkey(self):
        """自动模式切换热键回调"""
        self.auto_mode = not self.auto_mode
        status = "开启" if self.auto_mode else "关闭"
        self.logger.info(f"🔄 自动模式已{status}")
        
        if self.auto_mode:
            self.logger.info(f"⏰ 将每 {self.auto_interval} 秒自动发送continue命令")
    
    def on_quit_hotkey(self):
        """退出热键回调"""
        self.logger.info(f"🛑 检测到退出热键 {self.quit_hotkey}")
        self.running = False
    
    def auto_send_thread(self):
        """自动发送线程"""
        while self.running:
            if self.auto_mode:
                current_time = time.time()
                if (current_time - self.last_continue_time) >= self.auto_interval:
                    self.logger.info("⏰ 自动模式：发送continue命令")
                    self.send_continue_command()
            time.sleep(10)  # 每10秒检查一次
    
    def register_hotkeys(self):
        """注册全局热键"""
        try:
            keyboard.add_hotkey(self.manual_hotkey, self.on_manual_hotkey)
            keyboard.add_hotkey(self.auto_toggle_hotkey, self.on_auto_toggle_hotkey)
            keyboard.add_hotkey(self.quit_hotkey, self.on_quit_hotkey)
            
            self.logger.info("🎯 热键注册成功:")
            self.logger.info(f"   {self.manual_hotkey} - 手动发送continue命令")
            self.logger.info(f"   {self.auto_toggle_hotkey} - 切换自动模式")
            self.logger.info(f"   {self.quit_hotkey} - 退出程序")
            
        except Exception as e:
            self.logger.error(f"❌ 热键注册失败: {e}")
            return False
        return True
    
    def start(self):
        """启动监控"""
        self.running = True
        
        # 注册热键
        if not self.register_hotkeys():
            return
        
        # 启动自动发送线程
        auto_thread = threading.Thread(target=self.auto_send_thread, daemon=True)
        auto_thread.start()
        
        self.logger.info("🚀 热键监控已启动")
        self.logger.info("💡 使用说明:")
        self.logger.info(f"   1. 按 {self.manual_hotkey} 立即发送continue命令")
        self.logger.info(f"   2. 按 {self.auto_toggle_hotkey} 开启/关闭自动模式")
        self.logger.info(f"   3. 按 {self.quit_hotkey} 退出程序")
        self.logger.info("   4. 自动模式下，每2分钟自动发送一次continue")
        
        try:
            # 保持程序运行
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("接收到Ctrl+C信号")
        finally:
            self.stop()
    
    def stop(self):
        """停止监控"""
        self.running = False
        try:
            keyboard.unhook_all()
            self.logger.info("🛑 热键监控已停止")
        except:
            pass

def main():
    """主函数"""
    print("🚀 VS Code Copilot Chat 热键监控工具")
    print("=" * 60)
    print("✨ 特点：")
    print("   • 无需安装OCR软件")
    print("   • 无需复杂的图像识别")
    print("   • 支持手动和自动两种模式")
    print("   • 全局热键，任何时候都可以使用")
    print()
    print("🎯 使用方法：")
    print("   1. 启动本程序")
    print("   2. 在VS Code中打开Copilot Chat")
    print("   3. 使用热键控制continue命令的发送")
    print()
    print("⚠️  需要以管理员权限运行以支持全局热键")
    print("=" * 60)
    print()
    
    monitor = HotkeyCopilotMonitor()
    
    try:
        monitor.start()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n程序出错: {e}")
    finally:
        monitor.stop()

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VS Code Copilot Chat 定时器监控工具
最简单的解决方案：定期自动发送continue命令
无需OCR、无需图像检测、无需复杂依赖
"""

import time
import logging
import sys
import threading
from datetime import datetime

class TimerCopilotMonitor:
    """基于定时器的Copilot监控器"""
    
    def __init__(self):
        """初始化监控器"""
        self.setup_logging()
        self.running = False
        self.enabled = True
        
        # 配置设置
        self.interval_minutes = 2  # 每2分钟发送一次
        self.continue_command = 'continue'
        
        self.logger.info("🚀 定时器监控工具初始化完成")
        self.logger.info(f"⏰ 设置间隔: {self.interval_minutes} 分钟")
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('timer_copilot_monitor.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def send_continue_via_clipboard(self) -> bool:
        """通过剪贴板发送continue命令"""
        try:
            import pyperclip
            
            # 备份当前剪贴板内容
            original_clipboard = ""
            try:
                original_clipboard = pyperclip.paste()
            except:
                pass
            
            # 将continue命令复制到剪贴板
            pyperclip.copy(self.continue_command)
            
            self.logger.info("📋 continue命令已复制到剪贴板")
            self.logger.info("💡 请手动切换到VS Code并粘贴(Ctrl+V)，然后按Enter发送")
            
            # 等待用户操作
            time.sleep(5)
            
            # 恢复原剪贴板内容
            try:
                if original_clipboard:
                    pyperclip.copy(original_clipboard)
            except:
                pass
            
            return True
            
        except ImportError:
            self.logger.warning("❌ pyperclip 未安装，无法使用剪贴板功能")
            return False
        except Exception as e:
            self.logger.error(f"❌ 剪贴板操作失败: {e}")
            return False
    
    def send_continue_via_automation(self) -> bool:
        """通过自动化发送continue命令（需要额外库）"""
        try:
            import pyautogui
            import pygetwindow as gw
            
            # 查找VS Code窗口
            windows = gw.getWindowsWithTitle('Visual Studio Code')
            if not windows:
                self.logger.warning("⚠️ 未找到VS Code窗口")
                return False
            
            window = windows[0]
            
            # 激活窗口
            window.activate()
            time.sleep(0.5)
            
            # 发送Ctrl+I打开Copilot Chat
            pyautogui.hotkey('ctrl', 'i')
            time.sleep(0.5)
            
            # 输入continue命令
            pyautogui.write(self.continue_command, interval=0.03)
            time.sleep(0.3)
            
            # 按Enter发送
            pyautogui.press('enter')
            
            self.logger.info("✅ continue命令已自动发送")
            return True
            
        except ImportError:
            self.logger.debug("自动化库未安装，跳过自动发送")
            return False
        except Exception as e:
            self.logger.error(f"❌ 自动发送失败: {e}")
            return False
    
    def send_continue_command(self) -> bool:
        """发送continue命令（尝试多种方法）"""
        if not self.enabled:
            return True
        
        current_time = datetime.now().strftime("%H:%M:%S")
        self.logger.info(f"🕐 {current_time} - 准备发送continue命令")
        
        # 方法1：尝试自动化发送
        if self.send_continue_via_automation():
            return True
        
        # 方法2：使用剪贴板
        if self.send_continue_via_clipboard():
            return True
        
        # 方法3：仅提示用户
        self.logger.info("💡 请手动在VS Code Copilot Chat中输入: continue")
        self.logger.info("🎯 提示：您可以安装 pyautogui 和 pygetwindow 来启用自动发送功能")
        return True
    
    def timer_thread(self):
        """定时器线程"""
        next_send_time = time.time() + (self.interval_minutes * 60)
        
        while self.running:
            current_time = time.time()
            
            if current_time >= next_send_time and self.enabled:
                self.send_continue_command()
                next_send_time = current_time + (self.interval_minutes * 60)
                
                # 显示下次发送时间
                next_time_str = datetime.fromtimestamp(next_send_time).strftime("%H:%M:%S")
                self.logger.info(f"⏰ 下次发送时间: {next_time_str}")
            
            time.sleep(10)  # 每10秒检查一次
    
    def interactive_controls(self):
        """交互式控制"""
        self.logger.info("💡 交互式控制说明:")
        self.logger.info("   输入 'help' 查看所有命令")
        self.logger.info("   输入 'quit' 退出程序")
        
        while self.running:
            try:
                user_input = input().strip().lower()
                
                if user_input == 'quit' or user_input == 'q':
                    self.logger.info("🛑 用户请求退出")
                    self.running = False
                    break
                elif user_input == 'help' or user_input == 'h':
                    self.show_help()
                elif user_input == 'enable' or user_input == 'e':
                    self.enabled = True
                    self.logger.info("✅ 自动发送已启用")
                elif user_input == 'disable' or user_input == 'd':
                    self.enabled = False
                    self.logger.info("❌ 自动发送已禁用")
                elif user_input == 'send' or user_input == 's':
                    self.send_continue_command()
                elif user_input == 'status':
                    self.show_status()
                elif user_input.startswith('interval '):
                    try:
                        new_interval = int(user_input.split()[1])
                        if new_interval > 0:
                            self.interval_minutes = new_interval
                            self.logger.info(f"⏰ 间隔已设置为 {new_interval} 分钟")
                        else:
                            self.logger.warning("⚠️ 间隔必须大于0")
                    except (IndexError, ValueError):
                        self.logger.warning("⚠️ 格式错误，使用: interval <分钟数>")
                elif user_input:
                    self.logger.warning(f"❓ 未知命令: {user_input}，输入 'help' 查看帮助")
                    
            except (EOFError, KeyboardInterrupt):
                break
    
    def show_help(self):
        """显示帮助信息"""
        self.logger.info("📚 可用命令:")
        self.logger.info("   help, h      - 显示此帮助")
        self.logger.info("   quit, q      - 退出程序")
        self.logger.info("   enable, e    - 启用自动发送")
        self.logger.info("   disable, d   - 禁用自动发送")
        self.logger.info("   send, s      - 立即发送continue命令")
        self.logger.info("   status       - 显示当前状态")
        self.logger.info("   interval <N> - 设置间隔为N分钟")
    
    def show_status(self):
        """显示当前状态"""
        status = "启用" if self.enabled else "禁用"
        self.logger.info(f"📊 当前状态:")
        self.logger.info(f"   自动发送: {status}")
        self.logger.info(f"   发送间隔: {self.interval_minutes} 分钟")
        self.logger.info(f"   程序运行: {'是' if self.running else '否'}")
    
    def start(self):
        """启动监控"""
        self.running = True
        
        # 启动定时器线程
        timer_thread = threading.Thread(target=self.timer_thread, daemon=True)
        timer_thread.start()
        
        self.logger.info("🚀 定时器监控已启动")
        self.logger.info(f"⏰ 将每 {self.interval_minutes} 分钟自动处理continue命令")
        self.show_status()
        print("\n" + "="*50)
        
        try:
            # 启动交互式控制
            self.interactive_controls()
        except KeyboardInterrupt:
            self.logger.info("接收到Ctrl+C信号")
        finally:
            self.stop()
    
    def stop(self):
        """停止监控"""
        self.running = False
        self.logger.info("🛑 定时器监控已停止")

def main():
    """主函数"""
    print("🚀 VS Code Copilot Chat 定时器监控工具")
    print("=" * 60)
    print("✨ 特点：")
    print("   • 完全无需安装OCR或其他复杂软件")
    print("   • 简单的定时器机制")
    print("   • 支持自动发送或剪贴板辅助")
    print("   • 交互式控制界面")
    print()
    print("🎯 工作原理：")
    print("   1. 每隔指定时间（默认2分钟）")
    print("   2. 自动发送continue命令到VS Code Copilot Chat")
    print("   3. 或者将命令复制到剪贴板供您手动粘贴")
    print()
    print("💡 优势：")
    print("   • 无需复杂的状态检测")
    print("   • 不依赖屏幕截图或OCR")
    print("   • 轻量级，资源占用极少")
    print("   • 可以完全控制发送频率")
    print()
    print("⚠️  注意：")
    print("   • 确保VS Code和Copilot Chat正在运行")
    print("   • 可选安装pyautogui和pygetwindow以启用完全自动化")
    print("=" * 60)
    print()
    
    monitor = TimerCopilotMonitor()
    
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
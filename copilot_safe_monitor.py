#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VS Code Copilot Chat 安全监控工具
更安全的方案，不会干扰用户当前操作
"""

import time
import logging
import sys
import threading
from datetime import datetime
import json
import os

class SafeCopilotMonitor:
    """安全的Copilot监控器"""
    
    def __init__(self):
        """初始化监控器"""
        self.setup_logging()
        self.running = False
        self.enabled = True
        
        # 配置设置
        self.interval_minutes = 2
        self.continue_command = 'continue'
        
        # 安全设置
        self.safe_mode = True  # 安全模式，避免干扰用户操作
        
        self.logger.info("🛡️ 安全监控工具初始化完成")
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('safe_copilot_monitor.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def is_user_active(self) -> bool:
        """检测用户是否正在活跃操作"""
        try:
            import psutil
            
            # 检查CPU使用率（简单的活跃度指标）
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 如果CPU使用率高，可能用户正在工作
            if cpu_percent > 20:
                self.logger.debug(f"检测到用户活跃 (CPU: {cpu_percent}%)")
                return True
                
            return False
            
        except ImportError:
            # 如果没有psutil，假设用户不活跃
            return False
        except Exception as e:
            self.logger.debug(f"活跃度检测失败: {e}")
            return False
    
    def get_current_window_title(self) -> str:
        """获取当前活动窗口标题"""
        try:
            import pygetwindow as gw
            
            # 获取当前活动窗口
            active_window = gw.getActiveWindow()
            if active_window:
                return active_window.title
            return ""
            
        except Exception:
            return ""
    
    def is_vscode_active(self) -> bool:
        """检查VS Code是否是当前活动窗口"""
        current_title = self.get_current_window_title()
        return 'Visual Studio Code' in current_title
    
    def send_via_clipboard_safe(self) -> bool:
        """安全的剪贴板方案"""
        try:
            import pyperclip
            
            # 只有在安全的情况下才操作剪贴板
            if self.safe_mode and self.is_user_active():
                self.logger.info("🛡️ 检测到用户活跃，跳过剪贴板操作（安全模式）")
                return False
            
            # 备份剪贴板
            original_clipboard = ""
            try:
                original_clipboard = pyperclip.paste()
            except:
                pass
            
            # 复制命令
            pyperclip.copy(self.continue_command)
            
            self.logger.info("📋 continue命令已安全复制到剪贴板")
            self.logger.info("💡 请在方便时切换到VS Code Copilot Chat并粘贴")
            
            # 延迟恢复剪贴板，给用户时间粘贴
            def restore_clipboard():
                time.sleep(30)  # 30秒后恢复
                try:
                    if original_clipboard:
                        pyperclip.copy(original_clipboard)
                        self.logger.debug("剪贴板已恢复")
                except:
                    pass
            
            # 在后台线程中恢复剪贴板
            threading.Thread(target=restore_clipboard, daemon=True).start()
            
            return True
            
        except ImportError:
            self.logger.debug("pyperclip 未安装")
            return False
        except Exception as e:
            self.logger.error(f"剪贴板操作失败: {e}")
            return False
    
    def send_via_automation_safe(self) -> bool:
        """安全的自动化方案"""
        try:
            import pyautogui
            import pygetwindow as gw
            
            # 安全检查
            if self.safe_mode:
                # 检查用户是否活跃
                if self.is_user_active():
                    self.logger.info("🛡️ 检测到用户活跃，跳过自动化操作（安全模式）")
                    return False
                
                # 检查VS Code是否是活动窗口
                if not self.is_vscode_active():
                    self.logger.info("🛡️ VS Code不是活动窗口，跳过自动化操作（安全模式）")
                    return False
            
            # 查找VS Code窗口
            windows = gw.getWindowsWithTitle('Visual Studio Code')
            if not windows:
                self.logger.warning("⚠️ 未找到VS Code窗口")
                return False
            
            window = windows[0]
            
            self.logger.info("🤖 安全发送continue命令...")
            
            # 确保窗口已经是活动的
            if not window.isActive:
                # 只有在安全模式关闭时才切换窗口
                if not self.safe_mode:
                    window.activate()
                    time.sleep(0.5)
                else:
                    self.logger.info("🛡️ 安全模式：不切换窗口焦点")
                    return False
            
            # 尝试多种Copilot Chat打开方式
            methods = [
                ('ctrl', 'shift', 'i'),  # 常见的Copilot Chat快捷键
                ('ctrl', 'i'),           # 另一种快捷键
                ('ctrl', 'shift', 'p'),  # 命令面板方式
            ]
            
            for method in methods:
                try:
                    self.logger.debug(f"尝试快捷键: {'+'.join(method)}")
                    pyautogui.hotkey(*method)
                    time.sleep(0.5)
                    
                    # 如果是命令面板，输入命令
                    if method == ('ctrl', 'shift', 'p'):
                        pyautogui.write('Copilot Chat: Focus on Copilot Chat View', interval=0.02)
                        pyautogui.press('enter')
                        time.sleep(0.5)
                    
                    # 输入continue命令
                    pyautogui.write(self.continue_command, interval=0.03)
                    time.sleep(0.3)
                    
                    # 发送
                    pyautogui.press('enter')
                    
                    self.logger.info("✅ continue命令已安全发送")
                    return True
                    
                except Exception as e:
                    self.logger.debug(f"方法 {method} 失败: {e}")
                    continue
            
            self.logger.warning("❌ 所有自动化方法都失败了")
            return False
            
        except ImportError:
            self.logger.debug("自动化库未安装")
            return False
        except Exception as e:
            self.logger.error(f"自动化发送失败: {e}")
            return False
    
    def send_notification_only(self) -> bool:
        """仅发送通知，不执行任何操作"""
        current_time = datetime.now().strftime("%H:%M:%S")
        
        self.logger.info("🔔 " + "="*50)
        self.logger.info(f"🕐 {current_time} - 是时候发送 continue 命令了！")
        self.logger.info("💡 请手动在VS Code Copilot Chat中输入: continue")
        self.logger.info("🔔 " + "="*50)
        
        # 可选：系统通知（如果支持）
        try:
            import plyer
            plyer.notification.notify(
                title="Copilot Chat 提醒",
                message="是时候发送 continue 命令了！",
                timeout=5
            )
        except ImportError:
            pass
        except Exception:
            pass
        
        return True
    
    def send_continue_command(self) -> bool:
        """安全发送continue命令"""
        if not self.enabled:
            return True
        
        current_time = datetime.now().strftime("%H:%M:%S")
        self.logger.info(f"🕐 {current_time} - 准备安全发送continue命令")
        
        # 方案1：尝试安全自动化
        if self.send_via_automation_safe():
            return True
        
        # 方案2：安全剪贴板
        if self.send_via_clipboard_safe():
            return True
        
        # 方案3：仅通知
        return self.send_notification_only()
    
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
            
            time.sleep(10)
    
    def interactive_controls(self):
        """交互式控制"""
        self.logger.info("💡 安全监控控制说明:")
        self.logger.info("   help - 显示帮助")
        self.logger.info("   quit - 退出程序")
        self.logger.info("   safe on/off - 开启/关闭安全模式")
        self.logger.info("   send - 立即发送命令")
        
        while self.running:
            try:
                user_input = input().strip().lower()
                
                if user_input in ['quit', 'q']:
                    self.running = False
                    break
                elif user_input in ['help', 'h']:
                    self.show_help()
                elif user_input in ['enable', 'e']:
                    self.enabled = True
                    self.logger.info("✅ 自动发送已启用")
                elif user_input in ['disable', 'd']:
                    self.enabled = False
                    self.logger.info("❌ 自动发送已禁用")
                elif user_input in ['send', 's']:
                    self.send_continue_command()
                elif user_input == 'safe on':
                    self.safe_mode = True
                    self.logger.info("🛡️ 安全模式已开启")
                elif user_input == 'safe off':
                    self.safe_mode = False
                    self.logger.info("⚠️ 安全模式已关闭")
                elif user_input == 'status':
                    self.show_status()
                elif user_input.startswith('interval '):
                    try:
                        new_interval = int(user_input.split()[1])
                        if new_interval > 0:
                            self.interval_minutes = new_interval
                            self.logger.info(f"⏰ 间隔已设置为 {new_interval} 分钟")
                    except (IndexError, ValueError):
                        self.logger.warning("⚠️ 格式错误，使用: interval <分钟数>")
                elif user_input:
                    self.logger.warning(f"❓ 未知命令: {user_input}")
                    
            except (EOFError, KeyboardInterrupt):
                break
    
    def show_help(self):
        """显示帮助"""
        self.logger.info("📚 可用命令:")
        self.logger.info("   help/h       - 显示此帮助")
        self.logger.info("   quit/q       - 退出程序")
        self.logger.info("   enable/e     - 启用自动发送")
        self.logger.info("   disable/d    - 禁用自动发送")
        self.logger.info("   send/s       - 立即发送continue命令")
        self.logger.info("   safe on/off  - 开启/关闭安全模式")
        self.logger.info("   status       - 显示当前状态")
        self.logger.info("   interval <N> - 设置间隔为N分钟")
    
    def show_status(self):
        """显示状态"""
        self.logger.info("📊 当前状态:")
        self.logger.info(f"   自动发送: {'启用' if self.enabled else '禁用'}")
        self.logger.info(f"   安全模式: {'开启' if self.safe_mode else '关闭'}")
        self.logger.info(f"   发送间隔: {self.interval_minutes} 分钟")
        self.logger.info(f"   程序运行: {'是' if self.running else '否'}")
    
    def start(self):
        """启动监控"""
        self.running = True
        
        # 启动定时器线程
        timer_thread = threading.Thread(target=self.timer_thread, daemon=True)
        timer_thread.start()
        
        self.logger.info("🛡️ 安全监控已启动")
        self.show_status()
        print("\n" + "="*50)
        
        try:
            self.interactive_controls()
        except KeyboardInterrupt:
            self.logger.info("接收到Ctrl+C信号")
        finally:
            self.stop()
    
    def stop(self):
        """停止监控"""
        self.running = False
        self.logger.info("🛑 安全监控已停止")

def main():
    """主函数"""
    print("🛡️ VS Code Copilot Chat 安全监控工具")
    print("=" * 60)
    print("✨ 特点：")
    print("   • 安全模式，不会干扰用户操作")
    print("   • 智能检测用户活跃状态")
    print("   • 多种发送方式自动切换")
    print("   • 完全可控的行为")
    print()
    print("🛡️ 安全机制：")
    print("   • 检测用户是否正在操作")
    print("   • 避免在用户工作时发送命令")
    print("   • 不会强制切换窗口焦点")
    print("   • 优先使用剪贴板等安全方式")
    print()
    print("💡 使用建议：")
    print("   • 建议保持安全模式开启")
    print("   • 如需完全自动化，可关闭安全模式")
    print("=" * 60)
    print()
    
    monitor = SafeCopilotMonitor()
    
    try:
        monitor.start()
    except Exception as e:
        print(f"程序出错: {e}")
    finally:
        monitor.stop()

if __name__ == "__main__":
    main() 
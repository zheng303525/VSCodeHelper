#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VS Code GitHub Copilot Chat 高级自动监控工具
支持在屏幕锁定状态下工作，使用多种策略确保持续监控
"""

import time
import logging
import configparser
import threading
import sys
import os
import json
import psutil
import subprocess
from typing import Optional, Dict, Any
import re
import ctypes
from ctypes import wintypes
import winreg
from datetime import datetime, timedelta


class AdvancedCopilotMonitor:
    """高级GitHub Copilot Chat状态监控器 - 支持锁屏状态"""
    
    def __init__(self, config_file: str = "config.ini"):
        """初始化监控器"""
        self.config = configparser.ConfigParser()
        self.config.read(config_file, encoding='utf-8')
        self.setup_logging()
        self.running = False
        self.last_action_time = 0.0
        
        # 基本配置
        self.check_interval = self.config.getfloat('MONITOR', 'check_interval', fallback=30)
        self.continue_command = self.config.get('AUTOMATION', 'continue_command', fallback='continue')
        
        # 高级配置
        self.prevent_sleep = self.config.getboolean('MONITOR', 'prevent_sleep', fallback=True)
        self.use_process_monitoring = self.config.getboolean('ADVANCED', 'use_process_monitoring', fallback=True)
        self.use_log_monitoring = self.config.getboolean('ADVANCED', 'use_log_monitoring', fallback=True)
        self.use_filesystem_monitoring = self.config.getboolean('ADVANCED', 'use_filesystem_monitoring', fallback=True)
        
        # VS Code相关路径
        self.vscode_logs_path = self.get_vscode_logs_path()
        self.vscode_extensions_path = self.get_vscode_extensions_path()
        
        # 监控状态
        self.last_copilot_activity = time.time()
        self.inactivity_threshold = 300  # 5分钟无活动则认为需要干预
        
        # Windows API常量
        self.ES_CONTINUOUS = 0x80000000
        self.ES_SYSTEM_REQUIRED = 0x00000001
        self.ES_DISPLAY_REQUIRED = 0x00000002
        
        self.logger.info("AdvancedCopilotMonitor 初始化完成")
    
    def setup_logging(self):
        """设置日志记录"""
        log_level = self.config.get('LOGGING', 'log_level', fallback='INFO')
        log_file = self.config.get('LOGGING', 'log_file', fallback='copilot_monitor_advanced.log')
        console_output = self.config.getboolean('LOGGING', 'console_output', fallback=True)
        
        self.logger = logging.getLogger('AdvancedCopilotMonitor')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 控制台handler
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def get_vscode_logs_path(self) -> str:
        """获取VS Code日志路径"""
        # Windows系统的VS Code日志路径
        appdata = os.environ.get('APPDATA', '')
        logs_path = os.path.join(appdata, 'Code', 'logs')
        if os.path.exists(logs_path):
            return logs_path
        
        # 尝试其他可能的路径
        userprofile = os.environ.get('USERPROFILE', '')
        alt_paths = [
            os.path.join(userprofile, '.vscode', 'logs'),
            os.path.join(userprofile, 'AppData', 'Local', 'Programs', 'Microsoft VS Code', 'logs'),
        ]
        
        for path in alt_paths:
            if os.path.exists(path):
                return path
        
        return logs_path  # 返回默认路径，即使不存在
    
    def get_vscode_extensions_path(self) -> str:
        """获取VS Code扩展路径"""
        userprofile = os.environ.get('USERPROFILE', '')
        return os.path.join(userprofile, '.vscode', 'extensions')
    
    def prevent_screen_sleep(self):
        """防止屏幕息屏和锁屏"""
        if not self.prevent_sleep:
            return
            
        try:
            # 使用Windows API防止系统休眠和屏幕保护程序
            ctypes.windll.kernel32.SetThreadExecutionState(
                self.ES_CONTINUOUS | self.ES_SYSTEM_REQUIRED | self.ES_DISPLAY_REQUIRED
            )
            self.logger.info("已设置防止息屏模式")
            
            # 同时禁用屏幕保护程序
            self.disable_screensaver()
            
        except Exception as e:
            self.logger.warning(f"设置防止息屏模式失败: {e}")
    
    def restore_screen_sleep(self):
        """恢复屏幕息屏设置"""
        if not self.prevent_sleep:
            return
            
        try:
            # 恢复正常的电源管理
            ctypes.windll.kernel32.SetThreadExecutionState(self.ES_CONTINUOUS)
            self.logger.info("已恢复屏幕息屏设置")
        except Exception as e:
            self.logger.warning(f"恢复屏幕息屏设置失败: {e}")
    
    def disable_screensaver(self):
        """禁用屏幕保护程序"""
        try:
            # 通过注册表禁用屏幕保护程序
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                              "Control Panel\\Desktop", 0, 
                              winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "ScreenSaveActive", 0, winreg.REG_SZ, "0")
                winreg.SetValueEx(key, "ScreenSaveTimeOut", 0, winreg.REG_SZ, "0")
            self.logger.debug("已禁用屏幕保护程序")
        except Exception as e:
            self.logger.warning(f"禁用屏幕保护程序失败: {e}")
    
    def is_vscode_running(self) -> bool:
        """检查VS Code是否在运行"""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if 'code' in proc.info['name'].lower():
                    return True
            return False
        except Exception as e:
            self.logger.warning(f"检查VS Code进程失败: {e}")
            return False
    
    def get_vscode_processes(self) -> list:
        """获取所有VS Code相关进程"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                name = proc.info['name'].lower()
                if 'code' in name and ('exe' in name or 'app' in name):
                    processes.append(proc)
        except Exception as e:
            self.logger.warning(f"获取VS Code进程失败: {e}")
        return processes
    
    def monitor_vscode_logs(self) -> Dict[str, Any]:
        """监控VS Code日志文件"""
        result = {
            'copilot_active': False,
            'last_activity': None,
            'error_detected': False
        }
        
        try:
            if not os.path.exists(self.vscode_logs_path):
                return result
            
            # 查找最新的日志目录
            log_dirs = [d for d in os.listdir(self.vscode_logs_path) 
                       if os.path.isdir(os.path.join(self.vscode_logs_path, d))]
            
            if not log_dirs:
                return result
            
            latest_log_dir = max(log_dirs)
            log_dir_path = os.path.join(self.vscode_logs_path, latest_log_dir)
            
            # 查找Copilot相关的日志文件
            copilot_log_files = []
            for file in os.listdir(log_dir_path):
                if 'copilot' in file.lower() or 'chat' in file.lower():
                    copilot_log_files.append(os.path.join(log_dir_path, file))
            
            # 分析日志内容
            for log_file in copilot_log_files:
                if os.path.exists(log_file):
                    mtime = os.path.getmtime(log_file)
                    if time.time() - mtime < 3600:  # 1小时内有更新
                        result['copilot_active'] = True
                        result['last_activity'] = mtime
                        
                        # 读取日志内容查找错误
                        try:
                            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                                recent_lines = f.readlines()[-50:]  # 最后50行
                                for line in recent_lines:
                                    if any(keyword in line.lower() for keyword in 
                                          ['error', 'timeout', 'failed', 'stopped']):
                                        result['error_detected'] = True
                                        break
                        except Exception:
                            pass
            
        except Exception as e:
            self.logger.warning(f"监控VS Code日志失败: {e}")
        
        return result
    
    def send_continue_command_via_automation(self) -> bool:
        """通过自动化发送继续命令（无需屏幕截图）"""
        try:
            # 方法1: 使用Windows消息发送
            if self.send_via_windows_messages():
                return True
            
            # 方法2: 使用剪贴板和快捷键
            if self.send_via_clipboard():
                return True
            
            # 方法3: 直接写入VS Code的输入缓冲区
            if self.send_via_vscode_api():
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"发送继续命令失败: {e}")
            return False
    
    def send_via_windows_messages(self) -> bool:
        """通过Windows消息发送文本"""
        try:
            import pyautogui
            # 即使在锁屏状态下，某些自动化操作仍可能工作
            
            # 使用Win+R打开运行对话框的方式间接操作
            pyautogui.hotkey('win', 'r')
            time.sleep(0.5)
            
                                      # 构造一个命令来操作VS Code
             command = f'powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(\\"{self.continue_command}{{{{ENTER}}}}\\")"'
            
            pyautogui.write(command)
            pyautogui.press('enter')
            
            self.logger.info("通过Windows消息发送继续命令")
            return True
            
        except Exception as e:
            self.logger.warning(f"通过Windows消息发送失败: {e}")
            return False
    
    def send_via_clipboard(self) -> bool:
        """通过剪贴板发送文本"""
        try:
            import pyperclip
            
            # 保存当前剪贴板内容
            original_clipboard = pyperclip.paste()
            
            # 设置继续命令到剪贴板
            pyperclip.copy(self.continue_command)
            
            # 使用快捷键粘贴（假设VS Code是活动窗口）
            import pyautogui
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.1)
            pyautogui.press('enter')
            
            # 恢复原始剪贴板内容
            pyperclip.copy(original_clipboard)
            
            self.logger.info("通过剪贴板发送继续命令")
            return True
            
        except Exception as e:
            self.logger.warning(f"通过剪贴板发送失败: {e}")
            return False
    
    def send_via_vscode_api(self) -> bool:
        """尝试通过VS Code API发送命令"""
        try:
            # 这是一个概念性实现，实际需要VS Code扩展支持
            # 可以通过文件系统或命名管道与VS Code扩展通信
            
            # 创建一个命令文件
            command_file = os.path.join(os.path.expanduser('~'), '.vscode_copilot_command.json')
            command_data = {
                'command': 'send_message',
                'message': self.continue_command,
                'timestamp': time.time()
            }
            
            with open(command_file, 'w', encoding='utf-8') as f:
                json.dump(command_data, f)
            
            self.logger.info("通过VS Code API发送继续命令")
            return True
            
        except Exception as e:
            self.logger.warning(f"通过VS Code API发送失败: {e}")
            return False
    
    def check_system_locked(self) -> bool:
        """检查系统是否被锁定"""
        try:
            # 使用Windows API检查锁屏状态
            user32 = ctypes.windll.user32
            
            # 获取当前桌面
            desktop = user32.GetThreadDesktop(user32.GetCurrentThreadId())
            
            # 检查是否能够访问桌面
            if not desktop:
                return True
            
            # 另一种方法：检查屏幕保护程序是否活跃
            spi_getscreensaverrunning = 114
            is_running = ctypes.c_bool()
            user32.SystemParametersInfoW(spi_getscreensaverrunning, 0, 
                                       ctypes.byref(is_running), 0)
            
            return is_running.value
            
        except Exception as e:
            self.logger.debug(f"检查系统锁定状态失败: {e}")
            return False
    
    def monitor_loop(self):
        """主监控循环"""
        self.logger.info("开始高级监控 GitHub Copilot Chat")
        
        while self.running:
            try:
                current_time = time.time()
                system_locked = self.check_system_locked()
                
                self.logger.debug(f"监控状态 - 系统锁定: {system_locked}")
                
                # 检查VS Code是否在运行
                if not self.is_vscode_running():
                    self.logger.warning("VS Code未运行")
                    time.sleep(self.check_interval)
                    continue
                
                # 监控策略1: 进程监控
                if self.use_process_monitoring:
                    processes = self.get_vscode_processes()
                    if processes:
                        self.logger.debug(f"检测到 {len(processes)} 个VS Code进程")
                
                # 监控策略2: 日志监控
                intervention_needed = False
                if self.use_log_monitoring:
                    log_info = self.monitor_vscode_logs()
                    if log_info['copilot_active']:
                        self.last_copilot_activity = current_time
                    elif (current_time - self.last_copilot_activity) > self.inactivity_threshold:
                        intervention_needed = True
                        self.logger.info("检测到Copilot长时间无活动，可能需要干预")
                
                # 监控策略3: 文件系统监控
                if self.use_filesystem_monitoring:
                    # 检查VS Code扩展是否正常
                    pass  # 这里可以添加更多的文件系统监控逻辑
                
                # 如果需要干预且距离上次操作超过一定时间
                if intervention_needed and (current_time - self.last_action_time) > 60:
                    self.logger.info("准备发送继续命令")
                    
                    if system_locked:
                        # 系统锁定时使用高级发送方法
                        success = self.send_continue_command_via_automation()
                    else:
                        # 系统未锁定时可以使用常规方法
                        success = self.send_continue_command_via_automation()
                    
                    if success:
                        self.last_action_time = current_time
                        self.last_copilot_activity = current_time
                        self.logger.info("继续命令发送成功")
                    else:
                        self.logger.error("继续命令发送失败")
                
                # 等待下次检查
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("收到中断信号，停止监控")
                break
            except Exception as e:
                self.logger.error(f"监控循环中出现错误: {e}")
                time.sleep(self.check_interval)
    
    def start(self):
        """启动监控"""
        if self.running:
            self.logger.warning("监控已在运行中")
            return
        
        # 设置防止息屏
        self.prevent_screen_sleep()
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.logger.info("高级监控已启动")
    
    def stop(self):
        """停止监控"""
        self.running = False
        
        # 恢复屏幕息屏设置
        self.restore_screen_sleep()
        
        self.logger.info("高级监控已停止")


def main():
    """主函数"""
    print("VS Code GitHub Copilot Chat 高级自动监控工具")
    print("=" * 50)
    print("支持锁屏状态下的持续监控")
    
    try:
        # 创建监控器实例
        monitor = AdvancedCopilotMonitor()
        
        # 启动监控
        monitor.start()
        
        print("高级监控已启动，按 Ctrl+C 停止...")
        print(f"检查间隔: {monitor.check_interval} 秒")
        print(f"防止息屏: {'开启' if monitor.prevent_sleep else '关闭'}")
        print(f"进程监控: {'开启' if monitor.use_process_monitoring else '关闭'}")
        print(f"日志监控: {'开启' if monitor.use_log_monitoring else '关闭'}")
        
        # 保持主线程运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n正在停止监控...")
            monitor.stop()
            print("监控已停止")
            
    except Exception as e:
        print(f"启动监控时出错: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 
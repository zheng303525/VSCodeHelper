#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VS Code GitHub Copilot Chat 自动监控工具
自动检测Copilot Chat状态，当停止时发送continue命令
"""

import time
import logging
import configparser
import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import pytesseract
from PIL import Image, ImageEnhance
import threading
import sys
import os
from typing import Optional, Tuple, List
import re
import ctypes
from ctypes import wintypes


class CopilotMonitor:
    """GitHub Copilot Chat 状态监控器"""
    
    def __init__(self, config_file: str = "config.ini"):
        """初始化监控器"""
        self.config = configparser.ConfigParser()
        self.config.read(config_file, encoding='utf-8')
        self.setup_logging()
        self.running = False
        self.last_action_time = 0.0
        
        # 从配置文件读取设置
        self.check_interval = self.config.getfloat('MONITOR', 'check_interval', fallback=30)
        self.vscode_title = self.config.get('MONITOR', 'vscode_window_title', fallback='Visual Studio Code')
        self.chat_panel_title = self.config.get('MONITOR', 'chat_panel_title', fallback='GitHub Copilot Chat')
        
        self.continue_command = self.config.get('AUTOMATION', 'continue_command', fallback='continue')
        self.continue_command_alt = self.config.get('AUTOMATION', 'continue_command_alt', fallback='继续')
        self.send_delay = self.config.getfloat('AUTOMATION', 'send_delay', fallback=1.0)
        self.input_delay = self.config.getfloat('AUTOMATION', 'input_delay', fallback=0.5)
        
        self.stopped_keywords = [k.strip() for k in 
                                self.config.get('DETECTION', 'stopped_keywords', 
                                              fallback='stopped,completed,finished,done,等待,完成').split(',')]
        self.running_keywords = [k.strip() for k in 
                                self.config.get('DETECTION', 'running_keywords',
                                              fallback='thinking,processing,generating,working,运行中,处理中').split(',')]
        self.ocr_confidence = self.config.getfloat('DETECTION', 'ocr_confidence', fallback=0.6)
        
        # 设置pyautogui安全设置
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # 防止息屏配置
        self.prevent_sleep = self.config.getboolean('MONITOR', 'prevent_sleep', fallback=True)
        self.screen_saver_timeout = None
        self.power_timeout = None
        
        # Windows API常量
        self.ES_CONTINUOUS = 0x80000000
        self.ES_SYSTEM_REQUIRED = 0x00000001
        self.ES_DISPLAY_REQUIRED = 0x00000002
        
        self.logger.info("CopilotMonitor 初始化完成")
    
    def setup_logging(self):
        """设置日志记录"""
        log_level = self.config.get('LOGGING', 'log_level', fallback='INFO')
        log_file = self.config.get('LOGGING', 'log_file', fallback='copilot_monitor.log')
        console_output = self.config.getboolean('LOGGING', 'console_output', fallback=True)
        
        # 创建logger
        self.logger = logging.getLogger('CopilotMonitor')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # 创建formatter
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
    
    def prevent_screen_sleep(self):
        """防止屏幕息屏和锁屏"""
        if not self.prevent_sleep:
            return
            
        try:
            # 使用Windows API防止系统休眠和屏幕保护程序
            ctypes.windll.kernel32.SetThreadExecutionState(
                self.ES_CONTINUOUS | self.ES_SYSTEM_REQUIRED | self.ES_DISPLAY_REQUIRED
            )
            self.logger.debug("已设置防止息屏模式")
        except Exception as e:
            self.logger.warning(f"设置防止息屏模式失败: {e}")
    
    def restore_screen_sleep(self):
        """恢复屏幕息屏设置"""
        if not self.prevent_sleep:
            return
            
        try:
            # 恢复正常的电源管理
            ctypes.windll.kernel32.SetThreadExecutionState(self.ES_CONTINUOUS)
            self.logger.debug("已恢复屏幕息屏设置")
        except Exception as e:
            self.logger.warning(f"恢复屏幕息屏设置失败: {e}")
    
    def simulate_user_activity(self):
        """模拟用户活动以防止锁屏"""
        try:
            # 获取当前鼠标位置
            current_pos = pyautogui.position()
            # 轻微移动鼠标然后移回原位置
            pyautogui.move(1, 1, duration=0.1)
            time.sleep(0.1)
            pyautogui.move(-1, -1, duration=0.1)
            self.logger.debug(f"模拟用户活动: 鼠标位置 {current_pos}")
        except Exception as e:
            self.logger.warning(f"模拟用户活动失败: {e}")
    
    def find_vscode_window(self) -> Optional[gw.Win32Window]:
        """查找VS Code窗口"""
        try:
            windows = gw.getWindowsWithTitle(self.vscode_title)
            if windows:
                # 返回第一个找到的VS Code窗口
                window = windows[0]
                if window.isMinimized:
                    window.restore()
                return window
            return None
        except Exception as e:
            self.logger.error(f"查找VS Code窗口时出错: {e}")
            return None
    
    def capture_chat_area(self, window: gw.Win32Window) -> Optional[np.ndarray]:
        """截取聊天区域的屏幕截图"""
        try:
            # 激活窗口
            window.activate()
            time.sleep(0.5)
            
            # 获取窗口位置和大小
            left, top, width, height = window.left, window.top, window.width, window.height
            
            # 截取整个VS Code窗口
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            
            # 转换为OpenCV格式
            img_array = np.array(screenshot)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # 假设聊天区域在右侧，取右半部分
            chat_area = img_bgr[:, width//2:]
            
            return chat_area
        except Exception as e:
            self.logger.error(f"截取聊天区域时出错: {e}")
            return None
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """预处理图像以提高OCR识别率"""
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 增强对比度
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            # 降噪
            denoised = cv2.medianBlur(enhanced, 3)
            
            # 二值化
            _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            return binary
        except Exception as e:
            self.logger.error(f"图像预处理时出错: {e}")
            return image
    
    def extract_text_from_image(self, image: np.ndarray) -> str:
        """从图像中提取文本"""
        try:
            # 预处理图像
            processed_img = self.preprocess_image(image)
            
            # 使用pytesseract进行OCR
            # 配置OCR参数，支持中英文
            custom_config = r'--oem 3 --psm 6 -l eng+chi_sim'
            text = pytesseract.image_to_string(processed_img, config=custom_config)
            
            return text.strip()
        except Exception as e:
            self.logger.error(f"OCR文本提取时出错: {e}")
            return ""
    
    def analyze_chat_status(self, text: str) -> str:
        """分析聊天状态"""
        text_lower = text.lower()
        
        # 检查是否包含运行中的关键词
        for keyword in self.running_keywords:
            if keyword.lower() in text_lower:
                return "running"
        
        # 检查是否包含停止的关键词
        for keyword in self.stopped_keywords:
            if keyword.lower() in text_lower:
                return "stopped"
        
        # 默认返回未知状态
        return "unknown"
    
    def find_chat_input_area(self, window: gw.Win32Window) -> Optional[Tuple[int, int]]:
        """查找聊天输入框的位置"""
        try:
            # 简单策略：假设输入框在窗口底部中央
            input_x = window.left + window.width * 3 // 4  # 右侧3/4位置
            input_y = window.top + window.height - 100     # 底部往上100像素
            
            return (input_x, input_y)
        except Exception as e:
            self.logger.error(f"查找输入框位置时出错: {e}")
            return None
    
    def send_continue_command(self, window: gw.Win32Window):
        """发送继续命令"""
        try:
            # 激活窗口
            window.activate()
            time.sleep(0.5)
            
            # 查找输入框位置
            input_pos = self.find_chat_input_area(window)
            if not input_pos:
                self.logger.error("无法找到输入框位置")
                return False
            
            # 点击输入框
            pyautogui.click(input_pos[0], input_pos[1])
            time.sleep(self.input_delay)
            
            # 清空输入框（选择全部并删除）
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.press('delete')
            time.sleep(0.1)
            
            # 输入继续命令
            pyautogui.write(self.continue_command, interval=0.05)
            time.sleep(self.input_delay)
            
            # 发送消息（按Enter键）
            pyautogui.press('enter')
            
            self.logger.info(f"已发送继续命令: {self.continue_command}")
            self.last_action_time = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"发送继续命令时出错: {e}")
            return False
    
    def monitor_loop(self):
        """主监控循环"""
        self.logger.info("开始监控 GitHub Copilot Chat")
        last_activity_time = time.time()
        
        while self.running:
            try:
                # 查找VS Code窗口
                window = self.find_vscode_window()
                if not window:
                    self.logger.warning("未找到VS Code窗口")
                    time.sleep(self.check_interval)
                    continue
                
                # 截取聊天区域
                chat_image = self.capture_chat_area(window)
                if chat_image is None:
                    self.logger.warning("无法截取聊天区域")
                    time.sleep(self.check_interval)
                    continue
                
                # 提取文本
                text = self.extract_text_from_image(chat_image)
                if not text:
                    self.logger.debug("未检测到文本内容")
                    time.sleep(self.check_interval)
                    continue
                
                # 分析状态
                status = self.analyze_chat_status(text)
                self.logger.debug(f"检测到状态: {status}")
                
                # 如果检测到停止状态，并且距离上次操作超过一定时间
                if status == "stopped" and (time.time() - self.last_action_time) > 60:
                    self.logger.info("检测到Copilot Chat已停止，准备发送继续命令")
                    if self.send_continue_command(window):
                        self.logger.info("继续命令发送成功")
                    else:
                        self.logger.error("继续命令发送失败")
                
                # 定期模拟用户活动以防止锁屏（每5分钟一次）
                current_time = time.time()
                if self.prevent_sleep and (current_time - last_activity_time) > 300:  # 5分钟
                    self.simulate_user_activity()
                    last_activity_time = current_time
                
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
        
        self.logger.info("监控已启动")
    
    def stop(self):
        """停止监控"""
        self.running = False
        
        # 恢复屏幕息屏设置
        self.restore_screen_sleep()
        
        self.logger.info("监控已停止")


def main():
    """主函数"""
    print("VS Code GitHub Copilot Chat 自动监控工具")
    print("=" * 50)
    
    try:
        # 创建监控器实例
        monitor = CopilotMonitor()
        
        # 启动监控
        monitor.start()
        
        print("监控已启动，按 Ctrl+C 停止...")
        print(f"检查间隔: {monitor.check_interval} 秒")
        print(f"监控窗口: {monitor.vscode_title}")
        
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
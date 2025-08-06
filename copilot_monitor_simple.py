#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VS Code GitHub Copilot Chat 简化监控工具
不依赖OCR，使用图像匹配和像素检测
"""

import time
import logging
import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
from PIL import Image
import threading
import sys
import os
from typing import Optional, Tuple
import hashlib

class SimpleCopilotMonitor:
    """简化的GitHub Copilot Chat状态监控器 - 无需OCR"""
    
    def __init__(self):
        """初始化监控器"""
        self.setup_logging()
        self.running = False
        self.last_action_time = 0.0
        
        # 基本设置
        self.check_interval = 15  # 检查间隔（秒）
        self.vscode_title = 'Visual Studio Code'
        self.continue_command = 'continue'
        self.send_delay = 1.0
        
        # 图像匹配设置
        self.last_screenshot_hash = None
        self.static_counter = 0
        self.static_threshold = 3  # 连续3次相同截图认为是静止状态
        
        # 像素检测设置
        self.cursor_blink_area = None  # 光标闪烁区域
        self.last_cursor_state = None
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('simple_copilot_monitor.log', encoding='utf-8'),
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
    
    def capture_chat_area(self, window: gw.Win32Window) -> Optional[np.ndarray]:
        """截取聊天区域"""
        try:
            # 激活窗口
            window.activate()
            time.sleep(0.5)
            
            # 获取窗口位置
            left, top, width, height = window.left, window.top, window.width, window.height
            
            # 假设聊天区域在右半部分
            chat_left = left + width // 2
            chat_top = top + 100  # 跳过标题栏
            chat_width = width // 2 - 50
            chat_height = height - 200  # 留出底部空间
            
            # 截取聊天区域
            screenshot = pyautogui.screenshot(region=(chat_left, chat_top, chat_width, chat_height))
            
            # 转换为OpenCV格式
            img_array = np.array(screenshot)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            return img_bgr
        except Exception as e:
            self.logger.error(f"截取聊天区域时出错: {e}")
            return None
    
    def calculate_image_hash(self, image: np.ndarray) -> str:
        """计算图像哈希值"""
        # 将图像转为灰度并缩小尺寸以提高比较速度
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (64, 64))
        # 计算哈希
        return hashlib.md5(resized.tobytes()).hexdigest()
    
    def detect_static_content(self, image: np.ndarray) -> bool:
        """检测内容是否静止不变"""
        current_hash = self.calculate_image_hash(image)
        
        if self.last_screenshot_hash == current_hash:
            self.static_counter += 1
        else:
            self.static_counter = 0
            self.last_screenshot_hash = current_hash
        
        return self.static_counter >= self.static_threshold
    
    def detect_cursor_activity(self, image: np.ndarray) -> bool:
        """检测光标活动（简单的像素变化检测）"""
        try:
            # 转换为灰度图像
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 寻找可能的光标区域（通常在底部输入框附近）
            height, width = gray.shape
            input_area = gray[int(height * 0.8):, :]  # 底部20%区域
            
            # 检测亮度变化（光标闪烁会导致像素变化）
            if self.last_cursor_state is not None:
                diff = cv2.absdiff(input_area, self.last_cursor_state)
                activity_level = np.sum(diff > 30)  # 统计变化的像素数
                
                self.last_cursor_state = input_area.copy()
                
                # 如果变化的像素数很少，可能是光标闪烁
                return 5 < activity_level < 100
            else:
                self.last_cursor_state = input_area.copy()
                return False
        except Exception as e:
            self.logger.debug(f"检测光标活动时出错: {e}")
            return False
    
    def detect_loading_animation(self, image: np.ndarray) -> bool:
        """检测加载动画或思考状态"""
        try:
            # 转换为灰度图像
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 查找圆形或旋转的模式（常见的加载动画）
            circles = cv2.HoughCircles(
                gray, cv2.HOUGH_GRADIENT, 1, 50,
                param1=50, param2=30, minRadius=10, maxRadius=50
            )
            
            if circles is not None:
                return len(circles[0]) > 0
            
            # 检测重复的图案（另一种加载动画检测方法）
            # 使用模板匹配查找重复元素
            height, width = gray.shape
            template_size = min(30, width // 10, height // 10)
            
            if template_size > 10:
                template = gray[:template_size, :template_size]
                result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
                locations = np.where(result >= 0.8)
                
                # 如果找到多个相似的模式，可能是动画
                return len(locations[0]) > 1
            
            return False
        except Exception as e:
            self.logger.debug(f"检测加载动画时出错: {e}")
            return False
    
    def analyze_status_by_pixels(self, image: np.ndarray) -> str:
        """通过像素分析判断状态"""
        # 检测是否有活动（光标闪烁、动画等）
        has_cursor_activity = self.detect_cursor_activity(image)
        has_loading_animation = self.detect_loading_animation(image)
        is_static = self.detect_static_content(image)
        
        if has_loading_animation:
            return "thinking"
        elif has_cursor_activity:
            return "waiting_input"
        elif is_static:
            return "stopped"
        else:
            return "active"
    
    def find_input_area(self, window: gw.Win32Window) -> Tuple[int, int]:
        """寻找输入框位置（基于窗口位置推测）"""
        # 假设输入框在窗口底部中央
        input_x = window.left + window.width * 3 // 4
        input_y = window.top + window.height - 60
        return input_x, input_y
    
    def send_continue_command(self, window: gw.Win32Window) -> bool:
        """发送继续命令"""
        try:
            self.logger.info("准备发送继续命令...")
            
            # 激活窗口
            window.activate()
            time.sleep(0.5)
            
            # 查找输入框位置
            input_x, input_y = self.find_input_area(window)
            
            # 点击输入框
            pyautogui.click(input_x, input_y)
            time.sleep(0.5)
            
            # 清空输入框
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.press('delete')
            time.sleep(0.1)
            
            # 输入继续命令
            pyautogui.write(self.continue_command, interval=0.05)
            time.sleep(0.5)
            
            # 发送消息
            pyautogui.press('enter')
            
            self.logger.info(f"已发送继续命令: {self.continue_command}")
            self.last_action_time = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"发送继续命令时出错: {e}")
            return False
    
    def monitor_loop(self):
        """主监控循环"""
        self.logger.info("开始简化监控 GitHub Copilot Chat")
        self.logger.info("使用图像匹配和像素检测，无需OCR")
        
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
                
                # 分析状态
                status = self.analyze_status_by_pixels(chat_image)
                self.logger.debug(f"检测到状态: {status}")
                
                # 如果检测到停止状态，并且距离上次操作超过一定时间
                if status == "stopped" and (time.time() - self.last_action_time) > 60:
                    self.logger.info("检测到可能的停止状态，准备发送继续命令")
                    if self.send_continue_command(window):
                        self.logger.info("继续命令发送成功")
                        # 重置静态计数器
                        self.static_counter = 0
                        self.last_screenshot_hash = None
                    else:
                        self.logger.error("继续命令发送失败")
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("接收到停止信号")
                break
            except Exception as e:
                self.logger.error(f"监控循环出错: {e}")
                time.sleep(self.check_interval)
    
    def start(self):
        """启动监控"""
        self.running = True
        try:
            self.monitor_loop()
        except KeyboardInterrupt:
            self.logger.info("监控被用户中断")
        finally:
            self.stop()
    
    def stop(self):
        """停止监控"""
        self.running = False
        self.logger.info("监控已停止")

def main():
    """主函数"""
    print("🚀 VS Code Copilot Chat 简化监控工具")
    print("=" * 50)
    print("✨ 特点：无需安装OCR软件")
    print("🔍 检测方法：图像匹配 + 像素分析")
    print("⚡ 轻量级：只使用Python内置库")
    print()
    
    monitor = SimpleCopilotMonitor()
    
    try:
        print("按 Ctrl+C 停止监控")
        print("-" * 30)
        monitor.start()
    except KeyboardInterrupt:
        print("\n停止监控...")
    finally:
        monitor.stop()

if __name__ == "__main__":
    main() 
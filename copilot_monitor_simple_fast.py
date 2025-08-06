#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VS Code GitHub Copilot Chat 快速监控工具
优化版本：更快的检测间隔
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

class FastCopilotMonitor:
    """快速GitHub Copilot Chat状态监控器"""
    
    def __init__(self):
        """初始化监控器"""
        self.setup_logging()
        self.running = False
        self.last_action_time = 0.0
        
        # 优化后的设置 - 更快检测
        self.check_interval = 5   # 5秒检查一次（原来15秒）
        self.static_threshold = 2  # 连续2次相同即判断静态（原来3次）
        self.cooldown_time = 30   # 30秒冷却时间（原来60秒）
        
        self.vscode_title = 'Visual Studio Code'
        self.continue_command = 'continue'
        self.send_delay = 1.0
        
        # 图像匹配设置
        self.last_screenshot_hash = None
        self.static_counter = 0
        
        # 像素检测设置
        self.cursor_blink_area = None
        self.last_cursor_state = None
        
        self.logger.info("🚀 快速监控工具初始化完成")
        self.logger.info(f"⚡ 检测间隔: {self.check_interval}秒")
        self.logger.info(f"⚡ 静态阈值: {self.static_threshold}次")
        self.logger.info(f"⚡ 冷却时间: {self.cooldown_time}秒")
        self.logger.info(f"⚡ 预计最快检测时间: {self.check_interval * self.static_threshold}秒")
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('fast_copilot_monitor.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def find_vscode_window(self) -> Optional[gw.Win32Window]:
        """查找VS Code窗口"""
        try:
            windows = gw.getWindowsWithTitle(self.vscode_title)
            if windows:
                window = windows[0]
                if window.isMinimized:
                    self.logger.debug("VS Code窗口被最小化")
                    return None
                return window
            else:
                self.logger.debug("未找到VS Code窗口")
                return None
        except Exception as e:
            self.logger.error(f"查找VS Code窗口时出错: {e}")
            return None
    
    def capture_chat_area(self, window: gw.Win32Window) -> Optional[np.ndarray]:
        """截取聊天区域"""
        try:
            # 聚焦窗口
            window.activate()
            time.sleep(0.2)
            
            # 截取右侧区域（Copilot Chat通常在右侧）
            chat_left = window.left + int(window.width * 0.6)
            chat_top = window.top + 60  # 跳过标题栏
            chat_width = int(window.width * 0.4)
            chat_height = window.height - 120  # 减去标题栏和状态栏
            
            screenshot = pyautogui.screenshot(region=(chat_left, chat_top, chat_width, chat_height))
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            self.logger.error(f"截取聊天区域失败: {e}")
            return None
    
    def calculate_image_hash(self, image: np.ndarray) -> str:
        """计算图像哈希用于比较"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (64, 64))
        return hashlib.md5(resized.tobytes()).hexdigest()
    
    def detect_static_content(self, image: np.ndarray) -> bool:
        """检测内容是否静止不变"""
        current_hash = self.calculate_image_hash(image)
        
        if self.last_screenshot_hash == current_hash:
            self.static_counter += 1
            self.logger.debug(f"静态计数: {self.static_counter}/{self.static_threshold}")
        else:
            self.static_counter = 0
            self.last_screenshot_hash = current_hash
            self.logger.debug("检测到图像变化，重置静态计数")
        
        return self.static_counter >= self.static_threshold
    
    def detect_cursor_activity(self, image: np.ndarray) -> bool:
        """检测光标活动"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape
            input_area = gray[int(height * 0.8):, :]
            
            if self.last_cursor_state is not None:
                diff = cv2.absdiff(input_area, self.last_cursor_state)
                activity_level = np.sum(diff > 30)
                self.last_cursor_state = input_area.copy()
                
                is_cursor_active = 5 < activity_level < 100
                if is_cursor_active:
                    self.logger.debug("检测到光标活动")
                return is_cursor_active
            else:
                self.last_cursor_state = input_area.copy()
                return False
        except Exception as e:
            self.logger.debug(f"检测光标活动时出错: {e}")
            return False
    
    def detect_loading_animation(self, image: np.ndarray) -> bool:
        """检测加载动画"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            circles = cv2.HoughCircles(
                gray, cv2.HOUGH_GRADIENT, 1, 50,
                param1=50, param2=30, minRadius=5, maxRadius=30
            )
            
                                      has_loading = circles is not None and len(circles[0]) > 0
             if has_loading:
                 self.logger.debug("检测到可能的加载动画")
             return bool(has_loading)
         except Exception as e:
             self.logger.debug(f"检测加载动画时出错: {e}")
             return False
    
    def analyze_status_by_pixels(self, image: np.ndarray) -> str:
        """通过像素分析判断状态"""
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
    
    def send_continue_command(self, window: gw.Win32Window) -> bool:
        """发送继续命令"""
        try:
            self.logger.info("准备发送continue命令...")
            
            # 确保窗口激活
            window.activate()
            time.sleep(0.3)
            
            # 尝试多种方式打开Copilot Chat
            methods = [
                ('ctrl', 'shift', 'i'),
                ('ctrl', 'i'),
                ('ctrl', 'shift', 'p')
            ]
            
            for i, method in enumerate(methods):
                try:
                    self.logger.debug(f"尝试方法 {i+1}: {'+'.join(method)}")
                    pyautogui.hotkey(*method)
                    time.sleep(0.5)
                    
                    if method == ('ctrl', 'shift', 'p'):
                        pyautogui.write('Copilot Chat: Focus on Copilot Chat View', interval=0.02)
                        pyautogui.press('enter')
                        time.sleep(0.5)
                    
                    pyautogui.write(self.continue_command, interval=0.03)
                    time.sleep(0.3)
                    pyautogui.press('enter')
                    
                    self.logger.info("✅ continue命令发送成功")
                    self.last_action_time = time.time()
                    return True
                    
                except Exception as e:
                    self.logger.debug(f"方法 {i+1} 失败: {e}")
                    if i < len(methods) - 1:
                        time.sleep(0.5)
                        continue
            
            self.logger.warning("❌ 所有发送方法都失败了")
            return False
            
        except Exception as e:
            self.logger.error(f"发送continue命令时出错: {e}")
            return False
    
    def monitor_loop(self):
        """主监控循环"""
        self.logger.info("🔍 开始监控循环...")
        
        while self.running:
            try:
                window = self.find_vscode_window()
                if not window:
                    self.logger.debug("等待VS Code窗口...")
                    time.sleep(self.check_interval)
                    continue
                
                chat_image = self.capture_chat_area(window)
                if chat_image is None:
                    self.logger.warning("无法截取聊天区域")
                    time.sleep(self.check_interval)
                    continue
                
                status = self.analyze_status_by_pixels(chat_image)
                current_time = time.time()
                time_since_last_action = current_time - self.last_action_time
                
                self.logger.debug(f"状态: {status}, 距离上次操作: {time_since_last_action:.1f}秒")
                
                # 快速检测：如果是静态状态且超过冷却时间
                if status == "stopped" and time_since_last_action > self.cooldown_time:
                    self.logger.info(f"🎯 检测到停止状态！({self.static_counter}次静态)")
                    if self.send_continue_command(window):
                        self.logger.info("✅ continue命令发送成功")
                        self.static_counter = 0
                        self.last_screenshot_hash = None
                    else:
                        self.logger.error("❌ continue命令发送失败")
                elif status == "stopped":
                    remaining_time = self.cooldown_time - time_since_last_action
                    self.logger.debug(f"检测到静态，但仍在冷却期 (剩余: {remaining_time:.1f}秒)")
                
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
        print("🚀 快速监控模式启动")
        print(f"⚡ 每 {self.check_interval} 秒检测一次")
        print(f"⚡ 连续 {self.static_threshold} 次静态后判断为停止")
        print(f"⚡ 预计最快 {self.check_interval * self.static_threshold} 秒检测到停止状态")
        print(f"⚡ 冷却时间 {self.cooldown_time} 秒")
        print("📝 按 Ctrl+C 停止监控")
        print("=" * 50)
        
        try:
            self.monitor_loop()
        except KeyboardInterrupt:
            self.logger.info("监控被用户中断")
        finally:
            self.stop()
    
    def stop(self):
        """停止监控"""
        self.running = False
        self.logger.info("🛑 监控已停止")

def main():
    """主函数"""
    print("🚀 VS Code Copilot Chat 快速监控工具")
    print("=" * 50)
    print("⚡ 优化设置：")
    print("   • 检测间隔: 5秒（比标准版快3倍）")
    print("   • 静态阈值: 2次（比标准版快1.5倍）")
    print("   • 冷却时间: 30秒（比标准版快2倍）")
    print("   • 预计最快检测: 10秒")
    print()
    print("📋 需要的依赖：")
    print("   pip install pyautogui pygetwindow opencv-python pillow")
    print("=" * 50)
    print()
    
    monitor = FastCopilotMonitor()
    
    try:
        monitor.start()
    except Exception as e:
        print(f"程序出错: {e}")
    finally:
        monitor.stop()

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VS Code GitHub Copilot Chat 快速监控工具
优化版本：更快的检测间隔 + 详细日志 + 智能窗口处理
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
        self.new_window_message = '按照指令修改代码'  # 新窗口发送的消息
        self.send_delay = 1.0
        
        # 图像匹配设置
        self.last_screenshot_hash = None
        self.static_counter = 0
        
        # 像素检测设置
        self.cursor_blink_area = None
        self.last_cursor_state = None
        
        # 检测统计
        self.detection_stats = {
            'total_checks': 0,
            'static_detections': 0,
            'cursor_activities': 0,
            'loading_animations': 0,
            'commands_sent': 0,
            'new_windows_opened': 0
        }
        
        self.logger.info("🚀 快速监控工具初始化完成")
        self.logger.info(f"⚡ 检测间隔: {self.check_interval}秒")
        self.logger.info(f"⚡ 静态阈值: {self.static_threshold}次")
        self.logger.info(f"⚡ 冷却时间: {self.cooldown_time}秒")
        self.logger.info(f"⚡ 预计最快检测时间: {self.check_interval * self.static_threshold}秒")
        self.logger.info(f"📝 新窗口消息: '{self.new_window_message}'")
        
    def setup_logging(self):
        """设置日志"""
        # 设置更详细的日志级别
        logging.basicConfig(
            level=logging.DEBUG,  # 改为DEBUG级别
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
            self.logger.debug(f"🔍 找到 {len(windows)} 个VS Code窗口")
            
            if windows:
                window = windows[0]
                self.logger.debug(f"📱 窗口信息: {window.title}, 位置: ({window.left}, {window.top}), 大小: {window.width}x{window.height}")
                
                if window.isMinimized:
                    self.logger.warning("⚠️ VS Code窗口被最小化")
                    return None
                    
                self.logger.debug("✅ 找到可用的VS Code窗口")
                return window
            else:
                self.logger.warning("❌ 未找到VS Code窗口")
                return None
        except Exception as e:
            self.logger.error(f"❌ 查找VS Code窗口时出错: {e}")
            return None
    
    def capture_chat_area(self, window: gw.Win32Window) -> Optional[np.ndarray]:
        """截取聊天区域"""
        try:
            # 聚焦窗口
            self.logger.debug("🎯 激活VS Code窗口")
            window.activate()
            time.sleep(0.2)
            
            # 截取右侧区域（Copilot Chat通常在右侧）
            chat_left = window.left + int(window.width * 0.6)
            chat_top = window.top + 60  # 跳过标题栏
            chat_width = int(window.width * 0.4)
            chat_height = window.height - 120  # 减去标题栏和状态栏
            
            self.logger.debug(f"📷 截图区域: ({chat_left}, {chat_top}) 大小: {chat_width}x{chat_height}")
            
            screenshot = pyautogui.screenshot(region=(chat_left, chat_top, chat_width, chat_height))
            image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            self.logger.debug(f"✅ 截图成功，图像大小: {image.shape}")
            return image
        except Exception as e:
            self.logger.error(f"❌ 截取聊天区域失败: {e}")
            return None
    
    def calculate_image_hash(self, image: np.ndarray) -> str:
        """计算图像哈希用于比较"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (64, 64))
        hash_value = hashlib.md5(resized.tobytes()).hexdigest()
        self.logger.debug(f"🔢 图像哈希: {hash_value[:8]}...")
        return hash_value
    
    def detect_static_content(self, image: np.ndarray) -> bool:
        """检测内容是否静止不变"""
        current_hash = self.calculate_image_hash(image)
        
        if self.last_screenshot_hash == current_hash:
            self.static_counter += 1
            self.detection_stats['static_detections'] += 1
            self.logger.info(f"🔄 静态内容检测: {self.static_counter}/{self.static_threshold} (哈希匹配)")
        else:
            if self.static_counter > 0:
                self.logger.info(f"🔄 图像变化，重置静态计数 (从 {self.static_counter} 重置为 0)")
            self.static_counter = 0
            self.last_screenshot_hash = current_hash
            self.logger.debug("🖼️ 检测到图像变化")
        
        is_static = self.static_counter >= self.static_threshold
        if is_static:
            self.logger.info(f"⏹️ 检测到静态状态！连续 {self.static_counter} 次相同图像")
        
        return is_static
    
    def detect_cursor_activity(self, image: np.ndarray) -> bool:
        """检测光标活动"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape
            input_area = gray[int(height * 0.8):, :]
            
            self.logger.debug(f"👆 检查光标区域大小: {input_area.shape}")
            
            if self.last_cursor_state is not None:
                diff = cv2.absdiff(input_area, self.last_cursor_state)
                activity_level = np.sum(diff > 30)
                self.last_cursor_state = input_area.copy()
                
                is_cursor_active = 5 < activity_level < 100
                
                self.logger.debug(f"👆 光标活动级别: {activity_level}, 活跃: {is_cursor_active}")
                
                if is_cursor_active:
                    self.detection_stats['cursor_activities'] += 1
                    self.logger.info("✨ 检测到光标活动 - 可能正在等待输入")
                    
                return is_cursor_active
            else:
                self.last_cursor_state = input_area.copy()
                self.logger.debug("👆 初始化光标状态检测")
                return False
        except Exception as e:
            self.logger.error(f"❌ 检测光标活动时出错: {e}")
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
                self.detection_stats['loading_animations'] += 1
                circle_count = len(circles[0])
                self.logger.info(f"🔄 检测到加载动画! 找到 {circle_count} 个圆形元素")
            else:
                self.logger.debug("🔍 未检测到加载动画")
                
            return bool(has_loading)
        except Exception as e:
            self.logger.error(f"❌ 检测加载动画时出错: {e}")
            return False
    
    def analyze_status_by_pixels(self, image: np.ndarray) -> str:
        """通过像素分析判断状态"""
        self.detection_stats['total_checks'] += 1
        
        self.logger.debug("🔍 开始状态分析...")
        
        has_cursor_activity = self.detect_cursor_activity(image)
        has_loading_animation = self.detect_loading_animation(image)
        is_static = self.detect_static_content(image)
        
        if has_loading_animation:
            status = "thinking"
            self.logger.info("🤔 状态判断: THINKING (检测到加载动画)")
        elif has_cursor_activity:
            status = "waiting_input"
            self.logger.info("⌨️ 状态判断: WAITING_INPUT (检测到光标活动)")
        elif is_static:
            status = "stopped"
            self.logger.info("⏹️ 状态判断: STOPPED (内容静止)")
        else:
            status = "active"
            self.logger.info("🟢 状态判断: ACTIVE (内容变化中)")
        
        return status
    
    def check_chat_window_focus(self, window: gw.Win32Window) -> bool:
        """检查Chat窗口是否已经聚焦/打开"""
        try:
            # 简单的方法：尝试直接输入，如果Chat窗口已打开，应该能直接输入
            self.logger.debug("🔍 检查Chat窗口是否已打开")
            
            # 激活窗口
            window.activate()
            time.sleep(0.2)
            
            # 模拟一个很短的字符输入测试
            pyautogui.write(' ', interval=0.01)  # 输入一个空格
            time.sleep(0.1)
            pyautogui.press('backspace')  # 立即删除
            
            self.logger.debug("✅ Chat窗口可能已经打开")
            return True
            
        except Exception as e:
            self.logger.debug(f"❌ Chat窗口检查失败: {e}")
            return False
    
    def send_continue_command(self, window: gw.Win32Window) -> bool:
        """发送继续命令"""
        try:
            self.logger.info("📤 准备发送命令...")
            
            # 确保窗口激活
            window.activate()
            time.sleep(0.3)
            
            # 首先尝试使用现有Chat窗口
            self.logger.info("🎯 优先尝试使用现有Chat窗口")
            
            try:
                # 直接尝试输入continue命令
                pyautogui.write(self.continue_command, interval=0.03)
                time.sleep(0.3)
                pyautogui.press('enter')
                
                self.logger.info("✅ 使用现有Chat窗口发送continue命令成功")
                self.last_action_time = time.time()
                self.detection_stats['commands_sent'] += 1
                return True
                
            except Exception as e:
                self.logger.warning(f"⚠️ 使用现有窗口失败: {e}")
            
            # 如果现有窗口失败，尝试打开新窗口
            self.logger.info("🆕 尝试打开新的Chat窗口")
            
            # 尝试多种方式打开Copilot Chat
            methods = [
                ('ctrl', 'shift', 'i'),
                ('ctrl', 'i'),
                ('ctrl', 'shift', 'p')
            ]
            
            for i, method in enumerate(methods):
                try:
                    self.logger.info(f"🔑 尝试方法 {i+1}: {'+'.join(method)}")
                    pyautogui.hotkey(*method)
                    time.sleep(0.8)  # 给更多时间让窗口打开
                    
                    if method == ('ctrl', 'shift', 'p'):
                        self.logger.debug("📋 使用命令面板打开Chat")
                        pyautogui.write('Copilot Chat: Focus on Copilot Chat View', interval=0.02)
                        pyautogui.press('enter')
                        time.sleep(1.0)  # 等待Chat窗口打开
                    
                    # 发送新窗口消息
                    self.logger.info(f"📝 发送新窗口消息: '{self.new_window_message}'")
                    pyautogui.write(self.new_window_message, interval=0.03)
                    time.sleep(0.3)
                    pyautogui.press('enter')
                    
                    self.logger.info("✅ 新窗口消息发送成功")
                    self.last_action_time = time.time()
                    self.detection_stats['commands_sent'] += 1
                    self.detection_stats['new_windows_opened'] += 1
                    return True
                    
                except Exception as e:
                    self.logger.warning(f"❌ 方法 {i+1} 失败: {e}")
                    if i < len(methods) - 1:
                        time.sleep(0.5)
                        continue
            
            self.logger.error("❌ 所有发送方法都失败了")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 发送命令时出错: {e}")
            return False
    
    def print_stats(self):
        """打印检测统计信息"""
        stats = self.detection_stats
        self.logger.info("📊 检测统计:")
        self.logger.info(f"   总检测次数: {stats['total_checks']}")
        self.logger.info(f"   静态检测: {stats['static_detections']}")
        self.logger.info(f"   光标活动: {stats['cursor_activities']}")
        self.logger.info(f"   加载动画: {stats['loading_animations']}")
        self.logger.info(f"   发送命令: {stats['commands_sent']}")
        self.logger.info(f"   新窗口: {stats['new_windows_opened']}")
    
    def monitor_loop(self):
        """主监控循环"""
        self.logger.info("🔍 开始监控循环...")
        
        while self.running:
            try:
                self.logger.debug("=" * 60)
                self.logger.debug(f"🔄 第 {self.detection_stats['total_checks'] + 1} 次检测开始")
                
                window = self.find_vscode_window()
                if not window:
                    self.logger.warning("⚠️ 等待VS Code窗口...")
                    time.sleep(self.check_interval)
                    continue
                
                chat_image = self.capture_chat_area(window)
                if chat_image is None:
                    self.logger.warning("❌ 无法截取聊天区域")
                    time.sleep(self.check_interval)
                    continue
                
                status = self.analyze_status_by_pixels(chat_image)
                current_time = time.time()
                time_since_last_action = current_time - self.last_action_time
                
                self.logger.info(f"📊 当前状态: {status}, 距离上次操作: {time_since_last_action:.1f}秒")
                
                # 快速检测：如果是静态状态且超过冷却时间
                if status == "stopped" and time_since_last_action > self.cooldown_time:
                    self.logger.info(f"🎯 检测到停止状态！(静态计数: {self.static_counter})")
                    if self.send_continue_command(window):
                        self.logger.info("✅ 命令发送成功")
                        self.static_counter = 0
                        self.last_screenshot_hash = None
                        self.print_stats()
                    else:
                        self.logger.error("❌ 命令发送失败")
                elif status == "stopped":
                    remaining_time = self.cooldown_time - time_since_last_action
                    self.logger.info(f"⏳ 检测到静态，但仍在冷却期 (剩余: {remaining_time:.1f}秒)")
                
                # 每10次检测打印一次统计
                if self.detection_stats['total_checks'] % 10 == 0:
                    self.print_stats()
                
                self.logger.debug(f"😴 等待 {self.check_interval} 秒后继续检测")
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("⛔ 接收到停止信号")
                break
            except Exception as e:
                self.logger.error(f"❌ 监控循环出错: {e}")
                time.sleep(self.check_interval)
    
    def start(self):
        """启动监控"""
        self.running = True
        print("🚀 快速监控模式启动 (详细日志版)")
        print(f"⚡ 每 {self.check_interval} 秒检测一次")
        print(f"⚡ 连续 {self.static_threshold} 次静态后判断为停止")
        print(f"⚡ 预计最快 {self.check_interval * self.static_threshold} 秒检测到停止状态")
        print(f"⚡ 冷却时间 {self.cooldown_time} 秒")
        print(f"📝 新窗口消息: '{self.new_window_message}'")
        print("📋 按 Ctrl+C 停止监控")
        print("=" * 50)
        
        try:
            self.monitor_loop()
        except KeyboardInterrupt:
            self.logger.info("⛔ 监控被用户中断")
        finally:
            self.stop()
    
    def stop(self):
        """停止监控"""
        self.running = False
        self.print_stats()
        self.logger.info("🛑 监控已停止")

def main():
    """主函数"""
    print("🚀 VS Code Copilot Chat 快速监控工具 (详细日志版)")
    print("=" * 50)
    print("⚡ 优化设置：")
    print("   • 检测间隔: 5秒（比标准版快3倍）")
    print("   • 静态阈值: 2次（比标准版快1.5倍）")
    print("   • 冷却时间: 30秒（比标准版快2倍）")
    print("   • 预计最快检测: 10秒")
    print()
    print("🆕 新功能：")
    print("   • 详细检测日志输出")
    print("   • 优先使用现有Chat窗口")
    print("   • 新窗口发送: '按照指令修改代码'")
    print("   • 检测统计信息")
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
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
        
        # 简化设置 - 只要停止超过30秒就判断为停止
        self.check_interval = 5   # 5秒检查一次
        self.static_threshold = 3  # 连续3次相同即开始计时 (减少误判)
        self.cooldown_time = 30   # 30秒冷却时间
        self.min_static_duration = 30  # 最小静止时间：30秒
        
        self.vscode_title = 'Visual Studio Code'
        self.continue_command = 'continue'
        self.new_window_message = '按照指令修改代码'  # 新窗口发送的消息
        self.send_delay = 1.0
        
        # 图像匹配设置
        self.last_screenshot_hash = None
        self.static_counter = 0
        self.static_start_time = None  # 记录开始静止的时间
        
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
        """检测内容是否停止超过2分钟"""
        current_hash = self.calculate_image_hash(image)
        current_time = time.time()
        
        if self.last_screenshot_hash == current_hash:
            # 如果是第一次检测到停止，记录开始时间
            if self.static_start_time is None:
                self.static_start_time = current_time
                self.logger.info("⏸️ 开始检测停止状态...")
            
            self.static_counter += 1
            self.detection_stats['static_detections'] += 1
            
            # 计算已经停止的时间
            static_duration = current_time - self.static_start_time
            remaining_time = max(0, self.min_static_duration - static_duration)
            
            if remaining_time > 0:
                self.logger.info(f"⏱️ 停止时间: {static_duration:.1f}秒 / {self.min_static_duration}秒 (还需 {remaining_time:.1f}秒)")
            else:
                self.logger.info(f"✅ 停止时间: {static_duration:.1f}秒 (已超过2分钟)")
        else:
            if self.static_counter > 0:
                elapsed = current_time - self.static_start_time if self.static_start_time else 0
                self.logger.info(f"🔄 检测到变化，重置停止计时 (已停止 {elapsed:.1f}秒)")
            
            self.static_counter = 0
            self.static_start_time = None
            self.last_screenshot_hash = current_hash
            self.logger.debug("🖼️ 检测到图像变化")
        
        # 判断条件：达到停止阈值 AND 超过2分钟
        is_static_enough = self.static_counter >= self.static_threshold
        is_time_enough = (self.static_start_time is not None and 
                         current_time - self.static_start_time >= self.min_static_duration)
        
        is_truly_stopped = is_static_enough and is_time_enough
        
        if is_truly_stopped:
            static_duration = current_time - self.static_start_time
            self.logger.info(f"🛑 确认Copilot停止！已停止 {static_duration:.1f}秒")
        
        return is_truly_stopped
    
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
                
                is_cursor_active = bool(5 < activity_level < 100)
                
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
    
    def detect_stop_indicators(self, image: np.ndarray) -> bool:
        """检测明确的停止指示器"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 检测方法1: 查找停止按钮或完成指示器
            # 通常Copilot停止时会显示停止按钮或完成状态
            
            # 检测深色区域 (可能是停止按钮)
            dark_pixels = np.sum(gray < 50)
            total_pixels = gray.shape[0] * gray.shape[1]
            dark_ratio = dark_pixels / total_pixels
            
            # 检测边缘 (停止状态通常有清晰的边界)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / total_pixels
            
            # 检测文本区域的密度 (停止时文本通常更少)
            binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            text_density = np.sum(binary == 0) / total_pixels
            
            self.logger.debug(f"🛑 停止指示器检测:")
            self.logger.debug(f"   深色比例: {dark_ratio:.3f}")
            self.logger.debug(f"   边缘密度: {edge_density:.3f}")
            self.logger.debug(f"   文本密度: {text_density:.3f}")
            
            # 判断条件：深色区域较少，边缘清晰，文本密度适中
            is_stopped = (
                0.02 < dark_ratio < 0.15 and  # 深色区域不太多不太少
                edge_density > 0.01 and        # 有一定的边缘结构
                0.1 < text_density < 0.4       # 文本密度适中
            )
            
            if is_stopped:
                self.logger.info("🛑 检测到停止指示器特征")
            
            return is_stopped
            
        except Exception as e:
            self.logger.error(f"❌ 检测停止指示器时出错: {e}")
            return False
    
    def detect_completion_patterns(self, image: np.ndarray) -> bool:
        """检测完成模式 - 通过模板匹配"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 检测水平线条 (完成后常见的分隔线)
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
            
            # 检测垂直结构 (停止状态的侧边栏)
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 15))
            vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)
            
            # 统计线条数量
            horizontal_count = np.sum(horizontal_lines > 100)
            vertical_count = np.sum(vertical_lines > 100)
            
            self.logger.debug(f"📐 完成模式检测:")
            self.logger.debug(f"   水平线条: {horizontal_count}")
            self.logger.debug(f"   垂直线条: {vertical_count}")
            
            # 判断是否有完成的结构特征
            has_completion_pattern = bool(horizontal_count > 100 or vertical_count > 50)
            
            if has_completion_pattern:
                self.logger.info("📐 检测到完成模式特征")
            
            return has_completion_pattern
            
        except Exception as e:
            self.logger.error(f"❌ 检测完成模式时出错: {e}")
            return False
    
    def detect_interface_elements(self, image: np.ndarray) -> dict:
        """检测界面元素来判断状态"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape
            
            # 检测输入框区域 (通常在底部)
            input_region = gray[int(height * 0.8):, :]
            input_variance = float(np.var(input_region.astype(np.float64)))
            
            # 检测内容区域 (中部)
            content_region = gray[int(height * 0.2):int(height * 0.8), :]
            content_variance = float(np.var(content_region.astype(np.float64)))
            
            # 检测顶部区域 (标题栏)
            top_region = gray[:int(height * 0.2), :]
            top_variance = float(np.var(top_region.astype(np.float64)))
            
            elements = {
                'input_variance': input_variance,
                'content_variance': content_variance,
                'top_variance': top_variance,
                'has_input_focus': bool(input_variance > 100),
                'has_content': bool(content_variance > 50),
                'interface_stable': bool(top_variance < 200)
            }
            
            self.logger.debug(f"🎛️ 界面元素检测:")
            self.logger.debug(f"   输入区变化: {input_variance:.1f}")
            self.logger.debug(f"   内容区变化: {content_variance:.1f}")
            self.logger.debug(f"   顶部区变化: {top_variance:.1f}")
            self.logger.debug(f"   输入焦点: {elements['has_input_focus']}")
            self.logger.debug(f"   有内容: {elements['has_content']}")
            self.logger.debug(f"   界面稳定: {elements['interface_stable']}")
            
            return elements
            
        except Exception as e:
            self.logger.error(f"❌ 检测界面元素时出错: {e}")
            return {}

    def analyze_status_by_pixels(self, image: np.ndarray) -> str:
        """简化状态分析 - 只要停止超过30秒就判断为停止"""
        self.detection_stats['total_checks'] += 1
        
        self.logger.debug("🔍 开始状态分析...")
        
        # 主要检测：内容是否停止超过30秒
        is_truly_stopped = self.detect_static_content(image)
        
        # 辅助检测
        has_cursor_activity = self.detect_cursor_activity(image)
        has_loading_animation = self.detect_loading_animation(image)
        
        # 简化的状态判断逻辑
        if is_truly_stopped:
            # 停止超过30秒
            status = "stopped"
            self.logger.info("🛑 状态判断: STOPPED (停止超过30秒)")
        elif has_loading_animation:
            status = "thinking"
            self.logger.info("🤔 状态判断: THINKING (检测到加载动画)")
        elif has_cursor_activity:
            status = "waiting_input"
            self.logger.info("⌨️ 状态判断: WAITING_INPUT (检测到光标活动)")
        elif self.static_counter > 0:
            # 正在停止中，但还没到30秒
            status = "active"
            remaining_time = 0
            if self.static_start_time:
                elapsed = time.time() - self.static_start_time
                remaining_time = max(0, self.min_static_duration - elapsed)
            self.logger.info(f"🟡 状态判断: ACTIVE (停止中，还需 {remaining_time:.1f}秒到30秒)")
        else:
            status = "active"
            self.logger.info("🟢 状态判断: ACTIVE (内容变化中)")
        
        # 输出简化的检测结果
        self.logger.debug("📊 检测结果:")
        self.logger.debug(f"   停止超过30秒: {is_truly_stopped}")
        self.logger.debug(f"   停止计数: {self.static_counter}/{self.static_threshold}")
        self.logger.debug(f"   光标活动: {has_cursor_activity}")
        self.logger.debug(f"   加载动画: {has_loading_animation}")
        self.logger.debug(f"   最终状态: {status}")
        
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
    
    def find_chat_input_box(self, window: gw.Win32Window) -> Optional[Tuple[int, int]]:
        """智能查找Chat输入框位置"""
        try:
            self.logger.debug("🔍 智能查找Chat输入框位置")
            
            # 截取整个VS Code窗口
            screenshot = pyautogui.screenshot(region=(
                window.left, window.top, window.width, window.height
            ))
            image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 重点搜索右侧区域 (Chat通常在右侧)
            right_region_start = int(image.shape[1] * 0.6)  # 从60%宽度开始
            right_region = gray[:, right_region_start:]
            
            # 查找输入框的特征：
            # 1. 水平的长矩形区域
            # 2. 通常在底部
            # 3. 有明显的边界
            
            # 检测边缘
            edges = cv2.Canny(right_region, 50, 150)
            
            # 查找水平线条 (输入框的上下边界)
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            horizontal_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel)
            
            # 找到水平线的位置
            horizontal_coords = np.where(horizontal_lines > 0)
            
            if len(horizontal_coords[0]) > 0:
                # 找最底部的几条水平线 (输入框通常在底部)
                bottom_lines = []
                height = right_region.shape[0]
                
                # 只考虑底部30%的区域
                bottom_threshold = int(height * 0.7)
                
                for i in range(len(horizontal_coords[0])):
                    y = horizontal_coords[0][i]
                    x = horizontal_coords[1][i]
                    
                    if y > bottom_threshold:  # 在底部区域
                        bottom_lines.append((x, y))
                
                if bottom_lines:
                    # 找到最常见的y坐标 (输入框的边界)
                    y_coords = [line[1] for line in bottom_lines]
                    y_coords.sort()
                    
                    # 使用最底部的线作为输入框位置
                    input_y_relative = y_coords[-10] if len(y_coords) > 10 else y_coords[-1]
                    
                    # 输入框通常在Chat面板的中央
                    input_x_relative = right_region.shape[1] // 2
                    
                    # 转换为绝对坐标
                    input_x = window.left + right_region_start + input_x_relative
                    input_y = window.top + input_y_relative - 10  # 稍微向上偏移到输入框内部
                    
                    self.logger.info(f"✅ 智能检测到输入框位置: ({input_x}, {input_y})")
                    return (input_x, input_y)
            
            self.logger.debug("⚠️ 未能智能检测到输入框，使用默认位置")
            return None
            
        except Exception as e:
            self.logger.warning(f"❌ 智能查找输入框失败: {e}")
            return None
    
    def send_continue_command(self, window: gw.Win32Window) -> bool:
        """发送继续命令 - 增强版，确保真正发送成功"""
        try:
            self.logger.info("📤 准备发送命令...")
            
            # 确保窗口激活并等待
            self.logger.info("🎯 激活VS Code窗口")
            window.activate()
            time.sleep(0.5)  # 增加等待时间
            
            # 方法1: 尝试直接在当前位置发送continue
            self.logger.info("🎯 方法1: 尝试在当前位置发送continue")
            success = self._try_send_continue_direct()
            if success:
                return True
            
            # 方法2: 尝试通过快捷键打开Chat并发送
            self.logger.info("🎯 方法2: 通过快捷键打开Chat")
            success = self._try_send_via_shortcuts()
            if success:
                return True
            
            # 方法3: 通过命令面板打开Chat
            self.logger.info("🎯 方法3: 通过命令面板打开Chat")
            success = self._try_send_via_command_palette()
            if success:
                return True
            
            self.logger.error("❌ 所有发送方法都失败了")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 发送命令时出错: {e}")
            return False
    
    def _try_send_continue_direct(self) -> bool:
        """尝试直接发送continue命令"""
        try:
            self.logger.debug("📝 直接输入continue命令")
            
            # 获取窗口信息用于计算点击位置
            vscode_window = self.find_vscode_window()
            if vscode_window:
                # 首先尝试智能查找输入框
                smart_position = self.find_chat_input_box(vscode_window)
                
                if smart_position:
                    input_x, input_y = smart_position
                    self.logger.info(f"🎯 使用智能检测位置: ({input_x}, {input_y})")
                else:
                    # 备用方案：使用计算的位置
                    # Chat面板通常占右侧40%的宽度
                    chat_panel_left = vscode_window.left + int(vscode_window.width * 0.6)
                    chat_panel_width = int(vscode_window.width * 0.4)
                    
                    # 输入框在Chat面板的最底部，但要避开滚动条
                    input_x = chat_panel_left + int(chat_panel_width * 0.5)  # Chat面板中心
                    input_y = vscode_window.top + vscode_window.height - 80  # 距离底部80像素，更保守
                    
                    self.logger.info(f"🖱️ 使用计算位置: ({input_x}, {input_y})")
                
                self.logger.debug(f"   窗口范围: ({vscode_window.left}, {vscode_window.top}) - ({vscode_window.left + vscode_window.width}, {vscode_window.top + vscode_window.height})")
                
                # 多次点击确保焦点正确
                pyautogui.click(input_x, input_y)
                time.sleep(0.2)
                pyautogui.click(input_x, input_y)  # 双击确保焦点
                time.sleep(0.3)
                
                # 额外尝试：按Tab键导航到输入框 (如果点击位置不对)
                pyautogui.press('tab')
                time.sleep(0.1)
                pyautogui.press('tab')
                time.sleep(0.1)
                
            else:
                self.logger.warning("⚠️ 无法获取窗口信息，尝试直接输入")
            
            # 清空可能存在的内容
            pyautogui.hotkey('ctrl', 'a')  # 全选
            time.sleep(0.1)
            
            # 输入continue命令
            pyautogui.write(self.continue_command, interval=0.05)
            time.sleep(0.5)
            
            # 按回车发送
            pyautogui.press('enter')
            time.sleep(0.3)
            
            self.logger.info("✅ 直接发送continue命令完成")
            self.last_action_time = time.time()
            self.detection_stats['commands_sent'] += 1
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ 直接发送失败: {e}")
            return False
    
    def _try_send_via_shortcuts(self) -> bool:
        """通过快捷键打开Chat并发送"""
        shortcuts = [
            ('ctrl', 'shift', 'i'),  # Copilot Chat
            ('ctrl', 'i'),           # 另一个可能的快捷键
        ]
        
        for i, shortcut in enumerate(shortcuts):
            try:
                self.logger.info(f"🔑 尝试快捷键 {i+1}: {'+'.join(shortcut)}")
                
                # 按快捷键
                pyautogui.hotkey(*shortcut)
                time.sleep(1.0)  # 等待Chat窗口打开
                
                # 发送新窗口消息 (因为不确定现有窗口状态)
                self.logger.info(f"📝 发送消息: '{self.new_window_message}'")
                pyautogui.write(self.new_window_message, interval=0.05)
                time.sleep(0.5)
                pyautogui.press('enter')
                time.sleep(0.3)
                
                self.logger.info(f"✅ 快捷键方法 {i+1} 发送成功")
                self.last_action_time = time.time()
                self.detection_stats['commands_sent'] += 1
                self.detection_stats['new_windows_opened'] += 1
                return True
                
            except Exception as e:
                self.logger.warning(f"❌ 快捷键方法 {i+1} 失败: {e}")
                if i < len(shortcuts) - 1:
                    time.sleep(0.5)
                    continue
        
        return False
    
    def _try_send_via_command_palette(self) -> bool:
        """通过命令面板打开Chat并发送"""
        try:
            self.logger.info("📋 打开命令面板")
            
            # 打开命令面板
            pyautogui.hotkey('ctrl', 'shift', 'p')
            time.sleep(0.8)
            
            # 搜索Copilot Chat命令
            chat_commands = [
                'Copilot Chat: Focus on Copilot Chat View',
                'Chat: Focus on Chat View',
                'Copilot: Open Chat'
            ]
            
            for i, command in enumerate(chat_commands):
                try:
                    self.logger.debug(f"🔍 尝试命令: {command}")
                    
                    # 清空命令面板并输入命令
                    pyautogui.hotkey('ctrl', 'a')
                    pyautogui.write(command, interval=0.03)
                    time.sleep(0.5)
                    pyautogui.press('enter')
                    time.sleep(1.2)  # 等待Chat窗口打开
                    
                    # 发送消息
                    self.logger.info(f"📝 发送消息: '{self.new_window_message}'")
                    pyautogui.write(self.new_window_message, interval=0.05)
                    time.sleep(0.5)
                    pyautogui.press('enter')
                    time.sleep(0.3)
                    
                    self.logger.info(f"✅ 命令面板方法发送成功 (命令: {command})")
                    self.last_action_time = time.time()
                    self.detection_stats['commands_sent'] += 1
                    self.detection_stats['new_windows_opened'] += 1
                    return True
                    
                except Exception as e:
                    self.logger.warning(f"❌ 命令 {i+1} 失败: {e}")
                    if i < len(chat_commands) - 1:
                        # 重新打开命令面板
                        pyautogui.press('escape')  # 关闭当前面板
                        time.sleep(0.3)
                        pyautogui.hotkey('ctrl', 'shift', 'p')
                        time.sleep(0.5)
                        continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 命令面板方法失败: {e}")
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
                
                # 检测：如果停止超过30秒且超过冷却时间
                if status == "stopped" and time_since_last_action > self.cooldown_time:
                    self.logger.info(f"🎯 Copilot已停止超过30秒！")
                    if self.send_continue_command(window):
                        self.logger.info("✅ 命令发送成功")
                        self.static_counter = 0
                        self.static_start_time = None  # 重置停止开始时间
                        self.last_screenshot_hash = None
                        self.print_stats()
                    else:
                        self.logger.error("❌ 命令发送失败")
                elif status == "stopped":
                    remaining_time = self.cooldown_time - time_since_last_action
                    self.logger.info(f"⏳ Copilot已停止，但仍在冷却期 (剩余: {remaining_time:.1f}秒)")
                elif self.static_counter > 0:
                    # 显示停止进度
                    elapsed = time.time() - self.static_start_time if self.static_start_time else 0
                    remaining = max(0, self.min_static_duration - elapsed)
                    self.logger.info(f"⏱️ 停止进度: {elapsed:.1f}/{self.min_static_duration}秒 (还需 {remaining:.1f}秒)")
                
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
        print("🚀 Copilot监控工具启动 (30秒停止检测)")
        print(f"⚡ 每 {self.check_interval} 秒检测一次")
        print(f"⚡ 停止判断: 连续停止 {self.min_static_duration} 秒")
        print(f"⚡ 检测阈值: {self.static_threshold} 次 (约 {self.static_threshold * self.check_interval} 秒)")
        print(f"⚡ 冷却时间: {self.cooldown_time} 秒")
        print(f"📝 新窗口消息: '{self.new_window_message}'")
        print("🎯 逻辑: 只要停止超过30秒，就发送继续命令")
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
    print("🚀 VS Code Copilot Chat 监控工具")
    print("🎯 核心逻辑: 只要停止超过30秒，就认为Copilot停止了")
    print("=" * 50)
    print("⚡ 检测设置：")
    print("   • 检测间隔: 5秒")
    print("   • 停止判断: 连续停止30秒")
    print("   • 检测阈值: 3次 (15秒后开始计时)")
    print("   • 冷却时间: 30秒")
    print()
    print("🎯 工作原理：")
    print("   • 每5秒截图检测Copilot Chat区域")
    print("   • 连续3次相同画面后开始计时")
    print("   • 停止超过30秒自动发送继续命令")
    print("   • 如有变化立即重新开始计时")
    print()
    print("📝 自动操作：")
    print("   • 优先使用现有Chat窗口发送'continue'")
    print("   • 如失败则打开新窗口发送'按照指令修改代码'")
    print("   • 详细日志显示停止进度和剩余时间")
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
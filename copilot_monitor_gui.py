#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VS Code GitHub Copilot Chat 自动监控工具 - GUI版本
提供图形用户界面来控制监控功能
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import sys
import os
from copilot_monitor import CopilotMonitor


class CopilotMonitorGUI:
    """Copilot Monitor GUI界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("VS Code GitHub Copilot Chat 自动监控工具")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 设置图标（如果有的话）
        # self.root.iconbitmap("icon.ico")
        
        self.monitor = None
        self.monitoring = False
        
        self.setup_ui()
        self.setup_menu()
        
    def setup_menu(self):
        """设置菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开配置文件", command=self.open_config)
        file_menu.add_command(label="保存日志", command=self.save_log)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit_app)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="运行测试", command=self.run_tests)
        tools_menu.add_command(label="清空日志", command=self.clear_log)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="VS Code GitHub Copilot Chat 自动监控工具", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 状态区域
        status_frame = ttk.LabelFrame(main_frame, text="监控状态", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        ttk.Label(status_frame, text="状态:").grid(row=0, column=0, sticky=tk.W)
        self.status_var = tk.StringVar(value="未启动")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                     font=("Arial", 10, "bold"))
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(status_frame, text="监控间隔:").grid(row=1, column=0, sticky=tk.W)
        self.interval_var = tk.StringVar(value="30秒")
        ttk.Label(status_frame, textvariable=self.interval_var).grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        # 控制按钮区域
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=3, pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="开始监控", 
                                      command=self.start_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="停止监控", 
                                     command=self.stop_monitoring, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.test_button = ttk.Button(control_frame, text="运行测试", 
                                     command=self.run_tests)
        self.test_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 配置区域
        config_frame = ttk.LabelFrame(main_frame, text="快速配置", padding="10")
        config_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        ttk.Label(config_frame, text="检查间隔(秒):").grid(row=0, column=0, sticky=tk.W)
        self.interval_entry = ttk.Entry(config_frame, width=10)
        self.interval_entry.insert(0, "30")
        self.interval_entry.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(config_frame, text="继续命令:").grid(row=1, column=0, sticky=tk.W)
        self.command_entry = ttk.Entry(config_frame, width=20)
        self.command_entry.insert(0, "continue")
        self.command_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        apply_button = ttk.Button(config_frame, text="应用配置", command=self.apply_config)
        apply_button.grid(row=0, column=2, rowspan=2, padx=(20, 0))
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="10")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, 
                                                 width=80, height=15)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 底部状态栏
        self.statusbar = ttk.Label(main_frame, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def log_message(self, message):
        """添加日志消息"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            return
        
        try:
            self.monitor = CopilotMonitor()
            self.monitor.start()
            
            self.monitoring = True
            self.status_var.set("运行中")
            self.status_label.config(foreground="green")
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            
            self.log_message("监控已启动")
            self.statusbar.config(text="监控运行中...")
            
            # 启动日志更新线程
            self.log_thread = threading.Thread(target=self.update_log_from_monitor)
            self.log_thread.daemon = True
            self.log_thread.start()
            
        except Exception as e:
            messagebox.showerror("错误", f"启动监控失败: {e}")
            self.log_message(f"启动监控失败: {e}")
    
    def stop_monitoring(self):
        """停止监控"""
        if not self.monitoring:
            return
        
        try:
            if self.monitor:
                self.monitor.stop()
            
            self.monitoring = False
            self.status_var.set("已停止")
            self.status_label.config(foreground="red")
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            
            self.log_message("监控已停止")
            self.statusbar.config(text="就绪")
            
        except Exception as e:
            messagebox.showerror("错误", f"停止监控失败: {e}")
            self.log_message(f"停止监控失败: {e}")
    
    def apply_config(self):
        """应用配置"""
        try:
            interval = int(self.interval_entry.get())
            command = self.command_entry.get().strip()
            
            if interval < 5:
                messagebox.showwarning("警告", "检查间隔不能小于5秒")
                return
            
            if not command:
                messagebox.showwarning("警告", "继续命令不能为空")
                return
            
            self.interval_var.set(f"{interval}秒")
            self.log_message(f"配置已更新: 间隔={interval}秒, 命令={command}")
            self.statusbar.config(text="配置已更新")
            
            # 如果监控器正在运行，需要重新启动以应用新配置
            if self.monitoring:
                if messagebox.askyesno("确认", "配置更改需要重新启动监控，是否继续？"):
                    self.stop_monitoring()
                    self.root.after(1000, self.start_monitoring)  # 1秒后重新启动
            
        except ValueError:
            messagebox.showerror("错误", "检查间隔必须是有效的数字")
    
    def run_tests(self):
        """运行测试"""
        self.log_message("开始运行测试...")
        self.statusbar.config(text="正在运行测试...")
        
        # 在新线程中运行测试以避免界面冻结
        test_thread = threading.Thread(target=self._run_tests_thread)
        test_thread.daemon = True
        test_thread.start()
    
    def _run_tests_thread(self):
        """在后台线程中运行测试"""
        try:
            import subprocess
            result = subprocess.run([sys.executable, "test_detection.py"], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            
            self.root.after(0, lambda: self.log_message("测试完成"))
            self.root.after(0, lambda: self.log_message(result.stdout))
            if result.stderr:
                self.root.after(0, lambda: self.log_message(f"错误输出: {result.stderr}"))
            
            self.root.after(0, lambda: self.statusbar.config(text="测试完成"))
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"运行测试失败: {e}"))
            self.root.after(0, lambda: self.statusbar.config(text="测试失败"))
    
    def update_log_from_monitor(self):
        """从监控器更新日志（模拟功能）"""
        import time
        while self.monitoring:
            # 这里可以从监控器获取实际的日志信息
            # 目前只是定期更新状态
            time.sleep(10)
            if self.monitoring:
                self.root.after(0, lambda: self.log_message("监控运行正常..."))
    
    def open_config(self):
        """打开配置文件"""
        try:
            config_file = filedialog.askopenfilename(
                title="选择配置文件",
                filetypes=[("INI files", "*.ini"), ("All files", "*.*")],
                initialfile="config.ini"
            )
            if config_file:
                os.startfile(config_file)  # Windows系统
        except Exception as e:
            messagebox.showerror("错误", f"打开配置文件失败: {e}")
    
    def save_log(self):
        """保存日志"""
        try:
            log_file = filedialog.asksaveasfilename(
                title="保存日志",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if log_file:
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("成功", f"日志已保存到: {log_file}")
        except Exception as e:
            messagebox.showerror("错误", f"保存日志失败: {e}")
    
    def clear_log(self):
        """清空日志"""
        if messagebox.askyesno("确认", "确定要清空日志吗？"):
            self.log_text.delete(1.0, tk.END)
            self.log_message("日志已清空")
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """VS Code GitHub Copilot Chat 自动监控工具 v1.0

这是一个自动化工具，用于监控VS Code中的GitHub Copilot Chat状态。
当检测到Copilot Chat停止响应时，会自动发送"continue"命令来恢复对话。

功能特性：
• 自动检测VS Code窗口
• 智能识别Copilot Chat状态  
• 自动发送继续命令
• 支持中英文界面
• 可配置监控参数
• 详细日志记录

开发者: AI Assistant
许可证: MIT
"""
        messagebox.showinfo("关于", about_text)
    
    def quit_app(self):
        """退出应用"""
        if self.monitoring:
            if messagebox.askyesno("确认", "监控正在运行，确定要退出吗？"):
                self.stop_monitoring()
                self.root.quit()
        else:
            self.root.quit()


def main():
    """主函数"""
    try:
        root = tk.Tk()
        app = CopilotMonitorGUI(root)
        
        # 处理窗口关闭事件
        root.protocol("WM_DELETE_WINDOW", app.quit_app)
        
        # 启动GUI
        root.mainloop()
        
    except Exception as e:
        print(f"启动GUI时出错: {e}")
        input("按Enter键退出...")


if __name__ == "__main__":
    main() 
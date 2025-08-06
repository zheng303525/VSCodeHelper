# 📦 Tesseract OCR 安装指南

## 🎯 问题诊断结果

您的监控工具不工作的主要原因是：**Tesseract OCR 未安装**

该工具依赖 Tesseract OCR 来识别屏幕上的文本，没有它就无法检测 Copilot Chat 的状态。

## 🚀 安装 Tesseract OCR (Windows)

### 方法一：官方安装程序（推荐）

1. **下载最新版本**
   - 访问：https://github.com/UB-Mannheim/tesseract/wiki
   - 下载：`tesseract-ocr-w64-setup-5.5.0.20241111.exe` (64位)
   - 或直接点击：[下载链接](https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.5.0.20241111.exe)

2. **安装步骤**
   ```
   1. 以管理员身份运行安装程序
   2. 选择安装路径（建议默认：C:\Program Files\Tesseract-OCR）
   3. 在组件选择中，确保勾选：
      - Tesseract-OCR 
      - Additional Language Data (包含中文支持)
      - Development Libraries (可选)
   4. 完成安装
   ```

3. **配置环境变量**
   ```
   1. 右键"此电脑" → 属性 → 高级系统设置 → 环境变量
   2. 在"系统变量"中找到"Path"，点击编辑
   3. 添加：C:\Program Files\Tesseract-OCR
   4. 确定保存
   ```

### 方法二：使用包管理器

**使用 Chocolatey：**
```powershell
# 安装 Chocolatey (如果未安装)
Set-ExecutionPolicy Bypass -Scope Process -Force; 
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; 
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 安装 Tesseract
choco install tesseract
```

**使用 Winget：**
```powershell
winget install UB-Mannheim.TesseractOCR
```

## 🔧 配置 Python 环境

安装完 Tesseract 后，配置 Python 环境：

```bash
# 如果需要指定 Tesseract 路径
pip install pytesseract
```

在代码中设置路径（如果需要）：
```python
import pytesseract
# 设置 Tesseract 路径（如果环境变量配置失败）
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## ✅ 验证安装

1. **命令行验证**
   ```bash
   tesseract --version
   ```
   应该显示版本信息

2. **Python验证**
   ```python
   import pytesseract
   print(pytesseract.get_tesseract_version())
   ```

3. **运行诊断工具**
   ```bash
   python debug_tool.py
   ```

## 🔍 常见问题解决

### 问题1：Path not found
**解决方案：**
- 重新配置环境变量
- 重启命令行/PowerShell
- 使用完整路径

### 问题2：权限问题
**解决方案：**
- 以管理员身份运行安装程序
- 检查防火墙/杀毒软件设置

### 问题3：中文识别不准确
**解决方案：**
- 确保安装了中文语言包
- 下载额外的中文训练数据：
  ```bash
  # 从 https://github.com/tesseract-ocr/tessdata 下载
  # chi_sim.traineddata (简体中文)
  # chi_tra.traineddata (繁体中文)
  ```

## 🎯 安装完成后的测试

安装完成后，重新运行监控工具：

1. **运行诊断**
   ```bash
   python debug_tool.py
   ```

2. **测试基本监控**
   ```bash
   python test_detection.py
   ```

3. **启动完整监控**
   ```bash
   python start.py
   ```

## 📝 工具工作原理说明

安装 Tesseract OCR 后，监控工具的工作流程：

1. **窗口检测** → 查找 VS Code 窗口
2. **区域截图** → 截取聊天面板区域（假设在右半部分）
3. **OCR识别** → 使用 Tesseract 识别文本内容
4. **状态分析** → 检查关键词判断是否停止
5. **自动操作** → 发送 "continue" 命令

## ⚠️ 重要提示

1. **位置假设**：工具假设 Copilot Chat 面板在 VS Code 右侧
2. **精确度**：OCR 识别受字体大小、对比度影响
3. **语言支持**：需要对应的语言训练数据
4. **权限要求**：可能需要管理员权限进行自动化操作

## 🔧 进一步优化建议

1. **调整配置文件** (`config.ini`)
   - 修改检测关键词
   - 调整监控间隔
   - 设置输入框位置

2. **改善识别准确性**
   - 提高显示器分辨率
   - 使用较大字体
   - 确保足够对比度

3. **测试和调试**
   - 使用 `debug_tool.py` 生成截图
   - 检查 OCR 识别结果
   - 调整监控参数

安装完成后，您的 VS Code Copilot Chat 监控工具应该能够正常工作了！🎉 
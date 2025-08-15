# QApplication 崩溃问题解决方案

## 🐛 问题描述
当用户在状态栏菜单中点击 "Start Recording" 时，应用崩溃并显示错误：
```
QWidget: Must construct a QApplication before a QWidget
[1] 26757 abort python src/main.py
```

## 🔍 问题根因
- **PyQt6 要求**: 在创建任何 QWidget（如 FloatingWindow）之前，必须先有一个 QApplication 实例
- **rumps 环境**: rumps 状bar应用在自己的事件循环中运行，没有提供 QApplication 上下文
- **时机问题**: FloatingWindow 是在用户点击录音时才创建的，此时缺少必要的 Qt 应用上下文

## ✅ 解决方案

### 1. 修改 `ensure_qt_application()` 函数
```python
def ensure_qt_application():
    """Ensure QApplication is running."""
    global _qt_app
    
    if _qt_app is None:
        # Check if there's already a QApplication instance
        existing_app = QApplication.instance()
        if existing_app:
            _qt_app = existing_app
        else:
            # Create new QApplication
            _qt_app = QApplication(sys.argv)
    
    return _qt_app
```

### 2. 修改 FloatingWindow 初始化
```python
def __init__(self, ui_config: Dict[str, Any]):
    # Ensure QApplication exists before creating QWidget
    ensure_qt_application()
    
    super().__init__()
    # ... rest of initialization
```

### 3. 增强错误处理
在 `menu_bar.py` 中为 FloatingWindow 创建增加了错误处理：
```python
try:
    self.floating_window = FloatingWindow(self.config['ui'])
    self.logger.info("FloatingWindow created successfully")
except Exception as e:
    self.logger.error(f"Failed to create FloatingWindow: {e}", exc_info=True)
    rumps.alert("UI Error", f"Failed to create voice input window: {str(e)}")
    self.is_recording = False
    return
```

## 🧪 测试验证
创建了两个测试脚本验证修复：

1. **test_floating_window.py** - 独立测试 FloatingWindow 创建
2. **test_recording.py** - 测试完整录音工作流程

所有测试均通过 ✅

## 📋 关键学习点
1. **Qt 应用生命周期**: PyQt6 需要 QApplication 作为所有 GUI 组件的基础
2. **框架集成**: 不同 GUI 框架（rumps + PyQt6）需要小心处理上下文
3. **延迟初始化**: 需要在实际使用前确保依赖项存在
4. **错误处理**: GUI 创建失败时提供友好的用户反馈

## 🎯 最终状态
- ✅ 应用正常启动
- ✅ 状态栏菜单正常工作  
- ✅ "Start Recording" 按钮不再崩溃
- ✅ FloatingWindow 正确创建和显示
- ✅ 完整录音工作流程正常

**问题已完全解决！** 🎉
# Healthy Diet Tracker (PyQt5)

轻量级个人健康饮食记录系统，突出清新草绿色主题与极简交互体验。

## 核心特性

- 登录校验（账号 `admin` / 密码 `123456`）与错误提示。
- 主界面遵循菜单栏 + 工具栏 + 表格 + 状态栏结构，提供菜单和醒目按钮两条交互路径。
- 记录使用模态对话框录入/编辑，含必填校验与非数字热量提示。
- 数据存储于本地 `data.json`，随操作自动读写，便于实验验收演示。
- 全局 QSS 强调草绿色渐变、圆角卡片与 hover 微交互。

## 运行方式

```powershell
D:/Py_project/.venv/Scripts/python.exe d:/Py_project/Human-computer/exp2/sts1.py
```

首次运行后在同目录生成 `data.json`。如遇图形界面未显示，请确认已安装 PyQt5（`pip install PyQt5`）。

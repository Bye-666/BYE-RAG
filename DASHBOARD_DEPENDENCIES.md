# Dashboard 依赖说明

## 必需依赖

Dashboard 运行需要以下**必需**依赖：

```bash
pip install streamlit pandas
```

- **streamlit** - Web 应用框架
- **pandas** - 数据处理和表格展示

## 可选依赖

以下依赖是**可选**的，不安装也可以运行 Dashboard，但会影响部分功能：

### 1. Plotly (推荐)

```bash
pip install plotly
```

**作用**: 提供交互式图表

**影响页面**:
- Query 追踪 - 查询耗时趋势图
- Ingestion 追踪 - 摄取耗时趋势图

**未安装时**: 使用 Streamlit 内置的简单折线图，功能正常但交互性较差

### 2. PyMilvus (核心功能必需)

```bash
pip install pymilvus
```

**作用**: 向量数据库客户端

**影响页面**:
- 数据浏览器 - 无法连接向量库
- Ingestion 管理 - 无法摄取文档
- 系统设置 - 无法检测向量库状态

**未安装时**: Dashboard 可以启动，但上述页面会显示错误提示

### 3. 其他 RAG 组件依赖

这些是 RAG 系统本身的依赖，Dashboard 间接依赖：

```bash
# PDF 处理
pip install pypdf

# Embedding 和 LLM
pip install dashscope  # 或其他提供商的 SDK

# 其他
pip install pyyaml
```

**未安装时**: 相关功能无法使用，Dashboard 会显示错误

---

## 完整安装（推荐）

安装所有依赖（假设项目有 requirements.txt）：

```bash
pip install -r requirements.txt
```

或手动安装核心依赖：

```bash
# Dashboard 核心
pip install streamlit pandas plotly

# RAG 系统核心
pip install pymilvus pypdf dashscope pyyaml

# 其他
pip install python-dotenv
```

---

## 依赖检查

Dashboard 启动时会自动检查依赖：

1. **必需依赖缺失** - 无法启动，显示错误
2. **可选依赖缺失** - 可以启动，相关功能降级或显示提示

可以运行验证脚本检查：

```bash
python scripts/verify_fixes.py
```

---

## 故障排查

### Dashboard 无法启动

**错误**: `ModuleNotFoundError: No module named 'streamlit'`

**解决**:
```bash
pip install streamlit
```

### 图表不显示

**原因**: plotly 未安装

**解决**:
```bash
pip install plotly
```

或接受使用简单图表

### 向量库连接失败

**错误**: `ImportError: pymilvus 包未安装`

**解决**:
```bash
pip install pymilvus
```

### 文档摄取失败

**原因**: 缺少 PDF 处理或 Embedding 依赖

**解决**:
```bash
pip install pypdf dashscope
```

---

## 依赖版本要求

```
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.17.0  # 可选
pymilvus>=2.4.0
pypdf>=3.0.0
pyyaml>=6.0
```

具体版本要求请参考 `requirements.txt`

---

## 开发环境建议

使用虚拟环境隔离依赖：

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

---

## 最小化依赖安装

如果只想体验 Dashboard（不使用实际 RAG 功能）：

```bash
pip install streamlit pandas
```

然后启动 Dashboard，可以查看界面，但大部分功能会显示"依赖未安装"的提示。

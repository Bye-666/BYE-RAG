# Dashboard 使用说明

## 启动 Dashboard

```bash
# 方式 1: 使用启动脚本
python scripts/run_dashboard.py

# 方式 2: 直接运行 streamlit
streamlit run src/dashboard/streamlit_app.py
```

浏览器将自动打开: http://localhost:8501

---

## 页面功能

### 1. 主页 - 系统总览
- 查看系统状态（向量存储、LLM、Embedding）
- 查看快速统计（查询、摄取次数）
- 查看系统配置

### 2. 📚 数据浏览器
- 浏览向量库中的文档
- 查看文档详情和数据块
- 快速搜索功能

**使用步骤**:
1. 查看集合统计
2. 选择文档查看详情
3. 使用快速搜索测试检索

### 3. 📥 Ingestion 管理
- 上传 PDF 文档
- 执行摄取流程
- 查看摄取记录

**使用步骤**:
1. 点击 "选择 PDF 文件" 上传文档
2. 配置选项（Transform、批处理大小）
3. 点击 "开始摄取"
4. 查看进度和结果

### 4. 🔍 Query 追踪
- 实时查询测试
- 查看执行追踪
- 分析查询性能

**使用步骤**:
1. 输入查询文本
2. 配置选项（返回结果数、重排序、追踪）
3. 点击 "执行查询"
4. 查看结果和追踪详情

### 5. 📊 Ingestion 追踪
- 查看摄取统计
- 分析性能趋势
- 查看详细记录

### 6. 📝 评估面板
- 查看基础指标
- Golden Test Set（待 Ragas 集成）
- 评估历史（待开发）

### 7. ⚙️ 系统设置
- 查看系统配置
- 测试组件连接
- 数据管理（清除追踪、重置 BM25）
- 查看日志

---

## 典型工作流程

### 流程 1: 首次使用
1. 启动 Dashboard
2. 进入 **Ingestion 管理** 上传 PDF 文档
3. 等待摄取完成
4. 进入 **Query 追踪** 测试查询
5. 进入 **数据浏览器** 查看数据

### 流程 2: 性能分析
1. 进入 **Query 追踪** 执行多次查询
2. 查看耗时趋势图
3. 进入 **Ingestion 追踪** 查看摄取性能
4. 分析瓶颈

### 流程 3: 问题排查
1. 进入 **系统设置** 检查组件状态
2. 查看日志文件
3. 检查配置
4. 进入相关追踪页面查看详情

---

## 故障排除

### Dashboard 无法启动
```bash
# 检查 streamlit 是否安装
pip install streamlit

# 检查依赖
pip install plotly pandas
```

### 配置文件未找到
确保 `config/settings.yaml` 存在：
```bash
ls config/settings.yaml
```

### 向量存储连接失败
检查 Milvus 配置：
```yaml
milvus:
  uri: milvus.db  # 本地文件模式
  collection_name: rag_knowledge_hub
  dense_dim: 2048
```

### BM25 编码器未训练
进入 **Ingestion 管理** 页面，上传并摄取至少一个文档。

---

## 注意事项

1. **首次使用**: 需要先摄取文档才能进行查询
2. **配置修改**: 修改 `config/settings.yaml` 后需要重启 Dashboard
3. **数据清理**: 在 **系统设置** 页面进行，操作不可逆
4. **性能**: 大量数据时，某些操作可能较慢

---

## 开发提示

### 添加新页面
1. 在 `src/dashboard/pages/` 创建新文件
2. 文件名格式: `{序号}_{图标}_{名称}.py`
3. Streamlit 自动识别并添加到侧边栏

### 修改配置访问
所有配置使用 `config.get("key.subkey", default)` 方式访问

### 添加新图表
使用 Plotly Express:
```python
import plotly.express as px

fig = px.line(df, x="x", y="y", title="标题")
st.plotly_chart(fig, use_container_width=True)
```

---

## 未来增强

- [ ] 实时更新（WebSocket）
- [ ] 用户认证
- [ ] 更多可视化图表
- [ ] Ragas 评估集成
- [ ] 导出报告功能
- [ ] 批量操作

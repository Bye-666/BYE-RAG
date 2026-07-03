"""Evaluation Panel Page - RAG system evaluation."""

import streamlit as st
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.session_init import init_session_state

st.set_page_config(page_title="评估面板", page_icon="📝", layout="wide")

# Initialize session state
init_session_state()

st.title("📝 评估面板")
st.markdown("RAG 系统质量评估")

st.markdown("---")

st.info("⚠️ 完整的评估功能需要集成 Ragas 框架（阶段 H），当前为简化版本")

st.markdown("---")

# Basic evaluation metrics
st.subheader("📊 基础指标")

col1, col2, col3 = st.columns(3)

query_traces = st.session_state.trace_recorder.get_traces(trace_type="query")
ingestion_traces = st.session_state.trace_recorder.get_traces(trace_type="ingestion")

with col1:
    st.metric("总查询次数", len(query_traces))

with col2:
    if query_traces:
        durations = [t.get('duration_ms', 0) for t in query_traces if t.get('duration_ms')]
        avg_latency = sum(durations) / len(durations) if durations else 0
        st.metric("平均查询延迟", f"{avg_latency:.2f} ms")
    else:
        st.metric("平均查询延迟", "N/A")

with col3:
    if ingestion_traces:
        success = sum(1 for t in ingestion_traces if t.get('error') is None)
        success_rate = success / len(ingestion_traces) * 100
        st.metric("摄取成功率", f"{success_rate:.1f}%")
    else:
        st.metric("摄取成功率", "N/A")

st.markdown("---")

# Manual evaluation
st.subheader("✍️ 手动评估")

st.markdown("""
使用此工具手动评估查询结果的质量。

**评估维度**:
- **相关性**: 结果是否与查询相关
- **准确性**: 信息是否准确
- **完整性**: 是否包含必要信息
""")

# Query input
eval_query = st.text_input("输入测试查询", placeholder="例如: 什么是机器学习？")

if eval_query and st.button("执行查询"):
    st.info("查询功能请使用 Query 追踪页面")

st.markdown("---")

# Golden test set
st.subheader("🎯 Golden Test Set")

st.markdown("""
Golden Test Set 是预定义的测试查询集合，用于回归测试。

**状态**: 📋 未配置

要配置 Golden Test Set:
1. 创建 `data/test/test_golden.json` 文件
2. 定义测试查询和期望结果
3. 运行评估
""")

golden_test_path = Path("data/test/test_golden.json")

if golden_test_path.exists():
    st.success("✅ Golden Test Set 已配置")

    with open(golden_test_path) as f:
        import json
        golden_data = json.load(f)

    st.write(f"**测试用例数**: {len(golden_data.get('test_cases', []))}")

    if st.button("运行 Golden Test"):
        st.info("Golden Test 执行功能开发中...")
else:
    st.warning("⚠️ Golden Test Set 未找到")

st.markdown("---")

# Ragas integration status
st.subheader("🔧 Ragas 集成状态")

st.markdown("""
**Ragas** 是专业的 RAG 评估框架，支持以下指标:

- **Faithfulness**: 答案的忠实度
- **Answer Relevancy**: 答案相关性
- **Context Precision**: 上下文精确度
- **Context Recall**: 上下文召回率

**当前状态**: ❌ 未集成

**集成计划**: 阶段 H - Evaluation
""")

try:
    import ragas
    st.success("✅ Ragas 库已安装")
    st.code(f"Ragas 版本: {ragas.__version__}")
except ImportError:
    st.error("❌ Ragas 库未安装")
    st.code("pip install ragas")

st.markdown("---")

# Evaluation history
st.subheader("📜 评估历史")

st.info("评估历史记录将在 Ragas 集成后可用")

st.markdown("""
评估历史将包含:
- 评估时间
- 测试用例数量
- 各项指标得分
- 详细报告
""")

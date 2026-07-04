"""Data Browser Page - Browse documents and chunks in vector store."""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.session_init import init_session_state

st.set_page_config(page_title="数据浏览器", page_icon="📚", layout="wide")

# Initialize session state
init_session_state()

st.title("📚 数据浏览器")
st.markdown("浏览向量库中的文档和数据块")

# Get vector store with error handling
try:
    vector_store = st.session_state.component_loader.get_vector_store()
except Exception as e:
    st.error(f"⚠️ 无法连接向量存储: {str(e)}")
    st.info("请确保已安装所有依赖：pip install -r requirements.txt")
    st.stop()

st.markdown("---")

# Collection stats
st.subheader("📊 集合统计")

try:
    stats = vector_store.get_collection_stats()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("总数据块", stats.get("row_count", 0))

    with col2:
        st.metric("集合名称", st.session_state.config.get("milvus.collection_name", "rag_knowledge_hub"))

    with col3:
        st.metric("向量维度", f"{st.session_state.config.get('milvus.dense_dim', 2048)}D")

except Exception as e:
    st.error(f"获取统计信息失败: {str(e)}")

st.markdown("---")

# Document listing
st.subheader("📄 文档列表")

try:
    # Query sample documents (不传 output_fields 以获取所有字段包括动态字段)
    sample_results = vector_store.query(
        expr="",  # 查询所有记录
        limit=100
    )

    if sample_results and len(sample_results) > 0:
        # Extract unique documents from metadata
        docs = {}
        for result in sample_results:
            doc_id = result.get("metadata", {}).get("doc_id")
            if doc_id and doc_id not in docs:
                metadata = result.get("metadata", {})
                docs[doc_id] = {
                    "文档ID": doc_id,
                    "文件名": metadata.get("filename", "未知"),
                    "数据块数": 1
                }
            elif doc_id:
                docs[doc_id]["数据块数"] += 1

        if docs:
            # Display as table
            st.subheader("📄 按文档分组")
            df = pd.DataFrame(list(docs.values()))
            st.dataframe(df, use_container_width=True)

            st.markdown("---")

            # Document detail viewer
            st.subheader("🔍 文档详情")

            selected_doc = st.selectbox(
                "选择文档查看详情",
                options=list(docs.keys()),
                format_func=lambda x: docs[x]["文件名"]
            )

            if selected_doc:
                # Query chunks for this document (不传 output_fields)
                doc_results = vector_store.query(
                    expr=f'doc_id == "{selected_doc}"',
                    limit=1000
                )

                if doc_results and len(doc_results) > 0:
                    st.write(f"**文档包含 {len(doc_results)} 个数据块**")

                    # Show first few chunks
                    num_to_show = min(5, len(doc_results))

                    for i, chunk in enumerate(doc_results[:num_to_show]):
                        with st.expander(f"数据块 {i+1} - ID: {chunk.get('id', 'N/A')[:20]}..."):
                            st.write("**文本内容:**")
                            st.text(chunk.get("text", "")[:500])

                            st.write("**元数据:**")
                            st.json(chunk.get("metadata", {}))

                    if len(doc_results) > num_to_show:
                        st.info(f"还有 {len(doc_results) - num_to_show} 个数据块未显示")
        else:
            st.warning("⚠️ 数据中缺少 doc_id 字段，显示所有数据块")
            # Show all chunks without grouping
            chunk_list = []
            for i, result in enumerate(sample_results[:20]):  # 限制显示前20条
                chunk_list.append({
                    "序号": i + 1,
                    "ID": result.get("id", "")[:30] + "...",
                    "文本预览": result.get("text", "")[:50] + "..."
                })
            df = pd.DataFrame(chunk_list)
            st.dataframe(df, use_container_width=True)
    else:
        st.info("❌ 向量库中暂无数据，请先进行文档摄取")

except Exception as e:
    st.error(f"❌ 查询失败: {str(e)}")
    import traceback
    st.code(traceback.format_exc())

st.markdown("---")

# Search functionality
st.subheader("🔎 快速搜索")

search_query = st.text_input("输入搜索关键词")

if search_query:
    try:
        # Get embedding
        embedding = st.session_state.component_loader.get_embedding()
        query_vector = embedding.embed(search_query)

        # Search
        search_results = vector_store.search_dense(
            query_vector=query_vector,
            top_k=5
        )

        st.write(f"**找到 {len(search_results)} 个相关结果**")

        for i, result in enumerate(search_results):
            with st.expander(f"结果 {i+1} - 相似度: {result.get('distance', 0):.4f}"):
                st.write(result.get("text", "")[:300])
                st.json(result.get("metadata", {}))

    except Exception as e:
        st.error(f"搜索失败: {str(e)}")

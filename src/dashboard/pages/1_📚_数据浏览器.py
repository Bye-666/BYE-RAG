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
    # Query sample documents
    collection_name = st.session_state.config.get("milvus.collection_name", "rag_knowledge_hub")
    dense_dim = st.session_state.config.get("milvus.dense_dim", 2048)

    sample_results = vector_store.query(
        collection_name=collection_name,
        data=[[0.0] * dense_dim],
        limit=100,
        output_fields=["id", "doc_id", "text", "metadata"]
    )

    if sample_results and len(sample_results) > 0:
        # Extract unique documents
        docs = {}
        for result in sample_results[0]:
            entity = result.get("entity", {})
            doc_id = entity.get("doc_id")
            if doc_id and doc_id not in docs:
                metadata = entity.get("metadata", {})
                docs[doc_id] = {
                    "文档ID": doc_id,
                    "文件路径": metadata.get("file_path", "未知"),
                    "数据块数": 1
                }
            elif doc_id:
                docs[doc_id]["数据块数"] += 1

        # Display as table
        df = pd.DataFrame(list(docs.values()))
        st.dataframe(df, use_container_width=True)

        st.markdown("---")

        # Document detail viewer
        st.subheader("🔍 文档详情")

        selected_doc = st.selectbox(
            "选择文档查看详情",
            options=list(docs.keys()),
            format_func=lambda x: docs[x]["文件路径"]
        )

        if selected_doc:
            # Query chunks for this document
            collection_name = st.session_state.config.get("milvus.collection_name", "rag_knowledge_hub")
            dense_dim = st.session_state.config.get("milvus.dense_dim", 2048)

            doc_results = vector_store.query(
                collection_name=collection_name,
                data=[[0.0] * dense_dim],
                limit=1000,
                output_fields=["id", "text", "metadata"],
                filter=f'doc_id == "{selected_doc}"'
            )

            if doc_results and len(doc_results[0]) > 0:
                st.write(f"**文档包含 {len(doc_results[0])} 个数据块**")

                # Show first few chunks
                num_to_show = min(5, len(doc_results[0]))

                for i, chunk in enumerate(doc_results[0][:num_to_show]):
                    entity = chunk.get("entity", {})
                    with st.expander(f"数据块 {i+1} - ID: {entity.get('id', 'N/A')[:20]}..."):
                        st.write("**文本内容:**")
                        st.text(entity.get("text", "")[:500])

                        st.write("**元数据:**")
                        st.json(entity.get("metadata", {}))

                if len(doc_results[0]) > num_to_show:
                    st.info(f"还有 {len(doc_results[0]) - num_to_show} 个数据块未显示")
    else:
        st.info("向量库中暂无数据，请先进行文档摄取")

except Exception as e:
    st.error(f"查询失败: {str(e)}")
    st.code(str(e))

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

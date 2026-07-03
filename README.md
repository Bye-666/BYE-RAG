# RAG-MCP-SERVER

> 企业级 RAG 系统 + MCP 协议集成 | Production-Ready

基于 **混合检索（Dense + Sparse）** + **RRF 融合** + **MCP 协议**的完整 RAG 解决方案。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置系统

编辑 `config/settings.yaml`，配置 API Keys：

```yaml
llm:
  provider: dashscope
  api_key: YOUR_DASHSCOPE_API_KEY
  model: qwen-max

embedding:
  provider: dashscope  
  api_key: YOUR_DASHSCOPE_API_KEY
  model: text-embedding-v3

vector_store:
  type: milvus
  uri: ./data/db/milvus.db
```

### 3. 数据摄取

```bash
# 摄取单个文件
python scripts/ingest.py data/documents/report.pdf

# 摄取整个目录
python scripts/ingest.py data/documents/
```

### 4. 查询系统

```bash
# 基础查询
python scripts/query.py "什么是机器学习？"

# 查询改写 + 重排序
python scripts/query.py "ML 是什么？" --rewrite --rerank --top-k 5
```

### 5. 可视化面板

```bash
python scripts/dashboard_server.py
```

访问 http://localhost:5000 查看监控面板

## 📊 系统架构

```
┌─────────────────────────────────────────┐
│         MCP Clients (Claude Desktop)    │
└─────────────────┬───────────────────────┘
                  │
          ┌───────▼────────┐
          │  MCP Server    │
          │  (Tools API)   │
          └───────┬────────┘
                  │
    ┌─────────────┴──────────────┐
    │                            │
┌───▼────────┐          ┌────────▼────┐
│ Ingestion  │          │  Retrieval  │
│  Pipeline  │          │   Pipeline  │
└────┬───────┘          └─────┬───────┘
     │                        │
     ▼                        ▼
┌────────────────────────────────────┐
│     Milvus Vector Store            │
│  (Dense + Sparse Vectors)          │
└────────────────────────────────────┘
```

## 🔥 核心特性

### 混合检索 (Hybrid Search)

- **稠密检索 (Dense)**: Embedding 语义搜索
- **稀疏检索 (Sparse)**: BM25 关键词匹配  
- **RRF 融合**: 互惠排名融合算法

### 数据摄取 (Ingestion)

- PDF 文档解析（PyMuPDF）
- 智能文本分块
- 双向量编码（Dense + Sparse）
- 批量上传优化

### 可插拔架构

- **LLM**: Qwen / GPT / Claude / Ollama
- **Embedding**: Qwen / OpenAI / BGE
- **Vector Store**: Milvus / Chroma / Qdrant
- **Reranker**: CrossEncoder / LLM Rerank

### MCP 协议集成

- 标准化工具接口
- Claude Desktop 原生支持
- 6+ 工具：查询、摄取、文档管理

## 📁 项目结构

```
RAG-MCP-SERVER/
├── src/
│   ├── config/           # 配置管理
│   ├── libs/             # 可插拔组件层
│   │   ├── llm/
│   │   ├── embedding/
│   │   ├── vector_store/
│   │   └── splitter/
│   ├── ingestion/        # 数据摄取
│   │   ├── loaders/
│   │   ├── embedders/
│   │   └── pipeline.py
│   ├── retrieval/        # 检索系统
│   │   ├── retrievers/
│   │   ├── fusion/
│   │   └── hybrid_search.py
│   ├── mcp_server/       # MCP Server
│   ├── trace/            # 追踪系统
│   ├── dashboard/        # 监控面板
│   └── evaluation/       # 评估系统
├── scripts/
│   ├── ingest.py         # 摄取脚本
│   ├── query.py          # 查询脚本
│   └── dashboard_server.py # Web 面板
├── tests/
│   ├── unit/             # 单元测试
│   └── integration/      # 集成测试
└── data/
    ├── documents/        # 原始文档
    └── db/               # 数据库文件
```

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 测试覆盖率
pytest --cov=src tests/
```

## 📖 使用示例

### Python API

```python
from src.retrieval.hybrid_search import HybridSearch
from src.retrieval.query_processor import QueryProcessor

# 初始化
processor = QueryProcessor(llm, embedding, sparse_encoder)
hybrid_search = HybridSearch(dense_retriever, sparse_retriever)

# 处理查询
query_result = processor.process("机器学习的应用场景")

# 混合检索
results = hybrid_search.search(
    dense_vector=query_result["dense_vector"],
    sparse_vector=query_result["sparse_vector"],
    top_k=10
)
```

### MCP 工具

在 Claude Desktop 中使用：

```json
{
  "mcpServers": {
    "rag-system": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/path/to/RAG-MCP-SERVER"
    }
  }
}
```

## 🔧 配置说明

### LLM 配置

```yaml
llm:
  provider: dashscope  # dashscope / openai / azure / ollama
  api_key: YOUR_API_KEY
  model: qwen-max
  temperature: 0.7
  max_tokens: 2000
```

### Embedding 配置

```yaml
embedding:
  provider: dashscope
  api_key: YOUR_API_KEY  
  model: text-embedding-v3
  dimension: 2048
```

### Vector Store 配置

```yaml
vector_store:
  type: milvus
  uri: ./data/db/milvus.db  # 本地文件模式
  collection_name: rag_collection
```

## 📈 性能指标

- **摄取速度**: ~100 chunks/秒
- **查询延迟**: <500ms (包含 LLM)
- **向量维度**: 2048 (Dense) + 稀疏 (Sparse)
- **测试覆盖率**: >90%

## 🛠️ 开发

### 添加新的 LLM 提供商

```python
# src/libs/llm/your_provider.py
from .base import BaseLLM

class YourLLM(BaseLLM):
    def generate(self, prompt: str, **kwargs) -> str:
        # 实现生成逻辑
        pass
```

### 添加新的向量库

```python
# src/libs/vector_store/your_store.py
from .base import BaseVectorStore

class YourVectorStore(BaseVectorStore):
    def upsert(self, ids, texts, vectors, metadatas):
        # 实现上传逻辑
        pass
```

## 📝 开发日志

- **2026-07-03**: 完成全部 68 个任务
  - ✅ 阶段 A-D: 核心 Pipeline (46 任务)
  - ✅ 阶段 E-I: 基础设施 (22 任务)
  - ✅ 300+ 测试用例通过
  - ✅ Web Dashboard 上线

## 📄 许可证

MIT License

## 🤝 贡献

欢迎 PR 和 Issue！

## 📧 联系

项目问题请提交 GitHub Issue

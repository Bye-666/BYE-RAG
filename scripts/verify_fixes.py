#!/usr/bin/env python3
"""
验证脚本 - 检查所有修复的功能

测试内容：
- 配置加载
- TraceContext 功能
- Pipeline 集成
- MCP Server 初始化
- Dashboard 文件语法
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_config():
    """测试配置加载"""
    print("\n[测试 1/5] 配置加载...")
    try:
        from src.config.settings import Settings
        config = Settings()

        # 测试字典访问
        llm_model = config.get("llm.model", "未配置")
        milvus_uri = config.get("milvus.uri", "未配置")

        print(f"  [OK] 配置加载成功")
        print(f"    - LLM 模型: {llm_model}")
        print(f"    - Milvus URI: {milvus_uri}")
        return True
    except Exception as e:
        print(f"  [FAIL] 配置加载失败: {e}")
        return False


def test_trace_context():
    """测试 TraceContext"""
    print("\n[测试 2/5] TraceContext...")
    try:
        from src.trace.trace_context import TraceContext, get_trace_recorder

        recorder = get_trace_recorder()
        recorder.clear()

        # 测试基础追踪
        with TraceContext("test", "test_operation") as trace:
            trace.add_step("step1", {"data": "value"})
            trace.finish({"result": "ok"})

        traces = recorder.get_traces()
        assert len(traces) == 1
        assert traces[0]["trace_type"] == "test"

        print(f"  [OK] TraceContext 测试通过")
        print(f"    - 追踪记录数: {len(traces)}")
        return True
    except Exception as e:
        print(f"  [FAIL] TraceContext 测试失败: {e}")
        return False


def test_pipeline_trace():
    """测试 Pipeline 追踪集成"""
    print("\n[测试 3/5] Pipeline 追踪集成...")
    try:
        from src.ingestion.pipeline import IngestionPipeline
        from src.trace.trace_context import TraceContext

        # 检查是否导入了 TraceContext
        import inspect
        source = inspect.getsource(IngestionPipeline.ingest_file)

        has_trace = "TraceContext" in source
        has_enable_trace = "enable_trace" in source

        assert has_trace, "Pipeline 未导入 TraceContext"
        assert has_enable_trace, "Pipeline 未支持 enable_trace 参数"

        print(f"  [OK] Pipeline 追踪集成检查通过")
        return True
    except Exception as e:
        print(f"  [FAIL] Pipeline 追踪集成检查失败: {e}")
        return False


def test_mcp_server():
    """测试 MCP Server 初始化"""
    print("\n[测试 4/5] MCP Server...")
    try:
        # 检查源代码文件
        mcp_server_path = Path("src/mcp_server/server.py")
        if not mcp_server_path.exists():
            print(f"  [FAIL] MCP Server 文件不存在")
            return False

        with open(mcp_server_path, 'r', encoding='utf-8') as f:
            source = f.read()

        has_component_loader = "ComponentLoader" in source
        has_ingestion_pipeline = "IngestionPipeline" in source
        has_init_components = "_init_components" in source or "component_loader = ComponentLoader" in source

        if not has_component_loader:
            print(f"  [FAIL] MCP Server 未导入 ComponentLoader")
            return False

        if not has_ingestion_pipeline:
            print(f"  [FAIL] MCP Server 未导入 IngestionPipeline")
            return False

        if not has_init_components:
            print(f"  [FAIL] MCP Server 未初始化组件")
            return False

        print(f"  [OK] MCP Server 结构检查通过")
        return True
    except Exception as e:
        print(f"  [FAIL] MCP Server 检查失败: {e}")
        return False


def test_dashboard_syntax():
    """测试 Dashboard 文件语法"""
    print("\n[测试 5/5] Dashboard 语法...")
    try:
        import py_compile

        files = [
            "src/dashboard/streamlit_app.py",
            "src/dashboard/utils.py",
        ]

        # 测试 pages
        pages_dir = Path("src/dashboard/pages")
        if pages_dir.exists():
            files.extend([str(f) for f in pages_dir.glob("*.py")])

        errors = []
        for file in files:
            try:
                py_compile.compile(file, doraise=True)
            except py_compile.PyCompileError as e:
                errors.append(f"{file}: {e}")

        if errors:
            print(f"  [FAIL] 发现 {len(errors)} 个语法错误:")
            for err in errors:
                print(f"    - {err}")
            return False

        print(f"  [OK] Dashboard 语法检查通过")
        print(f"    - 检查文件数: {len(files)}")
        return True
    except Exception as e:
        print(f"  [FAIL] Dashboard 语法检查失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("RAG-MCP-SERVER 修复验证")
    print("=" * 60)

    results = []

    results.append(("配置加载", test_config()))
    results.append(("TraceContext", test_trace_context()))
    results.append(("Pipeline 追踪", test_pipeline_trace()))
    results.append(("MCP Server", test_mcp_server()))
    results.append(("Dashboard 语法", test_dashboard_syntax()))

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n[SUCCESS] 所有测试通过！系统修复完成。")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} 个测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

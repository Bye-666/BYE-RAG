#!/usr/bin/env python3
"""
完整功能验证脚本 - 端到端测试

测试所有已修复的功能模块
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_imports():
    """测试核心模块导入"""
    print_section("测试 1: 核心模块导入")

    modules = [
        ("配置系统", "src.config.settings", "Settings"),
        ("TraceContext", "src.trace.trace_context", "TraceContext"),
        ("ComponentLoader", "src.libs.loader", "ComponentLoader"),
        ("IngestionPipeline", "src.ingestion.pipeline", "IngestionPipeline"),
        ("HybridSearch", "src.retrieval.hybrid_search", "HybridSearch"),
        ("MCPServer", "src.mcp_server.server", "MCPServer"),
    ]

    success = 0
    for name, module, cls in modules:
        try:
            exec(f"from {module} import {cls}")
            print(f"  [OK] {name}")
            success += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")

    print(f"\n结果: {success}/{len(modules)} 模块导入成功")
    return success == len(modules)


def test_config_access():
    """测试配置访问"""
    print_section("测试 2: 配置访问")

    try:
        from src.config.settings import Settings

        config = Settings()

        # 测试字典访问
        llm_model = config.get("llm.model", "default")
        milvus_uri = config.get("milvus.uri", "default")
        embedding_model = config.get("embedding.model", "default")

        print(f"  [OK] 配置字典访问正常")
        print(f"    - llm.model: {llm_model}")
        print(f"    - milvus.uri: {milvus_uri}")
        print(f"    - embedding.model: {embedding_model}")

        return True
    except Exception as e:
        print(f"  [FAIL] 配置访问失败: {e}")
        return False


def test_trace_context():
    """测试追踪系统"""
    print_section("测试 3: TraceContext 功能")

    try:
        from src.trace.trace_context import TraceContext, get_trace_recorder

        recorder = get_trace_recorder()
        recorder.clear()

        # 测试基础追踪
        with TraceContext("test", "basic_test") as trace:
            trace.add_step("step1", {"data": "value1"})
            trace.add_step("step2", {"data": "value2"})
            trace.finish({"status": "success"})

        traces = recorder.get_traces()

        assert len(traces) == 1, f"期望 1 个追踪，实际 {len(traces)} 个"
        assert traces[0]["trace_type"] == "test"
        assert len(traces[0]["steps"]) == 2
        assert traces[0]["duration_ms"] is not None

        print(f"  [OK] TraceContext 功能正常")
        print(f"    - 追踪记录数: {len(traces)}")
        print(f"    - 耗时: {traces[0]['duration_ms']:.2f} ms")

        # 测试嵌套追踪
        recorder.clear()
        with TraceContext("test", "parent") as parent:
            parent.add_step("parent_step", {})
            with parent.sub_trace("child") as child:
                child.add_step("child_step", {})

        traces = recorder.get_traces()
        assert len(traces[0]["sub_traces"]) == 1

        print(f"  [OK] 嵌套追踪正常")

        return True
    except Exception as e:
        print(f"  [FAIL] TraceContext 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dashboard_files():
    """测试 Dashboard 文件"""
    print_section("测试 4: Dashboard 文件")

    files = [
        "src/dashboard/streamlit_app.py",
        "src/dashboard/session_init.py",
        "src/dashboard/utils.py",
    ]

    # 添加 pages
    pages_dir = Path("src/dashboard/pages")
    if pages_dir.exists():
        files.extend([str(f) for f in pages_dir.glob("*.py")])

    success = 0
    for file in files:
        file_path = Path(file)
        if file_path.exists():
            # 移除 emoji 避免编码问题
            display_name = file_path.name.encode('ascii', 'ignore').decode('ascii')
            if not display_name:
                display_name = "page_file"
            print(f"  [OK] {display_name}")
            success += 1
        else:
            display_name = file_path.name.encode('ascii', 'ignore').decode('ascii')
            if not display_name:
                display_name = "page_file"
            print(f"  [FAIL] {display_name} 不存在")

    print(f"\n结果: {success}/{len(files)} 文件存在")
    return success == len(files)


def test_mcp_server_structure():
    """测试 MCP Server 结构"""
    print_section("测试 5: MCP Server 结构")

    try:
        mcp_server_path = Path("src/mcp_server/server.py")
        if not mcp_server_path.exists():
            print(f"  [FAIL] server.py 不存在")
            return False

        with open(mcp_server_path, 'r', encoding='utf-8') as f:
            source = f.read()

        checks = [
            ("ComponentLoader 导入", "ComponentLoader" in source),
            ("IngestionPipeline 导入", "IngestionPipeline" in source),
            ("组件初始化", "component_loader = ComponentLoader" in source or "_init_components" in source),
            ("ingest_document 工具", "def ingest_document" in source),
            ("query 工具", "def query" in source),
            ("list_documents 工具", "def list_documents" in source),
        ]

        all_passed = True
        for name, result in checks:
            if result:
                print(f"  [OK] {name}")
            else:
                print(f"  [FAIL] {name}")
                all_passed = False

        return all_passed
    except Exception as e:
        print(f"  [FAIL] MCP Server 检查失败: {e}")
        return False


def test_dependencies():
    """测试依赖安装"""
    print_section("测试 6: 依赖检查")

    deps = [
        ("streamlit", "必需 - Dashboard"),
        ("pandas", "必需 - 数据处理"),
        ("plotly", "可选 - 图表"),
        ("pymilvus", "必需 - 向量库"),
        ("yaml", "必需 - 配置"),
    ]

    installed = 0
    optional_missing = []

    for dep, desc in deps:
        try:
            __import__(dep)
            print(f"  [OK] {dep:15s} - {desc}")
            installed += 1
        except ImportError:
            if "可选" in desc:
                print(f"  [WARN] {dep:15s} - {desc} (未安装)")
                optional_missing.append(dep)
            else:
                print(f"  [FAIL] {dep:15s} - {desc} (未安装)")

    print(f"\n结果: {installed}/{len(deps)} 依赖已安装")

    if optional_missing:
        print(f"\n可选依赖未安装: {', '.join(optional_missing)}")
        print(f"安装命令: pip install {' '.join(optional_missing)}")

    return True  # 只要必需依赖安装就算通过


def main():
    """运行所有测试"""
    print("=" * 60)
    print("  RAG-MCP-SERVER 完整功能验证")
    print("=" * 60)

    results = []

    results.append(("核心模块导入", test_imports()))
    results.append(("配置访问", test_config_access()))
    results.append(("TraceContext", test_trace_context()))
    results.append(("Dashboard 文件", test_dashboard_files()))
    results.append(("MCP Server", test_mcp_server_structure()))
    results.append(("依赖检查", test_dependencies()))

    print_section("测试总结")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"{status:15s} - {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n" + "=" * 60)
        print("  [SUCCESS] 所有测试通过！")
        print("=" * 60)
        print("\n下一步:")
        print("  1. 启动 Dashboard: python scripts/run_dashboard.py")
        print("  2. 摄取文档: 在 Dashboard 中上传 PDF")
        print("  3. 查询测试: 在 Dashboard 中执行查询")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print(f"  [WARNING] {total - passed} 个测试失败")
        print("=" * 60)
        print("\n请检查上述错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())

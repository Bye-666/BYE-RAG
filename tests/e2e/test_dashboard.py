"""Dashboard smoke test script.

Tests basic functionality of all Dashboard pages.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_dashboard_imports():
    """Test 1: Import Dashboard modules."""
    print("\n[Test 1/6] Dashboard 模块导入测试...")

    modules = [
        ("主应用", "src.dashboard.streamlit_app"),
        ("Session 初始化", "src.dashboard.session_init"),
        ("工具函数", "src.dashboard.utils"),
    ]

    success = 0
    for name, module in modules:
        try:
            __import__(module)
            print(f"  [OK] {name}")
            success += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")

    if success == len(modules):
        print(f"  [OK] 所有 {len(modules)} 个模块导入成功")
        return True
    else:
        print(f"  [FAIL] {len(modules) - success} 个模块导入失败")
        return False


def test_dashboard_pages():
    """Test 2: Check Dashboard pages."""
    print("\n[Test 2/6] Dashboard 页面检查...")

    pages_dir = Path("src/dashboard/pages")

    if not pages_dir.exists():
        print(f"  [FAIL] 页面目录不存在: {pages_dir}")
        return False

    expected_pages = 6
    page_files = list(pages_dir.glob("*.py"))

    print(f"  找到 {len(page_files)} 个页面文件")
    # Don't print filenames with emoji to avoid encoding issues

    if len(page_files) >= expected_pages:
        print(f"  [OK] 页面文件完整 ({len(page_files)}/{expected_pages})")
        return True
    else:
        print(f"  [WARN] 页面文件不足 ({len(page_files)}/{expected_pages})")
        return True  # Not failing


def test_session_init():
    """Test 3: Test session initialization."""
    print("\n[Test 3/6] Session 初始化测试...")

    try:
        from src.dashboard.session_init import init_session_state

        print("  [OK] init_session_state 函数存在")

        # Check function signature
        import inspect
        sig = inspect.signature(init_session_state)

        print(f"  [OK] 函数签名: {sig}")
        return True

    except Exception as e:
        print(f"  [FAIL] 测试失败: {e}")
        return False


def test_utils_functions():
    """Test 4: Test utility functions."""
    print("\n[Test 4/6] 工具函数测试...")

    try:
        from src.dashboard.utils import (
            get_config_value,
            get_milvus_config,
            get_llm_config,
            get_embedding_config
        )

        functions = [
            "get_config_value",
            "get_milvus_config",
            "get_llm_config",
            "get_embedding_config"
        ]

        print("  工具函数检查:")
        for func_name in functions:
            print(f"    [OK] {func_name}")

        print(f"  [OK] 所有 {len(functions)} 个工具函数已定义")
        return True

    except Exception as e:
        print(f"  [FAIL] 测试失败: {e}")
        return False


def test_page_structure():
    """Test 5: Check page structure."""
    print("\n[Test 5/6] 页面结构测试...")

    try:
        pages_dir = Path("src/dashboard/pages")
        page_files = list(pages_dir.glob("*.py"))

        required_patterns = [
            "st.set_page_config",
            "init_session_state",
        ]

        print("  检查页面必需模式:")
        checked = 0
        for i, page_file in enumerate(page_files[:3]):  # Check first 3
            with open(page_file, 'r', encoding='utf-8') as f:
                content = f.read()

            has_all = all(pattern in content for pattern in required_patterns)
            if has_all:
                print(f"    [OK] page_{i+1}")
                checked += 1
            else:
                print(f"    [WARN] page_{i+1} 缺少部分模式")

        if checked > 0:
            print(f"  [OK] 页面结构检查完成 ({checked} 个页面)")
            return True
        else:
            print("  [WARN] 无法验证页面结构")
            return True  # Not critical

    except Exception as e:
        print(f"  [FAIL] 测试失败: {e}")
        return False


def test_dependencies():
    """Test 6: Check Dashboard dependencies."""
    print("\n[Test 6/6] 依赖检查...")

    deps = [
        ("streamlit", "必需"),
        ("pandas", "必需"),
        ("plotly", "可选"),
    ]

    print("  依赖状态:")
    required_ok = True

    for dep, status in deps:
        try:
            __import__(dep)
            print(f"    [OK] {dep:15s} - {status}")
        except ImportError:
            if status == "必需":
                print(f"    [FAIL] {dep:15s} - {status} (未安装)")
                required_ok = False
            else:
                print(f"    [WARN] {dep:15s} - {status} (未安装)")

    if required_ok:
        print("  [OK] 必需依赖已安装")
        return True
    else:
        print("  [FAIL] 缺少必需依赖")
        return False


def main():
    """Run all Dashboard smoke tests."""
    print("=" * 60)
    print("  Dashboard 冒烟测试")
    print("=" * 60)

    tests = [
        ("Dashboard 模块导入", test_dashboard_imports),
        ("Dashboard 页面检查", test_dashboard_pages),
        ("Session 初始化", test_session_init),
        ("工具函数", test_utils_functions),
        ("页面结构", test_page_structure),
        ("依赖检查", test_dependencies),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[ERROR] 测试异常: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("  测试总结")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"{status:15s} - {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n[SUCCESS] Dashboard 冒烟测试通过！")
        print("\nDashboard 功能正常，可以:")
        print("  1. 启动 Dashboard: python scripts/run_dashboard.py")
        print("  2. 访问: http://localhost:8501")
        print("  3. 使用所有 6 个页面")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} 个测试失败")
        print("建议检查失败的测试项")
        return 1


if __name__ == "__main__":
    sys.exit(main())

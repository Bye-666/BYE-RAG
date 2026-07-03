#!/usr/bin/env python3
"""
Streamlit Dashboard启动脚本

Usage:
    python scripts/run_dashboard.py
    或
    streamlit run src/dashboard/streamlit_app.py
"""

import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """启动 Streamlit Dashboard"""
    dashboard_path = project_root / "src" / "dashboard" / "streamlit_app.py"

    if not dashboard_path.exists():
        print(f"错误: Dashboard 文件不存在: {dashboard_path}")
        sys.exit(1)

    print("=" * 60)
    print("启动 RAG System Dashboard")
    print("=" * 60)
    print(f"Dashboard 路径: {dashboard_path}")
    print("")
    print("Dashboard 将在浏览器中打开...")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    print("")

    # 启动 Streamlit
    try:
        subprocess.run([
            "streamlit",
            "run",
            str(dashboard_path),
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n\nDashboard 已停止")
    except FileNotFoundError:
        print("错误: streamlit 未安装")
        print("请运行: pip install streamlit")
        sys.exit(1)


if __name__ == "__main__":
    main()

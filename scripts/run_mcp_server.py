#!/usr/bin/env python3
"""
MCP Server startup script.

Usage:
    python scripts/run_mcp_server.py [--config CONFIG_PATH]
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.mcp_server.server import MCPServer


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run the RAG MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default config
  python scripts/run_mcp_server.py

  # Run with custom config
  python scripts/run_mcp_server.py --config config/settings.yaml
"""
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config/settings.yaml',
        help='Path to configuration file'
    )

    args = parser.parse_args()

    # Initialize and run server
    # Print to stderr to avoid breaking stdio MCP protocol
    print("Starting RAG MCP Server...", file=sys.stderr)
    print(f"Config: {args.config}", file=sys.stderr)
    print("-" * 60, file=sys.stderr)

    try:
        server = MCPServer(config_path=args.config)
        server.run()
    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

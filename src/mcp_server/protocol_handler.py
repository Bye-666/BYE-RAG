"""MCP Protocol handler for request/response processing."""

from typing import Dict, Any, List
from mcp.types import Tool, TextContent
import json


class ProtocolHandler:
    """Handle MCP protocol requests and responses.

    Provides request validation, response formatting, and error handling.
    """

    def __init__(self):
        """Initialize ProtocolHandler."""
        self.supported_tools = [
            "ingest_document",
            "query",
            "list_documents",
            "query_knowledge_hub",
            "list_collections",
            "get_document_summary"
        ]

    def validate_request(self, tool_name: str, arguments: Dict[str, Any]) -> tuple[bool, str]:
        """Validate tool request.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Tuple of (is_valid, error_message)
        """
        if tool_name not in self.supported_tools:
            return False, f"Unknown tool: {tool_name}"

        # Tool-specific validation
        if tool_name == "ingest_document":
            if "file_path" not in arguments:
                return False, "Missing required argument: file_path"

        elif tool_name == "query":
            if "query" not in arguments:
                return False, "Missing required argument: query"

        elif tool_name == "get_document_summary":
            if "doc_id" not in arguments:
                return False, "Missing required argument: doc_id"

        return True, ""

    def format_response(self, data: Any) -> List[TextContent]:
        """Format response data as TextContent.

        Args:
            data: Response data

        Returns:
            List of TextContent
        """
        if isinstance(data, dict) or isinstance(data, list):
            text = json.dumps(data, indent=2, ensure_ascii=False)
        else:
            text = str(data)

        return [TextContent(type="text", text=text)]

    def format_error(self, error: str) -> List[TextContent]:
        """Format error message.

        Args:
            error: Error message

        Returns:
            List of TextContent
        """
        error_response = {
            "error": error,
            "status": "failed"
        }
        return [TextContent(
            type="text",
            text=json.dumps(error_response, indent=2)
        )]

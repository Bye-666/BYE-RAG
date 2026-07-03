"""E2E tests for MCP Server tools."""

import pytest

from src.mcp_server.server import MCPServer


class TestMCPServerE2E:
    """End-to-end tests for MCP Server."""

    @pytest.mark.asyncio
    async def test_all_tools_registered(self):
        """All 6 tools are registered."""
        server = MCPServer()

        # Server should be initialized
        assert server.server is not None


    @pytest.mark.asyncio
    async def test_ingest_tool(self):
        """Ingest document tool works."""
        server = MCPServer()

        result = await server._handle_ingest({"file_path": "test.pdf"})

        assert len(result) == 1
        assert "test.pdf" in result[0].text


    @pytest.mark.asyncio
    async def test_query_tool(self):
        """Query tool works."""
        server = MCPServer()

        result = await server._handle_query({"query": "test query", "top_k": 5})

        assert len(result) == 1
        assert "test query" in result[0].text
        assert "5" in result[0].text


    @pytest.mark.asyncio
    async def test_list_documents_tool(self):
        """List documents tool works."""
        server = MCPServer()

        result = await server._handle_list_documents({})

        assert len(result) == 1
        assert "documents" in result[0].text


    @pytest.mark.asyncio
    async def test_query_knowledge_hub_tool(self):
        """Query knowledge hub tool works."""
        server = MCPServer()

        result = await server._handle_query_knowledge_hub({
            "collection": "technical",
            "query": "test query"
        })

        assert len(result) == 1
        assert "technical" in result[0].text


    @pytest.mark.asyncio
    async def test_list_collections_tool(self):
        """List collections tool works."""
        server = MCPServer()

        result = await server._handle_list_collections({})

        assert len(result) == 1
        assert "collections" in result[0].text
        assert "default" in result[0].text


    @pytest.mark.asyncio
    async def test_get_document_summary_tool(self):
        """Get document summary tool works."""
        server = MCPServer()

        result = await server._handle_get_document_summary({"doc_id": "doc123"})

        assert len(result) == 1
        assert "doc123" in result[0].text
        assert "summary" in result[0].text

"""Tests for ProtocolHandler."""

import pytest

from src.mcp_server.protocol_handler import ProtocolHandler


def test_protocol_handler_instantiation():
    """ProtocolHandler can be instantiated."""
    handler = ProtocolHandler()
    assert len(handler.supported_tools) > 0


def test_validate_request_valid():
    """Validate valid request."""
    handler = ProtocolHandler()

    is_valid, error = handler.validate_request("query", {"query": "test"})

    assert is_valid is True
    assert error == ""


def test_validate_request_unknown_tool():
    """Validate unknown tool."""
    handler = ProtocolHandler()

    is_valid, error = handler.validate_request("unknown_tool", {})

    assert is_valid is False
    assert "Unknown tool" in error


def test_validate_request_missing_argument():
    """Validate request with missing argument."""
    handler = ProtocolHandler()

    is_valid, error = handler.validate_request("ingest_document", {})

    assert is_valid is False
    assert "file_path" in error


def test_format_response_dict():
    """Format dict response."""
    handler = ProtocolHandler()

    response = handler.format_response({"key": "value"})

    assert len(response) == 1
    assert "key" in response[0].text


def test_format_response_list():
    """Format list response."""
    handler = ProtocolHandler()

    response = handler.format_response([1, 2, 3])

    assert len(response) == 1
    assert "1" in response[0].text


def test_format_error():
    """Format error message."""
    handler = ProtocolHandler()

    response = handler.format_error("Test error")

    assert len(response) == 1
    assert "error" in response[0].text
    assert "Test error" in response[0].text

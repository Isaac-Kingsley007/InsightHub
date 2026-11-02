"""Offline MCP registration and dispatch tests."""

import json
import unittest
from unittest.mock import patch
from mcp import Client

from src.agent.tools import search_documents, run_safe_query
from src.data_tool.query import SafeQueryError
from src.rag.ask import RetrievalError
from src.rag.schemas import AskResult
from src.mcp.server import mcp


class MCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_tools_share_descriptions_and_expected_inputs(self):
        tools = {tool.name: tool for tool in await mcp.list_tools()}
        self.assertEqual(set(tools), {"search_documents", "run_safe_query"})
        self.assertEqual(tools["search_documents"].description, search_documents.description)
        self.assertEqual(tools["run_safe_query"].description, run_safe_query.description)
        self.assertEqual(tools["search_documents"].input_schema["required"], ["query"])
        self.assertEqual(tools["run_safe_query"].input_schema["required"], ["sql"])

    async def test_dispatch_preserves_query_results_and_citations(self):
        expected = {"columns": ["total"], "rows": [[10]], "row_count": 1, "truncated": False}
        with patch("src.mcp.server.execute_safe_query", return_value=expected) as execute:
            result = await mcp.call_tool("run_safe_query", {"sql": "SELECT COUNT(*) FROM customers"})
            self.assertFalse(result.is_error)
            self.assertEqual(json.loads(result.content[0].text), expected)
            execute.assert_called_once_with("SELECT COUNT(*) FROM customers")
        with patch("src.mcp.server.ask_question", return_value=AskResult(
                answer="Refunds within 30 days.", source_chunks=["chunk-1"])):
            result = await mcp.call_tool("search_documents", {"query": "refund policy"})
            self.assertFalse(result.is_error)
            self.assertEqual(json.loads(result.content[0].text)["source_chunks"], ["chunk-1"])

    async def test_failures_are_mcp_errors(self):
        # Exercise the protocol boundary: direct server calls raise ToolError,
        # while MCP clients receive a result with is_error=True.
        async with Client(mcp) as client:
            with patch("src.mcp.server.execute_safe_query", side_effect=SafeQueryError("Only SELECT is allowed.")):
                result = await client.call_tool("run_safe_query", {"sql": "DELETE FROM customers"})
                self.assertTrue(result.is_error)
                self.assertIn("Only SELECT", result.content[0].text)
            with patch("src.mcp.server.ask_question", side_effect=RetrievalError("Gemini unavailable.")):
                result = await client.call_tool("search_documents", {"query": "refund"})
                self.assertTrue(result.is_error)


if __name__ == "__main__":
    unittest.main()

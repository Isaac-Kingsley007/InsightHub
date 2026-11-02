"""Offline checks: python -m unittest src.agent.test_agent."""

import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.api.main import app
from src.agent.agent import get_agent, invoke_agent
from src.agent.tools import run_safe_query, search_documents
from src.data_tool.query import SafeQueryError
from src.rag.ask import RetrievalError


class AgentTests(unittest.TestCase):
    def test_thread_id_and_current_turn_tools(self):
        messages = [HumanMessage(content="old"),
                    ToolMessage(content="old result", tool_call_id="old", name="search_documents"),
                    AIMessage(content="old answer"), HumanMessage(content="new"),
                    ToolMessage(content="new result", tool_call_id="new", name="run_safe_query"),
                    AIMessage(content=[{"type": "text", "text": "There are 10 customers."}])]
        runner = Mock()
        runner.invoke.return_value = {"messages": messages}
        with patch("src.agent.agent.get_agent", return_value=runner):
            result = invoke_agent("new", "session-1")
        self.assertEqual(result, {"answer": "There are 10 customers.", "tools_used": ["run_safe_query"]})
        self.assertEqual(runner.invoke.call_args.kwargs["config"]["configurable"]["thread_id"], "session-1")

    def test_omitted_sessions_are_isolated(self):
        runner = Mock()
        runner.invoke.return_value = {"messages": [HumanMessage(content="hi"), AIMessage(content="Hello")]}
        with patch("src.agent.agent.get_agent", return_value=runner):
            invoke_agent("hi")
            invoke_agent("hi")
        threads = [call.kwargs["config"]["configurable"]["thread_id"] for call in runner.invoke.call_args_list]
        self.assertNotEqual(*threads)

    def test_tool_errors_are_returned_to_model(self):
        with patch("src.agent.tools.execute_safe_query", side_effect=SafeQueryError("Unsupported SQL")):
            self.assertEqual(run_safe_query.invoke({"sql": "DELETE FROM customers"}), {"error": "Unsupported SQL"})
        with patch("src.agent.tools.ask_question", side_effect=RetrievalError("Unavailable")):
            self.assertEqual(search_documents.invoke({"query": "refund"}), {"error": "Unavailable"})

    def test_model_configuration_and_memory(self):
        get_agent.cache_clear()
        self.addCleanup(get_agent.cache_clear)
        with patch("src.agent.agent.load_dotenv"), \
             patch.dict("os.environ", {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "test-model"}), \
             patch("src.agent.agent.ChatGoogleGenerativeAI") as model, \
             patch("src.agent.agent.create_agent") as create:
            get_agent()
            get_agent()
        model.assert_called_once()
        self.assertEqual(model.call_args.kwargs["api_key"], "test-key")
        self.assertEqual(create.call_args.kwargs["model"], model.return_value)
        self.assertIsNotNone(create.call_args.kwargs["checkpointer"])

    def test_api_contract_and_errors(self):
        with TestClient(app) as client, patch("src.api.main.invoke_agent") as invoke:
            invoke.return_value = {"answer": "10 customers", "tools_used": ["run_safe_query"]}
            response = client.post("/agent", json={"query": "How many customers?", "session_id": "one"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), invoke.return_value)
            invoke.assert_called_with("How many customers?", "one")
            invoke.reset_mock()
            self.assertEqual(client.post("/agent", json={"query": "  "}).status_code, 422)
            invoke.assert_not_called()
            invoke.side_effect = RuntimeError("private provider detail")
            response = client.post("/agent", json={"query": "Hi"})
            self.assertEqual(response.status_code, 502)
            self.assertNotIn("private provider detail", response.text)


if __name__ == "__main__":
    unittest.main()

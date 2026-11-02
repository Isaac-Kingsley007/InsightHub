from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from src.rag.ask import ask_question, RetrievalError
from src.data_tool.query import run_safe_query as execute_safe_query, SafeQueryError
from src.tool_descriptions import SEARCH_DOCUMENTS, RUN_SAFE_QUERY

mcp = MCPServer(
    "insight_hub_mcp_server",
    instructions="Use search_documents for policy evidence and run_safe_query for customer data. "
    "Use both for mixed questions. Ground answers in successful results, preserve document "
    "citation IDs, and explain missing evidence or tool errors without inventing results.",
)

@mcp.tool(description=SEARCH_DOCUMENTS)
def search_documents(query: str) -> dict:
    """Return a grounded document answer or a recoverable tool error."""
    try:
        return ask_question(query).model_dump()
    except RetrievalError as exc:
        raise ToolError(str(exc)) from None

@mcp.tool(description=RUN_SAFE_QUERY)
def run_safe_query(sql: str) -> dict:
    """Return customer query results or a recoverable tool error."""
    try:
        return execute_safe_query(sql)
    except SafeQueryError as exc:
        raise ToolError(str(exc)) from None

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8001)

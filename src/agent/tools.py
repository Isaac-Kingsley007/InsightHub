from langchain.tools import tool
from src.rag.ask import ask_question, RetrievalError
from src.data_tool.query import run_safe_query as execute_safe_query, SafeQueryError
from src.tool_descriptions import SEARCH_DOCUMENTS, RUN_SAFE_QUERY

@tool(description=SEARCH_DOCUMENTS)
def search_documents(query: str) -> dict:
    """Return a grounded document answer or a recoverable tool error."""
    try:
        return ask_question(query).model_dump()
    except RetrievalError as exc:
        return {"error": str(exc)}

@tool(description=RUN_SAFE_QUERY)
def run_safe_query(sql: str) -> dict:
    """Return customer query results or a recoverable tool error."""
    try:
        return execute_safe_query(sql)
    except SafeQueryError as exc:
        return {"error": str(exc)}

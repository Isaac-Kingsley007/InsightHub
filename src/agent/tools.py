from langchain.tools import tool
from src.rag.ask import ask_question, RetrievalError
from src.data_tool.query import run_safe_query as execute_safe_query, SafeQueryError

@tool
def search_documents(query: str) -> dict:
    """
    Search documents for relevant information based on the query using rag.

    args: 
        query (str): The query based on which the documents will be searched and relevant information will be returned.
    """
    try:
        return ask_question(query).model_dump()
    except RetrievalError as exc:
        return {"error": str(exc)}

@tool
def run_safe_query(sql: str) -> dict:
    """
    Run a safe SQL query against the database.

    args: 
        sql (str): One SELECT query against public.customers.
    """
    try:
        return execute_safe_query(sql)
    except SafeQueryError as exc:
        return {"error": str(exc)}

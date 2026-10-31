"""Run from the project root: python -m uvicorn src.api.main:app --reload."""

from fastapi import FastAPI, HTTPException

from src.llm.schemas import AnalysisResult, AnalyzeRequest
from src.llm.service import AnalysisError, analyze_text
from src.rag.ask import RetrievalError, ask_question
from src.rag.schemas import AskRequest, AskResult

app = FastAPI(title="InsightHub")


@app.post("/ask", response_model=AskResult)
def ask(request: AskRequest) -> AskResult:
    try:
        return ask_question(request.question)
    except RetrievalError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from None


@app.post("/analyze", response_model=AnalysisResult)
def analyze(request: AnalyzeRequest) -> AnalysisResult:
    try:
        return analyze_text(request.text)
    except AnalysisError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from None

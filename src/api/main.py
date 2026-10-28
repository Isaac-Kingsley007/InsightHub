"""Run from the project root: python -m uvicorn src.api.main:app --reload."""

from fastapi import FastAPI, HTTPException

from src.llm.schemas import AnalysisResult, AnalyzeRequest
from src.llm.service import AnalysisError, analyze_text

app = FastAPI(title="InsightHub")


@app.post("/analyze", response_model=AnalysisResult)
def analyze(request: AnalyzeRequest) -> AnalysisResult:
    try:
        return analyze_text(request.text)
    except AnalysisError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from None

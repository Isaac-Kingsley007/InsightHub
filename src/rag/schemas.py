"""Request and response contracts for POST /ask."""

from pydantic import BaseModel, ConfigDict

from src.llm.schemas import NonEmptyText


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    question: NonEmptyText


class AskResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    answer: NonEmptyText
    source_chunks: list[NonEmptyText]

"""The JSON contract shared by Gemini and the API."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: NonEmptyText


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    sentiment: Literal["positive", "neutral", "negative", "mixed"]
    topics: list[NonEmptyText]
    summary: NonEmptyText

    @field_validator("summary")
    @classmethod
    def require_one_line(cls, value):
        if len(value.splitlines()) != 1:
            raise ValueError("Summary must be a single line.")
        return value

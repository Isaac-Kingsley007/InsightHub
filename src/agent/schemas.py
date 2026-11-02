from pydantic import BaseModel, ConfigDict

from src.llm.schemas import NonEmptyText


class AgentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    query: NonEmptyText
    session_id: NonEmptyText | None = None


class AgentResult(BaseModel):
    answer: NonEmptyText
    tools_used: list[str]

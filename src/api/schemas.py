from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str
    conversation_id: str | None = None


class DirectSearchRequest(BaseModel):
    query: str
    engine: str  # relational, vector, keyword, log, code
    top_k: int = 10


class StatsResponse(BaseModel):
    collections: list[str]
    tool_count: int

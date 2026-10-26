from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    session_id: str | None = Field(default=None, max_length=80, pattern=r'^[A-Za-z0-9_-]+$')


class Source(BaseModel):
    ref: str
    document: str
    chunk: int
    excerpt: str
    similarity: float


class AskResponse(BaseModel):
    answer: str
    session_id: str
    trace_id: str
    tools_used: list[str]
    sources: list[Source]


class UploadResponse(BaseModel):
    document_id: str
    name: str
    chunks: int


class HistoryItem(BaseModel):
    trace_id: str
    session_id: str
    question: str
    answer: str
    tools_used: list[str]
    sources: list[Source]
    timestamp: str

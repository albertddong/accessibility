from typing import Any

from pydantic import BaseModel, Field


class AnalysisItem(BaseModel):
    type: str
    number: int | None = None
    page: int | None = None
    title: str
    description: str
    confidence: float | None = None
    needs_review: bool | None = None
    review_reason: str | None = None
    table_data: list[list[Any]] | None = None


class PdfAnalysis(BaseModel):
    title: str
    items: list[AnalysisItem]


class UsageStats(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    model: str | None = None


class AnalyzeResponse(BaseModel):
    analysis: PdfAnalysis
    usage: UsageStats


class CreateGoogleDocRequest(BaseModel):
    analysis: PdfAnalysis


class DebugLogEntry(BaseModel):
    item_number: int | str | None = None
    item_title: str | None = None
    table_insert_location: int | None = None
    table_data: list[list[Any]] | None = None
    tables_before: list[dict[str, Any]] | None = None
    tables_after: list[dict[str, Any]] | None = None
    comment_error: str | None = None
    comment_payload: dict[str, Any] | None = None


class CreateGoogleDocResponse(BaseModel):
    document_id: str
    document_url: str
    debug_logs: list[DebugLogEntry] = Field(default_factory=list)

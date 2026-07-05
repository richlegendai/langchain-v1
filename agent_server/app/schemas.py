from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class DraftStatus(StrEnum):
    draft = "draft"
    reviewing = "reviewing"
    ready_to_publish = "ready_to_publish"


class Provider(StrEnum):
    codex = "codex"
    claude = "claude"
    gemini = "gemini"


class OutputFormat(StrEnum):
    markdown = "markdown"
    html = "html"


class SourceDocument(FrozenModel):
    id: str
    path: str
    category: str
    extension: str
    content: str


class SourceScanItem(FrozenModel):
    path: str
    category: str
    extension: str
    characters: int


class SourceScanResult(FrozenModel):
    items: list[SourceScanItem]
    excluded_files: int


class HealthResponse(FrozenModel):
    status: str


class IndexResponse(FrozenModel):
    processed_files: int
    failed_files: list[str]
    excluded_files: int


class GenerateRequest(FrozenModel):
    topic: str = Field(min_length=1)
    keywords: list[str] = Field(min_length=1)
    channel: str = Field(min_length=1)
    provider: Provider = Provider.codex


class Candidate(FrozenModel):
    id: str
    title: str
    summary: str
    body: str
    recommended_channel: str
    reference_summary: str


class QualityCheckItem(FrozenModel):
    name: str
    status: str
    detail: str


class GenerateResponse(FrozenModel):
    draft_id: int
    candidates: list[Candidate]
    search_summary: list[str]
    quality_checks: list[QualityCheckItem]
    cli_log_id: int


class ReviseRequest(FrozenModel):
    draft_id: int
    candidate_id: str
    tone: str = Field(min_length=1)
    revision_request: str = Field(min_length=1)


class ReviseResponse(FrozenModel):
    draft_id: int
    revised_body: str
    change_summary: str
    quality_checks: list[QualityCheckItem]
    cli_log_id: int


class ApproveRequest(FrozenModel):
    draft_id: int
    output_format: OutputFormat = OutputFormat.markdown


class ApproveResponse(FrozenModel):
    draft_id: int
    status: DraftStatus
    saved_path: str


class DraftListItem(FrozenModel):
    id: int
    topic: str
    channel: str
    status: DraftStatus
    updated_at: str


class DraftDetail(FrozenModel):
    id: int
    topic: str
    keywords: list[str]
    channel: str
    status: DraftStatus
    selected_candidate_id: str | None
    current_body: str
    revisions: list[str]
    quality_checks: list[QualityCheckItem]
    cli_logs: list[str]

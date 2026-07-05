from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from agent_server.app.database import initialize_database, mark_ready_to_publish
from agent_server.app.graph import CliWorkflowError, run_generate_workflow, run_revision_workflow
from agent_server.app.paths import OUTPUTS_DIR
from agent_server.app.repository import DraftMissingError, get_current_body, get_draft_detail, list_drafts
from agent_server.app.retriever import SourceFilesMissingError, index_sources
from agent_server.app.schemas import (
    ApproveRequest,
    ApproveResponse,
    DraftDetail,
    DraftListItem,
    DraftStatus,
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    IndexResponse,
    ReviseRequest,
    ReviseResponse,
)


def create_app() -> FastAPI:
    initialize_database()
    app = FastAPI(title="Content RAG Desktop Agent Server")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "tauri://localhost"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.post("/index", response_model=IndexResponse)
    def index() -> IndexResponse:
        try:
            processed_files, excluded_files = index_sources()
        except SourceFilesMissingError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error
        return IndexResponse(
            processed_files=processed_files,
            failed_files=[],
            excluded_files=excluded_files,
        )

    @app.post("/generate", response_model=GenerateResponse)
    def generate(payload: GenerateRequest) -> GenerateResponse:
        try:
            return run_generate_workflow(payload)
        except CliWorkflowError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "message": str(error),
                    "log_id": error.log_id,
                    "exit_code": error.result.exit_code,
                    "timed_out": error.result.timed_out,
                },
            ) from error

    @app.post("/revise", response_model=ReviseResponse)
    def revise(payload: ReviseRequest) -> ReviseResponse:
        try:
            current_body = get_current_body(payload.draft_id)
        except DraftMissingError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        return run_revision_workflow(payload, current_body)

    @app.post("/approve", response_model=ApproveResponse)
    def approve(payload: ApproveRequest) -> ApproveResponse:
        try:
            detail = get_draft_detail(payload.draft_id)
        except DraftMissingError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        saved_path = save_output_file(payload.draft_id, detail.current_body)
        mark_ready_to_publish(payload.draft_id)
        return ApproveResponse(
            draft_id=payload.draft_id,
            status=DraftStatus.ready_to_publish,
            saved_path=saved_path,
        )

    @app.get("/drafts", response_model=list[DraftListItem])
    def drafts() -> list[DraftListItem]:
        return list_drafts()

    @app.get("/drafts/{draft_id}", response_model=DraftDetail)
    def draft_detail(draft_id: int) -> DraftDetail:
        try:
            return get_draft_detail(draft_id)
        except DraftMissingError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error

    return app


def save_output_file(draft_id: int, body: str) -> str:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUTS_DIR / f"draft-{draft_id}.md"
    path.write_text(body, encoding="utf-8")
    return str(Path(path).resolve())


app = create_app()

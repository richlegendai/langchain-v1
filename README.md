# Tauri 콘텐츠 RAG 데스크톱 앱 MVP

프로젝트 내부 `data/sources/` 자료를 검색해 콘텐츠 후보 생성, 수정, 검수, Markdown 발행 준비까지 처리하는 로컬 데스크톱 앱 MVP입니다.

## 현재 구현 범위

- `data/sources/content/`, `data/sources/guidelines/`, `data/sources/references/` 샘플 자료
- `scripts/scan_sources.py` 자료 경로 감지
- FastAPI Agent Server
- Chroma 기반 `data/sources/` 인덱싱과 검색
- `codex`, `claude`, `gemini` CLI provider adapter
- LangGraph 기반 생성 workflow
- SQLite `data/app.sqlite` 초안, 수정 이력, CLI 로그 저장
- Tauri v2 + React UI
- Markdown 승인 파일 저장: `data/outputs/`

## 실행

```bash
uv sync
pnpm install
pnpm approve-builds --all
```

백엔드만 실행:

```bash
uv run uvicorn agent_server.app.main:app --host 127.0.0.1 --port 8000
```

프론트엔드만 실행:

```bash
pnpm dev
```

Tauri 앱 실행:

```bash
pnpm tauri dev
```

## 검증

```bash
uv run python scripts/scan_sources.py
uv run pytest agent_server/tests -q
pnpm build
pnpm exec biome check src vite.config.ts
cd src-tauri && cargo check
```

API smoke test:

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/index
```

## API

- `GET /health`
- `POST /index`
- `POST /generate`
- `POST /revise`
- `POST /approve`
- `GET /drafts`
- `GET /drafts/{id}`

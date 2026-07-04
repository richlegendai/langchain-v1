# Tauri 기반 콘텐츠 기획·수정·발행 RAG 데스크톱 앱 워크플로우

로컬에 로그인된 CLI 기반 LLM 도구를 직접 호출해야 하는 콘텐츠 자동화 앱을 Tauri 데스크톱 앱으로 구현하는 방향을 정리한 문서입니다.

대상 도구와 기술 스택은 Claude Code CLI, Codex CLI, Gemini CLI, Tauri, Rust, React, FastAPI, LangGraph, LangChain, Chroma, SQLite입니다.

## 결론

Claude Code 같은 로컬 CLI 기반 LLM 도구를 API가 아니라 사용자 MacBook의 로컬 인증 세션으로 호출해야 한다면, Vercel 웹앱보다 Tauri 기반 로컬 데스크톱 앱이 적합합니다.

권장 구조는 다음과 같습니다.

- Tauri + Rust: 데스크톱 앱 shell, 로컬 명령 실행, 파일 저장, 백엔드 프로세스 제어
- React: 주제 입력, 후보 비교, 말투 선택, 수정 요청, 검수 결과, 발행 상태 UI
- Python FastAPI: 로컬 Agent Server
- LangGraph: 콘텐츠 생성 워크플로우의 상태, 노드, 전환 관리
- LangChain: RAG 검색과 LLM 호출 체인 구성
- Chroma: 프로젝트 내부 콘텐츠 자료와 기준 문서의 벡터 검색
- SQLite: 초안, 수정 이력, 발행 상태, CLI 실행 로그 저장

## 프로젝트 한 줄 정의

프로젝트 내부에 저장한 로컬 콘텐츠 자료와 발행 기준을 Vector DB에 저장하고, Claude Code CLI 같은 로컬 LLM 도구를 호출하여 콘텐츠 후보 생성, 사용자 선택, 수정, 검수, 발행 준비까지 처리하는 Tauri 기반 콘텐츠 운영 데스크톱 앱입니다.

## 로컬 콘텐츠 자료 범위

RAG 검색과 콘텐츠 생성에 사용하는 원천 자료는 사용자 MacBook 전체가 아니라 이 프로젝트 폴더 안의 자료를 대상으로 합니다.

기본 위치는 다음과 같이 둡니다.

- `data/sources/content/`: 기존 콘텐츠, 블로그 초안, SNS 초안, 뉴스레터 초안
- `data/sources/guidelines/`: CTA 기준, 톤앤매너 예시, 발행 기준, 금지 표현, 검수 체크리스트
- `data/sources/references/`: 참고 자료, 제품 설명, 고객 사례, 조사 메모

앱은 위 폴더에 들어 있는 Markdown, HTML, TXT, CSV 같은 로컬 파일을 읽어 Chunking과 Embedding을 수행하고, Chroma Vector DB에 저장합니다. 프로젝트 밖의 Obsidian vault, 다운로드 폴더, 개인 문서 폴더는 사용자가 별도로 가져오거나 복사하지 않는 한 자동 수집 대상에 포함하지 않습니다.

## 로컬 데스크톱 앱이 맞는 이유

| 이유 | 설명 |
| --- | --- |
| CLI LLM 호출 | Claude Code CLI, Codex CLI, Gemini CLI처럼 로컬 인증 세션을 쓰는 도구를 직접 실행할 수 있습니다. |
| 로컬 파일 접근 | 프로젝트 내부 `data/sources/`에 저장한 Markdown, HTML, 기존 초안, CTA 기준, 발행 체크리스트를 직접 읽을 수 있습니다. |
| 로컬 Vector DB | Chroma 같은 Vector DB를 이 프로젝트의 `data/chroma_db/` 또는 앱 데이터 폴더에서 관리할 수 있습니다. |
| 데스크톱 UI | 후보 비교, 말투 선택, 수정 요청, 검수 결과, 발행 준비 상태를 로컬 앱 화면에서 안정적으로 관리할 수 있습니다. |

## 권장 아키텍처

| 구성 요소 | 역할 |
| --- | --- |
| Tauri Desktop App | 로컬 데스크톱 앱 shell입니다. React 화면과 Rust Command를 연결합니다. |
| React UI | 주제 입력, 후보 비교, 말투 선택, 수정 요청, 검수 결과, 발행 상태 화면을 제공합니다. |
| Rust Commands | 로컬 CLI 실행, 파일 저장, 로컬 FastAPI 서버 실행/중지, 경로 관리를 담당합니다. |
| Python FastAPI Agent Server | LangGraph, LangChain, Chroma, CLI LLM Adapter를 실행하는 로컬 백엔드입니다. |
| LangGraph Workflow | 주제 분석, 자료 검색, 후보 생성, 사용자 선택, 수정 반영, 검수, 발행 준비 상태를 관리합니다. |
| LangChain RAG Chain | 검색 자료와 프롬프트를 조합하고 LLM 호출 체인을 구성합니다. |
| Chroma + SQLite | Chroma는 RAG 검색용, SQLite는 초안/수정/발행 상태 저장용으로 사용합니다. |

## 전체 실행 흐름

```text
사용자 주제 입력
↓
Tauri React UI
↓
FastAPI Agent Server 호출
↓
LangGraph workflow 시작
↓
LangChain이 Chroma에서 프로젝트 내부 콘텐츠, CTA, 톤앤매너, 발행 기준 검색
↓
CLI LLM Adapter가 Claude Code CLI 또는 Codex CLI 호출
↓
콘텐츠 후보 3개 생성
↓
Tauri 화면에 후보 표시
↓
사용자가 후보 선택, 말투 선택, 수정 요청 입력
↓
LangGraph State에 선택값 저장
↓
CLI LLM으로 수정본 재생성
↓
검수 체크리스트 실행
↓
발행용 Markdown/HTML 생성
↓
SQLite에 초안, 수정 이력, 발행 상태 저장
```

## 핵심 용어

| 용어 | 설명 |
| --- | --- |
| RAG = Retrieval-Augmented Generation | 검색 증강 생성입니다. AI가 프로젝트 내부 콘텐츠와 기준 문서를 먼저 검색한 뒤 그 내용을 참고하여 결과를 생성하는 방식입니다. |
| Vector DB = Vector Database | 문서를 숫자 벡터로 저장하여 의미가 비슷한 자료를 찾는 데이터베이스입니다. |
| Embedding | 문서나 문장을 의미 검색이 가능한 숫자 벡터로 바꾸는 과정입니다. |
| CLI LLM Adapter | Claude Code CLI, Codex CLI 같은 로컬 명령어 기반 LLM 도구를 같은 방식으로 호출하기 위한 어댑터입니다. |
| LangGraph | State, Node, Edge로 Agent 흐름을 관리하는 프레임워크입니다. |
| Tauri | Rust 백엔드와 웹 프론트엔드를 결합하여 로컬 데스크톱 앱을 만드는 프레임워크입니다. |

## CLI LLM Adapter 설계

이 프로젝트의 핵심은 API 호출 대신 로컬 CLI 도구를 Agent 워크플로우 안에서 호출하는 것입니다.

```python
class LlmCliAdapter:
    def generate(self, prompt: str, provider: str) -> str:
        if provider == "claude-code":
            return run_command(["claude", "-p", prompt])

        if provider == "codex":
            return run_command(["codex", "exec", prompt])

        if provider == "gemini":
            return run_command(["gemini", prompt])

        raise ValueError("지원하지 않는 provider")
```

실제 구현에서는 다음 항목이 필요합니다.

- timeout 설정
- stdout/stderr 캡처
- 실패 재시도
- 실행 로그 저장
- 민감정보 마스킹
- provider별 명령어 경로 설정

## LangGraph Node 설계

```text
START
↓
analyze_topic
  - 주제, 키워드, 타깃 독자, 발행 채널 분석
↓
retrieve_context
  - 프로젝트 내부 콘텐츠, CTA 기준, 톤앤매너 예시, 발행 체크리스트 검색
↓
generate_candidates_with_cli
  - Claude Code CLI 또는 Codex CLI로 콘텐츠 후보 3개 생성
↓
wait_user_choice
  - 사용자가 Tauri 화면에서 후보 선택
↓
apply_revision
  - 말투 옵션과 수정 요청 반영
↓
regenerate_with_cli
  - 선택 후보 기준으로 수정본 재생성
↓
quality_check
  - 키워드, CTA, 금지 표현, 발행 기준 검수
↓
format_publish_draft
  - 블로그, SNS, 뉴스레터용 Markdown/HTML 생성
↓
save_local_state
  - SQLite에 초안, 수정 이력, 발행 상태 저장
↓
END 또는 apply_revision으로 반복
```

## 로컬 데이터 구조

| 저장소 | 역할 |
| --- | --- |
| Chroma | 프로젝트 내부 콘텐츠, CTA 기준, 톤앤매너 예시, 발행 체크리스트의 벡터 검색 저장소 |
| SQLite | 초안 후보, 선택 이력, 수정 요청, 발행 상태, CLI 실행 로그 저장 |
| Local Files | 발행용 Markdown, HTML, 최종 콘텐츠 파일 저장 |
| App Config | Claude Code CLI 경로, Codex CLI 경로, 데이터 폴더, 기본 모델 옵션 저장 |

## MVP 구현 범위

1. Tauri 화면 구성
   - 주제 입력
   - 후보 카드
   - 말투 선택
   - 수정 요청
   - 발행 상태
2. FastAPI 연결
   - `/generate`
   - `/revise`
   - `/approve`
   - `/drafts`
3. CLI 호출
   - `claude` 또는 `codex` 명령 실행
   - 실행 결과를 화면에 표시

## 최소 기능 목록

- 주제/키워드 입력
- 프로젝트 내부 콘텐츠와 CTA 기준 검색
- 콘텐츠 후보 3개 생성
- 후보 선택과 말투 선택
- 수정 요청 입력 후 재생성
- 검수 체크리스트 표시
- 발행용 Markdown/HTML 저장
- `draft`, `reviewing`, `ready_to_publish` 상태 관리

## 프로젝트 폴더 구조 예시

```text
content-rag-tauri-app/
├── src/
│   ├── pages-or-routes/
│   ├── components/
│   └── lib/api.ts
├── src-tauri/
│   ├── src/main.rs
│   ├── src/commands.rs
│   ├── capabilities/
│   └── tauri.conf.json
├── agent-server/
│   ├── app/main.py
│   ├── app/graph.py
│   ├── app/retriever.py
│   ├── app/llm_cli_adapter.py
│   ├── app/prompts.py
│   └── app/schemas.py
├── data/
│   ├── sources/
│   │   ├── content/
│   │   ├── guidelines/
│   │   └── references/
│   ├── chroma_db/
│   └── app.sqlite
└── README.md
```

## 이력서 삽입용 요약 문구

**Tauri 기반 콘텐츠 기획·수정·발행 RAG 데스크톱 앱**

- Tauri와 React 기반 데스크톱 UI에서 주제 입력, 후보 비교, 말투 선택, 수정 요청, 검수 결과, 발행 상태 관리 화면 구성
- 프로젝트 내부 콘텐츠와 CTA 기준, 톤앤매너 예시, 발행 체크리스트를 Chunking과 Embedding 처리 후 Chroma 기반 Vector DB에 저장
- FastAPI 기반 로컬 Agent Server에서 LangChain으로 문서 검색과 LLM 호출 체인을 구성하고, LangGraph로 주제 분석, 자료 검색, 후보 생성, 사용자 선택, 수정 요청 반영, 검수, 발행 준비 단계를 Node로 분리
- Rust Command와 Python subprocess를 통해 Claude Code CLI, Codex CLI 등 로컬 CLI 기반 LLM 도구를 콘텐츠 생성·수정 단계에 연결
- 최종 콘텐츠, 선택 이력, 수정 요청, 발행 채널, 발행 상태를 SQLite에 저장하여 반복 가능한 콘텐츠 운영 이력으로 관리

## 표현 수위 가이드

### 실험 후 안전한 표현

- Tauri 기반 RAG 콘텐츠 데스크톱 앱 프로토타입 구현
- Claude Code CLI 등 로컬 LLM 도구를 호출하는 콘텐츠 생성·수정 워크플로우 구성
- Chroma 기반 콘텐츠 자료 검색과 LangGraph 기반 사용자 선택형 수정 흐름 구현

### 실제 구현 전에는 피할 표현

- 상용 데스크톱 앱 출시
- 완전 자동 발행 운영
- 다중 LLM CLI 안정 운영 완료

## 참고 원문

- `Tauri 기반 콘텐츠 기획·수정·발행 RAG 데스크톱 앱 워크플로우.html`
- 이 README는 원본 HTML의 내용을 마크다운 문서로 재구성한 정리본입니다.

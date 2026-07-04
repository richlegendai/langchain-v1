# Chroma 단독 체험 실습 계획

## Summary

Chroma를 직접 설치하고, 샘플 문서 5개를 Vector DB에 저장한 뒤, 질문으로 유사 문서를 검색해보는 최소 실습을 진행합니다. LangChain, LangGraph, Codex CLI는 아직 붙이지 않고, 먼저 “문장을 벡터로 저장하면 의미 기반 검색이 된다”는 감각만 확인합니다.

## 실습 흐름

1. 현재 폴더에서 Python 프로젝트를 초기화합니다.
   ```bash
   uv init --app --python 3.12 .
   ```

2. Chroma를 설치합니다.
   ```bash
   uv add chromadb
   ```

3. `main.py`에 아래 역할만 넣습니다.
   - Chroma `PersistentClient` 생성
   - `./chroma_db` 경로에 로컬 DB 저장
   - `quickstart_docs` collection 생성
   - 샘플 문서 5개 저장
   - 사용자 질문 1개로 유사 문서 3개 검색
   - 결과에 `id`, `topic`, `distance`, `document` 출력

4. 샘플 문서 5개는 처음에는 아주 짧게 둡니다.
   - LangChain은 문서 로딩, 분할, 검색 흐름을 도와준다.
   - LangGraph는 여러 단계를 상태 그래프로 연결한다.
   - Chroma는 텍스트와 메타데이터를 저장하고 유사도 검색을 제공한다.
   - Vector DB는 정확한 키워드보다 의미가 가까운 문서를 찾는 데 유리하다.
   - RAG는 검색된 문맥을 LLM 답변에 넣어 근거 있는 답변을 만든다.

5. 실행 명령은 하나로 고정합니다.
   ```bash
   uv run python main.py "LangGraph는 언제 쓰면 좋아?"
   ```

6. 기대 결과는 `LangGraph`, `workflow`, `state graph`와 관련된 문서가 상위에 나오는 것입니다. 같은 방식으로 `"Vector DB는 왜 필요해?"`, `"RAG가 뭐야?"`를 바꿔 입력하며 검색 결과가 달라지는 것을 확인합니다.

## Key Changes

- 새 파일은 최소 3개만 둡니다.
  - `pyproject.toml`: `uv init`과 `uv add chromadb`로 생성
  - `main.py`: Chroma 저장과 검색 실습 코드
  - `.gitignore`: `.venv/`, `chroma_db/`, `__pycache__/` 제외

- Chroma API는 공식 Cookbook의 `PersistentClient`, `get_or_create_collection`, `upsert`, `query` 흐름을 사용합니다.
- Python은 현재 `3.14.6`도 있으나, 실습 안정성을 위해 `3.12`를 기본값으로 둡니다.

## Test Plan

- 설치 확인:
  ```bash
  uv run python -c "import chromadb; print(chromadb.__version__)"
  ```

- 저장과 검색 확인:
  ```bash
  uv run python main.py "Vector DB는 왜 필요해?"
  ```

- 재실행 확인:
  ```bash
  uv run python main.py "RAG가 뭐야?"
  ```
  `./chroma_db`가 유지되므로 두 번째 실행에서도 같은 collection을 재사용해야 합니다.

- 실패 시 확인:
  - `chromadb` import 실패: `uv add chromadb` 재실행
  - Python 버전 문제: `uv python install 3.12` 후 `uv venv --python 3.12`
  - DB 초기화가 꼬인 경우: 학습용이므로 `rm -rf chroma_db` 후 재실행

## Assumptions

- 첫 목표는 “Vector DB 체감”이므로 LangChain과 LangGraph는 제외합니다.
- 임베딩 모델은 Chroma 기본 동작을 먼저 사용합니다.
- 웹 UI 없이 CLI로만 진행합니다.
- Chroma 로컬 저장소는 `./chroma_db`로 고정합니다.
- 다음 단계에서 LangChain retriever, 그다음 LangGraph workflow로 확장합니다.

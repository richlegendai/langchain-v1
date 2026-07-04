import sys
from typing import Final

import chromadb


DB_PATH: Final[str] = "./chroma_db"
COLLECTION_NAME: Final[str] = "quickstart_docs"

DOCUMENT_IDS: Final[list[str]] = [
    "langchain",
    "langgraph",
    "chroma",
    "vector-db",
    "rag",
]

DOCUMENTS: Final[list[str]] = [
    "LangChain은 문서 로딩, 텍스트 분할, 검색기 연결, 프롬프트 구성을 도와주는 LLM 애플리케이션 프레임워크입니다.",
    "LangGraph는 여러 처리 단계를 상태 그래프로 연결해 검색, 생성, 검수, 재시도 같은 워크플로우를 만들 때 유용합니다.",
    "Chroma는 텍스트와 메타데이터를 로컬에 저장하고 질문과 의미가 가까운 문서를 찾아주는 Vector DB입니다.",
    "Vector DB는 정확히 같은 키워드가 없어도 의미가 가까운 문서를 찾는 데 강점이 있습니다.",
    "RAG는 Vector DB에서 찾은 관련 문맥을 LLM에게 함께 전달해 더 근거 있는 답변을 만들게 하는 방식입니다.",
]

METADATAS: Final[list[dict[str, str]]] = [
    {"topic": "langchain"},
    {"topic": "langgraph"},
    {"topic": "chroma"},
    {"topic": "vector-db"},
    {"topic": "rag"},
]


def main() -> None:
    query = " ".join(sys.argv[1:]).strip()

    if not query:
        print('사용법: uv run python main.py "Vector DB는 왜 필요해?"')
        raise SystemExit(1)

    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    collection.upsert(
        ids=DOCUMENT_IDS,
        documents=DOCUMENTS,
        metadatas=METADATAS,
    )

    result = collection.query(
        query_texts=[query],
        n_results=3,
        include=["documents", "metadatas", "distances"],
    )

    print(f"질문: {query}")
    print()

    ids = result["ids"][0]
    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    distances = result["distances"][0]

    for index, document_id in enumerate(ids, start=1):
        metadata = metadatas[index - 1]
        distance = distances[index - 1]
        document = documents[index - 1]

        print(f"{index}. id={document_id}")
        print(f"   topic={metadata['topic']}")
        print(f"   distance={distance:.4f}")
        print(f"   document={document}")
        print()


if __name__ == "__main__":
    main()

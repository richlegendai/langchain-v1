import sys
from pathlib import Path
from typing import Final

import chromadb


DB_PATH: Final[str] = "./chroma_db"
COLLECTION_NAME: Final[str] = "quickstart_docs"
DOCS_DIR: Final[Path] = Path("docs")

type Metadata = dict[str, str]


def load_documents(docs_dir: Path) -> tuple[list[str], list[str], list[Metadata]]:
    paths = sorted(docs_dir.glob("*.md"))

    if not paths:
        print(f"문서가 없습니다: {docs_dir}")
        raise SystemExit(1)

    ids = [path.stem for path in paths]
    documents = [path.read_text(encoding="utf-8").strip() for path in paths]
    metadatas = [{"topic": path.stem, "source": str(path)} for path in paths]

    return ids, documents, metadatas


def main() -> None:
    query = " ".join(sys.argv[1:]).strip()

    if not query:
        print('사용법: uv run python main.py "Vector DB는 왜 필요해?"')
        raise SystemExit(1)

    document_ids, documents, metadatas = load_documents(DOCS_DIR)

    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    collection.upsert(
        ids=document_ids,
        documents=documents,
        metadatas=metadatas,
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
        print(f"   source={metadata['source']}")
        print(f"   distance={distance:.4f}")
        print(f"   document={document}")
        print()


if __name__ == "__main__":
    main()

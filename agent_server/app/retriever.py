from pathlib import Path
from typing import Final

import chromadb

from agent_server.app.paths import CHROMA_DIR, SOURCES_DIR
from agent_server.app.schemas import SourceDocument, SourceScanItem, SourceScanResult


SUPPORTED_EXTENSIONS: Final[frozenset[str]] = frozenset({".md", ".html", ".txt", ".csv"})
COLLECTION_NAME: Final[str] = "content_sources"


class SourceFilesMissingError(RuntimeError):
    def __init__(self, sources_dir: Path) -> None:
        super().__init__(f"지원 파일이 없습니다: {sources_dir}")


def scan_sources(sources_dir: Path = SOURCES_DIR) -> SourceScanResult:
    documents, excluded_files = load_source_documents(sources_dir)
    items = [
        SourceScanItem(
            path=document.path,
            category=document.category,
            extension=document.extension,
            characters=len(document.content),
        )
        for document in documents
    ]
    return SourceScanResult(items=items, excluded_files=excluded_files)


def load_source_documents(sources_dir: Path = SOURCES_DIR) -> tuple[list[SourceDocument], int]:
    documents: list[SourceDocument] = []
    excluded_files = 0

    for path in sorted(sources_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            excluded_files += 1
            continue

        relative_path = path.relative_to(sources_dir)
        category = relative_path.parts[0] if len(relative_path.parts) > 1 else "uncategorized"
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            excluded_files += 1
            continue

        documents.append(
            SourceDocument(
                id=relative_path.as_posix(),
                path=str(path),
                category=category,
                extension=path.suffix.lower(),
                content=content,
            )
        )

    if not documents:
        raise SourceFilesMissingError(sources_dir)

    return documents, excluded_files


def index_sources(sources_dir: Path = SOURCES_DIR) -> tuple[int, int]:
    documents, excluded_files = load_source_documents(sources_dir)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    collection.upsert(
        ids=[document.id for document in documents],
        documents=[document.content for document in documents],
        metadatas=[
            {
                "path": document.path,
                "category": document.category,
                "extension": document.extension,
            }
            for document in documents
        ],
    )
    return len(documents), excluded_files


def search_context(query: str, n_results: int = 3) -> list[str]:
    index_sources()
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    result = collection.query(query_texts=[query], n_results=n_results, include=["documents"])
    documents = result["documents"][0]
    return [str(document) for document in documents]

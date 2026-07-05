from fastapi.testclient import TestClient

from agent_server.app.main import app
from agent_server.app.retriever import scan_sources
from agent_server.app.schemas import Provider


def test_scan_sources_detects_seed_documents() -> None:
    result = scan_sources()

    categories = {item.category for item in result.items}

    assert {"content", "guidelines", "references"}.issubset(categories)


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_index_endpoint_returns_processed_files() -> None:
    client = TestClient(app)

    response = client.post("/index")

    assert response.status_code == 200
    payload = response.json()
    assert payload["processed_files"] >= 3
    assert payload["failed_files"] == []


def test_unsupported_provider_is_rejected_by_schema() -> None:
    client = TestClient(app)

    response = client.post(
        "/generate",
        json={
            "topic": "RAG 콘텐츠 운영",
            "keywords": ["RAG"],
            "channel": "blog",
            "provider": "unsupported",
        },
    )

    assert response.status_code == 422


def test_provider_enum_contains_codex() -> None:
    assert Provider.codex.value == "codex"

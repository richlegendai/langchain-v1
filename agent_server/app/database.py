import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from agent_server.app.paths import SQLITE_PATH
from agent_server.app.schemas import DraftStatus, QualityCheckItem


@contextmanager
def connect_database(path: Path = SQLITE_PATH) -> Iterator[sqlite3.Connection]:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database() -> None:
    with connect_database() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                keywords TEXT NOT NULL,
                channel TEXT NOT NULL,
                status TEXT NOT NULL,
                candidates TEXT NOT NULL,
                selected_candidate_id TEXT,
                current_body TEXT NOT NULL,
                quality_checks TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS revisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                draft_id INTEGER NOT NULL,
                body TEXT NOT NULL,
                request TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (draft_id) REFERENCES drafts(id)
            );
            CREATE TABLE IF NOT EXISTS cli_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                prompt TEXT NOT NULL,
                stdout TEXT NOT NULL,
                stderr TEXT NOT NULL,
                exit_code INTEGER NOT NULL,
                timed_out INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def create_cli_log(
    provider: str,
    prompt: str,
    stdout: str,
    stderr: str,
    exit_code: int,
    timed_out: bool,
) -> int:
    initialize_database()
    with connect_database() as connection:
        cursor = connection.execute(
            """
            INSERT INTO cli_logs (provider, prompt, stdout, stderr, exit_code, timed_out)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (provider, prompt, stdout, stderr, exit_code, int(timed_out)),
        )
        return int(cursor.lastrowid)


def create_draft(
    topic: str,
    keywords: list[str],
    channel: str,
    candidates_json: str,
    current_body: str,
    quality_checks: list[QualityCheckItem],
) -> int:
    initialize_database()
    with connect_database() as connection:
        cursor = connection.execute(
            """
            INSERT INTO drafts (
                topic, keywords, channel, status, candidates, current_body, quality_checks
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                topic,
                json.dumps(keywords, ensure_ascii=False),
                channel,
                DraftStatus.draft.value,
                candidates_json,
                current_body,
                json.dumps([item.model_dump() for item in quality_checks], ensure_ascii=False),
            ),
        )
        return int(cursor.lastrowid)


def update_draft_revision(
    draft_id: int,
    candidate_id: str,
    body: str,
    request: str,
    quality_checks: list[QualityCheckItem],
) -> None:
    initialize_database()
    with connect_database() as connection:
        connection.execute(
            """
            UPDATE drafts
            SET selected_candidate_id = ?,
                current_body = ?,
                status = ?,
                quality_checks = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                candidate_id,
                body,
                DraftStatus.reviewing.value,
                json.dumps([item.model_dump() for item in quality_checks], ensure_ascii=False),
                draft_id,
            ),
        )
        connection.execute(
            """
            INSERT INTO revisions (draft_id, body, request)
            VALUES (?, ?, ?)
            """,
            (draft_id, body, request),
        )


def mark_ready_to_publish(draft_id: int) -> None:
    initialize_database()
    with connect_database() as connection:
        connection.execute(
            """
            UPDATE drafts
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (DraftStatus.ready_to_publish.value, draft_id),
        )

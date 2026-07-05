import json

from agent_server.app.database import connect_database, initialize_database
from agent_server.app.schemas import DraftDetail, DraftListItem, DraftStatus, QualityCheckItem


class DraftMissingError(RuntimeError):
    def __init__(self, draft_id: int) -> None:
        super().__init__(f"초안을 찾을 수 없습니다: {draft_id}")


def list_drafts() -> list[DraftListItem]:
    initialize_database()
    with connect_database() as connection:
        rows = connection.execute(
            """
            SELECT id, topic, channel, status, updated_at
            FROM drafts
            ORDER BY updated_at DESC
            """
        ).fetchall()
    return [
        DraftListItem(
            id=int(row["id"]),
            topic=str(row["topic"]),
            channel=str(row["channel"]),
            status=DraftStatus(str(row["status"])),
            updated_at=str(row["updated_at"]),
        )
        for row in rows
    ]


def get_draft_detail(draft_id: int) -> DraftDetail:
    initialize_database()
    with connect_database() as connection:
        row = connection.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        if row is None:
            raise DraftMissingError(draft_id)
        revision_rows = connection.execute(
            "SELECT request || ': ' || body AS entry FROM revisions WHERE draft_id = ? ORDER BY id",
            (draft_id,),
        ).fetchall()
        log_rows = connection.execute(
            "SELECT provider || ' exit=' || exit_code || ' timeout=' || timed_out AS entry FROM cli_logs ORDER BY id",
        ).fetchall()

    keywords_raw = json.loads(str(row["keywords"]))
    checks_raw = json.loads(str(row["quality_checks"]))
    return DraftDetail(
        id=int(row["id"]),
        topic=str(row["topic"]),
        keywords=[str(keyword) for keyword in keywords_raw],
        channel=str(row["channel"]),
        status=DraftStatus(str(row["status"])),
        selected_candidate_id=(
            str(row["selected_candidate_id"]) if row["selected_candidate_id"] is not None else None
        ),
        current_body=str(row["current_body"]),
        revisions=[str(revision["entry"]) for revision in revision_rows],
        quality_checks=[QualityCheckItem.model_validate(check) for check in checks_raw],
        cli_logs=[str(log["entry"]) for log in log_rows],
    )


def get_current_body(draft_id: int) -> str:
    initialize_database()
    with connect_database() as connection:
        row = connection.execute("SELECT current_body FROM drafts WHERE id = ?", (draft_id,)).fetchone()
    if row is None:
        raise DraftMissingError(draft_id)
    return str(row["current_body"])

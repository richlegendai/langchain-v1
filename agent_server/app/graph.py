import json
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from agent_server.app.database import create_cli_log, create_draft, update_draft_revision
from agent_server.app.llm_cli_adapter import CliResult, generate_with_cli
from agent_server.app.quality import run_quality_checks
from agent_server.app.retriever import search_context
from agent_server.app.schemas import Candidate, GenerateRequest, GenerateResponse, ReviseRequest, ReviseResponse


class WorkflowState(TypedDict):
    topic: str
    keywords: list[str]
    channel: str
    provider: str
    context: list[str]
    prompt: str
    cli_stdout: str
    cli_stderr: str
    cli_exit_code: int
    cli_timed_out: bool
    candidates: list[Candidate]
    search_summary: list[str]


class CliWorkflowError(RuntimeError):
    def __init__(self, result: CliResult, log_id: int) -> None:
        super().__init__(result.stderr or "CLI 실행에 실패했습니다.")
        self.result = result
        self.log_id = log_id


def analyze_topic(state: WorkflowState) -> WorkflowState:
    return state


def retrieve_context(state: WorkflowState) -> WorkflowState:
    query = f"{state['topic']} {' '.join(state['keywords'])} {state['channel']}"
    context = search_context(query)
    return {**state, "context": context, "search_summary": context}


def generate_candidates_with_cli(state: WorkflowState) -> WorkflowState:
    prompt = build_generate_prompt(state)
    result = generate_with_cli(prompt=prompt, provider=GenerateRequest.model_validate(state).provider)
    return {
        **state,
        "prompt": prompt,
        "cli_stdout": result.stdout,
        "cli_stderr": result.stderr,
        "cli_exit_code": result.exit_code,
        "cli_timed_out": result.timed_out,
    }


def format_candidates(state: WorkflowState) -> WorkflowState:
    candidates = build_candidates_from_text(
        topic=state["topic"],
        channel=state["channel"],
        context=state["context"],
        generated_text=state["cli_stdout"],
    )
    return {**state, "candidates": candidates}


def build_generate_graph():
    graph = StateGraph(WorkflowState)
    graph.add_node("analyze_topic", analyze_topic)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("generate_candidates_with_cli", generate_candidates_with_cli)
    graph.add_node("format_candidates", format_candidates)
    graph.add_edge(START, "analyze_topic")
    graph.add_edge("analyze_topic", "retrieve_context")
    graph.add_edge("retrieve_context", "generate_candidates_with_cli")
    graph.add_edge("generate_candidates_with_cli", "format_candidates")
    graph.add_edge("format_candidates", END)
    return graph.compile()


def run_generate_workflow(payload: GenerateRequest) -> GenerateResponse:
    graph = build_generate_graph()
    state = graph.invoke(
        {
            "topic": payload.topic,
            "keywords": payload.keywords,
            "channel": payload.channel,
            "provider": payload.provider.value,
            "context": [],
            "prompt": "",
            "cli_stdout": "",
            "cli_stderr": "",
            "cli_exit_code": 0,
            "cli_timed_out": False,
            "candidates": [],
            "search_summary": [],
        }
    )
    log_id = create_cli_log(
        provider=payload.provider.value,
        prompt=str(state["prompt"]),
        stdout=str(state["cli_stdout"]),
        stderr=str(state["cli_stderr"]),
        exit_code=int(state["cli_exit_code"]),
        timed_out=bool(state["cli_timed_out"]),
    )
    if int(state["cli_exit_code"]) != 0:
        raise CliWorkflowError(
            CliResult(
                stdout=str(state["cli_stdout"]),
                stderr=str(state["cli_stderr"]),
                exit_code=int(state["cli_exit_code"]),
                timed_out=bool(state["cli_timed_out"]),
            ),
            log_id,
        )

    candidates = list(state["candidates"])
    current_body = candidates[0].body if candidates else ""
    checks = run_quality_checks(current_body, payload.keywords)
    draft_id = create_draft(
        topic=payload.topic,
        keywords=payload.keywords,
        channel=payload.channel,
        candidates_json=json.dumps([candidate.model_dump() for candidate in candidates], ensure_ascii=False),
        current_body=current_body,
        quality_checks=checks,
    )
    return GenerateResponse(
        draft_id=draft_id,
        candidates=candidates,
        search_summary=[str(item) for item in state["search_summary"]],
        quality_checks=checks,
        cli_log_id=log_id,
    )


def run_revision_workflow(payload: ReviseRequest, current_body: str) -> ReviseResponse:
    revised_body = "\n\n".join(
        [
            current_body,
            f"수정 말투: {payload.tone}",
            f"수정 요청 반영: {payload.revision_request}",
        ]
    )
    checks = run_quality_checks(revised_body, [])
    log_id = create_cli_log(
        provider="local-rule",
        prompt=payload.revision_request,
        stdout=revised_body,
        stderr="",
        exit_code=0,
        timed_out=False,
    )
    update_draft_revision(
        draft_id=payload.draft_id,
        candidate_id=payload.candidate_id,
        body=revised_body,
        request=payload.revision_request,
        quality_checks=checks,
    )
    return ReviseResponse(
        draft_id=payload.draft_id,
        revised_body=revised_body,
        change_summary="선택 후보에 말투와 수정 요청을 덧붙였습니다.",
        quality_checks=checks,
        cli_log_id=log_id,
    )


def build_generate_prompt(state: WorkflowState) -> str:
    context_text = "\n\n".join(state["context"])
    return (
        "한국어 콘텐츠 후보 3개를 생성하세요. "
        "각 후보는 제목, 요약, 본문, 추천 채널, 참고 자료 요약을 포함하세요.\n"
        f"주제: {state['topic']}\n"
        f"키워드: {', '.join(state['keywords'])}\n"
        f"채널: {state['channel']}\n"
        f"프로젝트 내부 참고 자료:\n{context_text}"
    )


def build_candidates_from_text(
    topic: str,
    channel: str,
    context: list[str],
    generated_text: str,
) -> list[Candidate]:
    reference_summary = " / ".join(item.splitlines()[0][:80] for item in context if item)
    body = generated_text.strip()
    return [
        Candidate(
            id=f"candidate-{index}",
            title=f"{topic} 후보 {index}",
            summary=f"{topic}에 대한 {channel}용 콘텐츠 후보입니다.",
            body=body,
            recommended_channel=channel,
            reference_summary=reference_summary,
        )
        for index in range(1, 4)
    ]

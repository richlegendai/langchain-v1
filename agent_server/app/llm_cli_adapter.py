import re
import subprocess
from dataclasses import dataclass
from typing import Final

from agent_server.app.schemas import Provider


SECRET_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"(?i)(api[_-]?key|token|secret|password)=\S+"),
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
)


@dataclass(frozen=True, slots=True)
class CliResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool


class UnsupportedProviderError(RuntimeError):
    def __init__(self, provider: str) -> None:
        super().__init__(f"지원하지 않는 provider입니다: {provider}")


def mask_sensitive(value: str) -> str:
    masked = value
    for pattern in SECRET_PATTERNS:
        masked = pattern.sub("[REDACTED]", masked)
    return masked


def command_for_provider(provider: Provider, prompt: str) -> list[str]:
    match provider:
        case Provider.codex:
            return ["codex", "exec", "--sandbox", "read-only", "--ephemeral", prompt]
        case Provider.claude:
            return ["claude", "-p", prompt]
        case Provider.gemini:
            return ["gemini", prompt]


def generate_with_cli(prompt: str, provider: Provider, timeout_seconds: int = 120) -> CliResult:
    command = command_for_provider(provider, prompt)
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            stdin=subprocess.DEVNULL,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout if isinstance(error.stdout, str) else ""
        stderr = error.stderr if isinstance(error.stderr, str) else "CLI 실행 시간이 초과됐습니다."
        return CliResult(
            stdout=mask_sensitive(stdout),
            stderr=mask_sensitive(stderr),
            exit_code=124,
            timed_out=True,
        )
    except FileNotFoundError as error:
        return CliResult(
            stdout="",
            stderr=mask_sensitive(str(error)),
            exit_code=127,
            timed_out=False,
        )

    return CliResult(
        stdout=mask_sensitive(completed.stdout),
        stderr=mask_sensitive(completed.stderr),
        exit_code=completed.returncode,
        timed_out=False,
    )

from agent_server.app.schemas import QualityCheckItem


FORBIDDEN_PHRASES = ("무조건 성공", "100% 보장", "즉시 수익")


def run_quality_checks(body: str, keywords: list[str]) -> list[QualityCheckItem]:
    missing_keywords = [keyword for keyword in keywords if keyword not in body]
    forbidden_hits = [phrase for phrase in FORBIDDEN_PHRASES if phrase in body]
    return [
        QualityCheckItem(
            name="키워드",
            status="pass" if not missing_keywords else "warning",
            detail="모든 키워드 포함" if not missing_keywords else ", ".join(missing_keywords),
        ),
        QualityCheckItem(
            name="CTA",
            status="pass" if "다음" in body or "확인" in body else "warning",
            detail="CTA 단서 확인" if "다음" in body or "확인" in body else "CTA 문장 보강 필요",
        ),
        QualityCheckItem(
            name="금지 표현",
            status="pass" if not forbidden_hits else "fail",
            detail="금지 표현 없음" if not forbidden_hits else ", ".join(forbidden_hits),
        ),
    ]

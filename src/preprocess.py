import re


ROLE_ALIASES = {
    "마케팅 팀장": "팀장",
    "퍼포먼스 마케터": "퍼포먼스 마케터",
    "콘텐츠 디자이너": "콘텐츠 디자이너",
}

TERM_ALIASES = {
    "GA": "Google Analytics",
    "A/B": "A/B 테스트",
    "CTA": "CTA",
    "ROAS": "ROAS",
    "CPM": "CPM",
}

FILLER_PATTERN = r"(^|[\s,])(?:어|음|아|자)(?=[\s,….])[\s,….]*"


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalize_speaker(speaker: str | None) -> str:
    if not speaker:
        return "unknown"
    return normalize_whitespace(speaker)


def normalize_role(role: str | None) -> str:
    if not role:
        return ""
    normalized = normalize_whitespace(role)
    return ROLE_ALIASES.get(normalized, normalized)


def normalize_terms(text: str) -> str:
    normalized = text
    for source, target in TERM_ALIASES.items():
        normalized = re.sub(rf"\b{re.escape(source)}\b", target, normalized)
    return normalized


def remove_fillers(text: str) -> str:
    return re.sub(FILLER_PATTERN, r"\1", text)


def normalize_text(text: str | None) -> str:
    if not text:
        return ""

    normalized = text.replace("…", " ")
    normalized = normalize_terms(normalized)
    normalized = remove_fillers(normalized)
    normalized = normalize_whitespace(normalized)
    normalized = re.sub(r"\s+([,.?!])", r"\1", normalized)
    return normalized

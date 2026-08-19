from __future__ import annotations

import re
from typing import Optional

from app.models.schemas import CertificateFields


DATE_PATTERNS = [
    r"\b(?:0?[1-9]|[12]\d|3[01])[/-](?:0?[1-9]|1[0-2])[/-](?:19|20)\d{2}\b",
    r"\b(?:19|20)\d{2}[/-](?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])\b",
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+(?:19|20)\d{2}\b",
    r"\b\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(?:19|20)\d{2}\b",
]


def _clean(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    value = re.sub(r"[ \t]+", " ", value)
    value = value.strip(" :-|,\n\t")

    return value or None


def _search(
    patterns: list[str],
    text: str,
    flags=re.IGNORECASE,
) -> Optional[str]:

    for pattern in patterns:
        match = re.search(pattern, text, flags)

        if match:
            if match.groups():
                return _clean(match.group(1))
            return _clean(match.group(0))

    return None


def _looks_like_name(value: str) -> bool:
    value = _clean(value)

    if not value:
        return False

    words = value.split()

    if not 2 <= len(words) <= 5:
        return False

    if any(ch.isdigit() for ch in value):
        return False

    blocked = {
        "certificate",
        "participation",
        "completion",
        "achievement",
        "international",
        "designers",
        "engineers",
        "alliance",
        "presented",
        "proudly",
        "attending",
        "participating",
    }

    for word in words:
        if word.lower().strip(".,:;") in blocked:
            return False

    return True


def _candidate_name(
    lines: list[str],
    text: str,
) -> Optional[str]:

    triggers = [
        "presented to",
        "proudly presented to",
        "certifies that",
        "awarded to",
        "recipient",
        "candidate",
        "student",
    ]

    # Best method:
    # take ONLY the next OCR line after a trigger phrase.
    for index, line in enumerate(lines):
        low = line.lower()

        if any(trigger in low for trigger in triggers):

            for offset in range(1, 3):
                next_index = index + offset

                if next_index >= len(lines):
                    break

                candidate = _clean(lines[next_index])

                if candidate and _looks_like_name(candidate):
                    return candidate

    # Same-line fallback
    patterns = [
        r"(?:presented\s+to|awarded\s+to|certifies\s+that)\s*[:\-]?[ \t]+([A-Z][A-Za-z.'-]+(?:[ \t]+[A-Z][A-Za-z.'-]+){1,4})",
        r"(?:candidate|student|recipient)\s*[:\-][ \t]*([A-Z][A-Za-z.'-]+(?:[ \t]+[A-Z][A-Za-z.'-]+){1,4})",
    ]

    result = _search(
        patterns,
        text,
        flags=re.IGNORECASE,
    )

    if result and _looks_like_name(result):
        return result

    return None


def _certificate_title(
    lines: list[str],
    text: str,
) -> Optional[str]:

    # Prefer the actual course/program title.
    # Example:
    # has successfully completed the
    # Machine Learning Fundamentals
    lines_lower = [line.lower() for line in lines]

    for index, line in enumerate(lines_lower):

        if "successfully completed" in line:

            # Text may be on same line
            match = re.search(
                r"successfully\s+completed\s+(?:the\s+)?(.+)",
                lines[index],
                re.IGNORECASE,
            )

            if match:
                value = _clean(match.group(1))

                if value and len(value) > 3:
                    return value

            # Or course title may be on next line
            if index + 1 < len(lines):
                next_line = _clean(lines[index + 1])

                if next_line:
                    return next_line

    lowered = text.lower()

    if re.search(
        r"certificate[\s\S]{0,80}participation",
        lowered,
    ):
        return "Certificate of Participation"

    if re.search(
        r"certificate[\s\S]{0,80}completion",
        lowered,
    ):
        return "Certificate of Completion"

    if re.search(
        r"certificate[\s\S]{0,80}achievement",
        lowered,
    ):
        return "Certificate of Achievement"

    if re.search(
        r"certificate[\s\S]{0,80}appreciation",
        lowered,
    ):
        return "Certificate of Appreciation"

    return None


def _organization(
    lines: list[str],
    text: str,
) -> Optional[str]:

    explicit = _search(
        [
            r"(?:organization|organisation|institution|issued\s+by|issuer)\s*[:\-]\s*([^\n]+)",
        ],
        text,
    )

    if explicit:
        return explicit

    # Multi-line IDEA organization
    for index, line in enumerate(lines):

        low = line.lower()

        if "international designers" in low:

            start = low.find("international designers")
            organization = line[start:]

            if index + 1 < len(lines):
                next_line = lines[index + 1]
                next_low = next_line.lower()

                if "engineers alliance" in next_low:
                    start2 = next_low.find("engineers alliance")
                    organization += " " + next_line[start2:]

            nearby = " ".join(
                lines[max(0, index - 2): index + 1]
            ).lower()

            if "idea" in nearby:
                organization = "IDEA | " + organization

            return _clean(organization)

    keywords = (
        "university",
        "institute",
        "college",
        "academy",
        "school",
        "limited",
        "ltd",
        "pvt",
        "foundation",
        "alliance",
        "association",
        "company",
        "corporation",
    )

    for line in lines:
        low = line.lower()

        if (
            any(keyword in low for keyword in keywords)
            and len(line) < 150
        ):
            return _clean(line)

    return None


def _issue_date(text: str) -> Optional[str]:

    for pattern in DATE_PATTERNS:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            return _clean(match.group(0))

    return None


def _certificate_number(text: str) -> Optional[str]:

    # Only accept a number when an ID/number label is present.
    labeled = _search(
        [
            r"(?:certificate\s*(?:id|no\.?|number)|cert\.?\s*no\.?|serial\s*(?:no\.?|number)|credential\s*(?:id|no\.?)|registration\s*(?:id|no\.?))\s*[:#\-]?\s*([A-Z0-9][A-Z0-9/_\-]{3,})",
        ],
        text,
    )

    if labeled:
        return labeled

    # Safe fallback for IDs such as TEEROP-2026-001.
    fallback = re.search(
        r"\b([A-Z]{2,15}-\d{2,4}-[A-Z0-9\-]{2,})\b",
        text,
        re.IGNORECASE,
    )

    if fallback:
        return _clean(fallback.group(1))

    return None


def _grade_score(text: str) -> Optional[str]:

    return _search(
        [
            r"(?:grade|score|marks?|percentage|cgpa|gpa)\s*[:\-]?\s*([A-Z0-9.+/%-]+(?:\s+out\s+of\s+[A-Z0-9.]+)?)",
        ],
        text,
    )


def _duration(text: str) -> Optional[str]:

    return _search(
        [
            r"(?:duration|course\s+duration|program\s+duration)\s*[:\-]?\s*([^\n]+)",
            r"\b((?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|twelve)\s+(?:day|days|week|weeks|month|months|year|years|hour|hours))\b",
        ],
        text,
    )


def parse_certificate_fields(
    raw_text: str,
) -> CertificateFields:

    text = raw_text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    lines = []

    for line in text.splitlines():

        cleaned = _clean(line)

        if not cleaned:
            continue

        if cleaned.startswith("--- Page"):
            continue

        lines.append(cleaned)

    fields = CertificateFields(
        candidate_name=_candidate_name(lines, text),
        certificate_title=_certificate_title(lines, text),
        organization_name=_organization(lines, text),
        issue_date=_issue_date(text),
        certificate_number=_certificate_number(text),
        grade_score=_grade_score(text),
        duration=_duration(text),
        additional_fields={},
    )

    lowered = text.lower()

    if "completion" in lowered:
        fields.additional_fields["certificate_type"] = "Completion"

    elif "achievement" in lowered:
        fields.additional_fields["certificate_type"] = "Achievement"

    elif "participation" in lowered:
        fields.additional_fields["certificate_type"] = "Participation"

    elif "appreciation" in lowered:
        fields.additional_fields["certificate_type"] = "Appreciation"

    return fields
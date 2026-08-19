from app.core.extractor import parse_certificate_fields


def test_parse_sample_certificate():
    text = """
    CERTIFICATE OF COMPLETION
    This certifies that
    Ali Hassan
    has successfully completed the Machine Learning Fundamentals
    with grade A
    Date: 12/07/2026
    Certificate ID: TEEROP-2026-001
    Teerop Pvt. Limited
    """
    result = parse_certificate_fields(text)
    assert result.candidate_name == "Ali Hassan"
    assert "Machine Learning" in (result.certificate_title or "")
    assert result.issue_date == "12/07/2026"
    assert result.certificate_number == "TEEROP-2026-001"
    assert result.grade_score == "A"

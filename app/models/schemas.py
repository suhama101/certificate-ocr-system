from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class CertificateFields(BaseModel):
    candidate_name: Optional[str] = None
    certificate_title: Optional[str] = None
    organization_name: Optional[str] = None
    issue_date: Optional[str] = None
    certificate_number: Optional[str] = None
    grade_score: Optional[str] = None
    duration: Optional[str] = None
    additional_fields: Dict[str, Any] = Field(default_factory=dict)


class OCRResult(BaseModel):
    id: str
    filename: str
    page_count: int
    average_confidence: Optional[float] = None
    fields: CertificateFields
    raw_text: str
    created_at: str

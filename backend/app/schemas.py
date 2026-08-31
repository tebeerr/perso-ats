from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    resume_id: int
    filename: str
    status: str = "uploaded"


class AnalyzeRequest(BaseModel):
    resume_id: int
    job_description: str = Field(default="", max_length=50_000)


class Issue(BaseModel):
    severity: Literal["critical", "high", "medium", "low"]
    category: str
    title: str
    description: str
    recommendation: str


class ScoreItem(BaseModel):
    label: str
    value: float
    reason: str


class AnalysisResponse(BaseModel):
    analysis_id: int
    status: str = "completed"
    overall_score: float
    label: str
    scores: list[ScoreItem]
    issues: list[Issue]
    recommendations: list[str]
    matched_keywords: list[str]
    missing_keywords: list[str]
    weak_keywords: list[str]
    detected_sections: list[str]
    detected_skills: list[str]
    extracted_text: str
    language: str
    job_match_score: float


class HistoryItem(BaseModel):
    id: int
    filename: str
    overall_score: float
    job_match_score: float
    created_at: datetime
    main_issue: str | None


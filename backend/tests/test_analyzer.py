import pytest

from app.services.analyzer import analyze_resume
from app.services.document_parser import DocumentError, parse_document


SAMPLE = """Jane Doe
jane@example.com | +33 6 12 34 56 78 | linkedin.com/in/janedoe
Summary
Product engineer with 5 years of experience.
Experience
- Built a React dashboard used by 50 users and improved conversion by 20%.
- Developed FastAPI services with Python and Docker.
Skills
Python, React, TypeScript, Docker, SQL, Git, AWS
Education
BSc Computer Science
"""


def test_analysis_detects_contacts_sections_and_skills():
    result = analyze_resume(SAMPLE)
    assert result.overall_score >= 70
    assert "Experience" in result.detected_sections
    assert "python" in result.detected_skills
    assert not any(issue.title == "Email address not detected" for issue in result.issues)


def test_job_matching_returns_missing_terms():
    result = analyze_resume(SAMPLE, "Senior React engineer with Python, Kubernetes, AWS and CI/CD experience.")
    assert "react" in result.matched_keywords
    assert "kubernetes" in result.missing_keywords


def test_rejects_mime_type_that_does_not_match_extension():
    with pytest.raises(DocumentError, match="MIME type"):
        parse_document("resume.pdf", "text/plain", b"%PDF-1.4")

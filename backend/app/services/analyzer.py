import re
from collections import Counter
from dataclasses import dataclass

from app.schemas import Issue, ScoreItem
from app.services.document_parser import detect_possible_columns

SCORING_WEIGHTS = {"Parsing": 20, "Keywords": 20, "Job match": 20, "Experience": 15, "Skills": 10, "Sections": 5, "Formatting": 5, "Contact": 5}
SECTION_PATTERNS = {"Contact": r"\b(contact|coordonn[eé]es)\b", "Summary": r"\b(summary|profile|objective|profil|r[eé]sum[eé])\b", "Experience": r"\b(experience|employment|work history|exp[eé]rience)\b", "Skills": r"\b(skills|technical skills|competencies|comp[eé]tences)\b", "Education": r"\b(education|academic|formation|[eé]ducation)\b"}
SKILLS = {"python", "javascript", "typescript", "react", "node.js", "node", "sql", "postgresql", "mysql", "docker", "kubernetes", "aws", "azure", "gcp", "git", "figma", "fastapi", "django", "flask", "java", "c#", "c++", "excel", "power bi", "tableau", "rest api", "graphql", "ci/cd", "testing", "agile", "scrum", "linux"}
STOP_WORDS = {"with", "that", "this", "from", "your", "have", "will", "and", "the", "for", "are", "our", "you", "job", "role", "team", "work", "years", "about", "into", "using", "experience", "skills", "their", "they", "who", "all", "can", "not", "but", "more", "also", "required", "preferred"}


@dataclass
class AnalysisData:
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
    language: str


def _score_label(score: float) -> str:
    if score >= 90: return "Excellent"
    if score >= 80: return "Strong"
    if score >= 70: return "Good"
    if score >= 60: return "Needs improvement"
    return "Needs work"


def _keywords(text: str) -> set[str]:
    lower = text.lower()
    found = {skill for skill in SKILLS if re.search(rf"(?<!\w){re.escape(skill)}(?!\w)", lower)}
    found.update(re.findall(r"\b(?:python|react|docker|aws|kubernetes|typescript|javascript|sql|figma)\b", lower))
    return found


def _job_terms(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z+#/.]{2,}", text.lower())
    terms = {token for token, count in Counter(tokens).items() if count >= 1 and token not in STOP_WORDS}
    return terms | _keywords(text)


def analyze_resume(text: str, job_description: str = "") -> AnalysisData:
    normalized = re.sub(r"\s+", " ", text).strip()
    lower = normalized.lower()
    sections = [name for name, pattern in SECTION_PATTERNS.items() if re.search(pattern, lower)]
    skills = sorted(_keywords(text))
    issues: list[Issue] = []
    recommendations: list[str] = []
    email = bool(re.search(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", text))
    phone = bool(re.search(r"(?:\+?\d[\d .()/-]{7,}\d)", text))
    links = bool(re.search(r"\b(?:linkedin\.com|github\.com)\b", lower))
    quantified = len(re.findall(r"\b\d+(?:[.,]\d+)?(?:%|x|\+|\s*(?:users|clients|projects|months|years|k|m))\b|[$€£]\s?\d+", lower))
    bullets = len(re.findall(r"(?:^|\n)\s*(?:[-•*]|\d+[.)])\s+", text))
    columns = detect_possible_columns(text)
    parsing = 20.0 if len(normalized) > 350 else 13.0
    formatting = 5.0 if not columns and bullets >= 2 else 3.0
    contact = 5.0 if email and phone else (3.5 if email or phone else 0.0)
    section_score = round(5 * min(len(sections), 4) / 4, 1)
    skills_score = 10.0 if len(skills) >= 6 else round(2 + len(skills) * 1.3, 1)
    experience_score = 15.0 if "Experience" in sections and quantified >= 2 else (10.0 if "Experience" in sections else 4.0)
    matched: list[str] = []
    missing: list[str] = []
    weak: list[str] = []
    if job_description.strip():
        relevant = _job_terms(job_description)
        resume_terms = _job_terms(text)
        matched = sorted(relevant & resume_terms)[:24]
        missing = sorted(relevant - resume_terms)[:16]
        job_match = round(20 * len(matched) / max(min(len(relevant), 30), 1), 1)
        keyword_score = job_match
        weak = sorted({term for term in matched if lower.count(term) == 1})[:8]
    else:
        keyword_score = min(20.0, 6 + len(skills) * 1.8)
        job_match = 12.0
    if not email:
        issues.append(Issue(severity="critical", category="contact", title="Email address not detected", description="No readable email address was found in the extracted text.", recommendation="Add a professional email address in a simple text header."))
    if not phone:
        issues.append(Issue(severity="high", category="contact", title="Phone number not detected", description="A phone number could not be reliably parsed.", recommendation="Add an international-format phone number near your email address."))
    if columns:
        issues.append(Issue(severity="high", category="formatting", title="Possible multi-column layout", description="Widely separated text suggests columns, which some parsers may read out of order.", recommendation="Use a single-column layout for the most predictable parsing."))
    if "Experience" not in sections:
        issues.append(Issue(severity="high", category="sections", title="Experience heading not detected", description="A standard experience section heading was not found.", recommendation="Use a clear 'Experience' or 'Work Experience' heading."))
    if "Education" not in sections:
        issues.append(Issue(severity="medium", category="sections", title="Education heading not detected", description="A standard education section heading was not found.", recommendation="Add an 'Education' heading when it is relevant to your background."))
    if quantified < 2:
        issues.append(Issue(severity="medium", category="experience", title="Few measurable outcomes", description="The text contains limited evidence of quantified impact.", recommendation="Where truthful, add measurable outcomes such as percentages, scale, time saved, or users served."))
    if job_description.strip() and missing:
        issues.append(Issue(severity="medium", category="keywords", title=f"{len(missing)} job terms may be missing", description="Important terms from the job description were not found in the resume text.", recommendation="Incorporate relevant missing terms only where they accurately describe your experience."))
    if email and phone: recommendations.append("Your contact information is readable and likely easy for an ATS to parse.")
    if skills: recommendations.append(f"Your resume includes {len(skills)} detected technical or professional skills.")
    if links: recommendations.append("A professional profile link was detected; keep links written out as readable text.")
    if job_description.strip() and matched: recommendations.append(f"You already match {len(matched)} terms from the supplied job description.")
    score_values = {"Parsing": parsing, "Keywords": keyword_score, "Job match": job_match, "Experience": experience_score, "Skills": skills_score, "Sections": section_score, "Formatting": formatting, "Contact": contact}
    reasons = {"Parsing": "Readable text was extracted from the document.", "Keywords": "Based on relevant skills and job-description terms.", "Job match": "Comparison against the optional job description.", "Experience": "Experience heading and quantified outcomes were checked.", "Skills": "Recognized skills are scored for coverage.", "Sections": "Standard resume headings were detected.", "Formatting": "Simple reading order and bullet structure were checked.", "Contact": "Email and phone-number detection."}
    overall = round(sum(score_values.values()), 1)
    scores = [ScoreItem(label=label, value=value, reason=reasons[label]) for label, value in score_values.items()]
    language = "fr" if any(word in lower for word in ["expérience", "compétences", "formation"]) else "en"
    return AnalysisData(overall, _score_label(overall), scores, issues, recommendations, matched, missing, weak, sections, skills, language)


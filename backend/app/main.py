import json
from contextlib import asynccontextmanager
from datetime import datetime
from io import BytesIO

from fastapi import Depends, FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.database import Base, engine, get_db
from app.models import Analysis, Resume
from app.schemas import AnalysisResponse, AnalyzeRequest, HistoryItem, UploadResponse
from app.services.analyzer import analyze_resume
from app.services.document_parser import DocumentError, parse_document


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="ATS Resume Analyzer API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


def not_found() -> HTTPException:
    return HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "The requested resource was not found."})


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/resumes/upload", response_model=UploadResponse, status_code=201)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)) -> UploadResponse:
    raw = await file.read()
    try:
        parsed = parse_document(file.filename or "", file.content_type, raw)
    except DocumentError as error:
        raise HTTPException(status_code=422, detail={"code": "INVALID_DOCUMENT", "message": str(error)}) from error
    resume = Resume(filename=parsed.filename, file_type=parsed.file_type, file_size=len(raw), extracted_text=parsed.text)
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return UploadResponse(resume_id=resume.id, filename=resume.filename)


@app.post("/api/analyses", response_model=AnalysisResponse, status_code=201)
def create_analysis(request: AnalyzeRequest, db: Session = Depends(get_db)) -> AnalysisResponse:
    resume = db.get(Resume, request.resume_id)
    if not resume:
        raise not_found()
    result = analyze_resume(resume.extracted_text, request.job_description)
    payload = result.__dict__ | {"extracted_text": resume.extracted_text, "job_match_score": next(score.value for score in result.scores if score.label == "Job match")}
    analysis = Analysis(resume_id=resume.id, overall_score=result.overall_score, parsing_score=next(x.value for x in result.scores if x.label == "Parsing"), keyword_score=next(x.value for x in result.scores if x.label == "Keywords"), job_match_score=payload["job_match_score"], experience_score=next(x.value for x in result.scores if x.label == "Experience"), skills_score=next(x.value for x in result.scores if x.label == "Skills"), section_score=next(x.value for x in result.scores if x.label == "Sections"), formatting_score=next(x.value for x in result.scores if x.label == "Formatting"), contact_score=next(x.value for x in result.scores if x.label == "Contact"), result_json=json.dumps(payload, default=lambda value: value.model_dump() if hasattr(value, "model_dump") else value))
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return AnalysisResponse(analysis_id=analysis.id, **payload)


@app.get("/api/analyses", response_model=list[HistoryItem])
def list_analyses(db: Session = Depends(get_db)) -> list[HistoryItem]:
    analyses = db.scalars(select(Analysis).options(joinedload(Analysis.resume)).order_by(Analysis.created_at.desc())).unique().all()
    items = []
    for analysis in analyses:
        payload = json.loads(analysis.result_json)
        issue = payload.get("issues", [{}])[0].get("title") if payload.get("issues") else None
        items.append(HistoryItem(id=analysis.id, filename=analysis.resume.filename, overall_score=analysis.overall_score, job_match_score=analysis.job_match_score, created_at=analysis.created_at, main_issue=issue))
    return items


@app.get("/api/analyses/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)) -> AnalysisResponse:
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise not_found()
    return AnalysisResponse(analysis_id=analysis.id, **json.loads(analysis.result_json))


@app.delete("/api/analyses/{analysis_id}", status_code=204)
def delete_analysis(analysis_id: int, db: Session = Depends(get_db)) -> Response:
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise not_found()
    db.delete(analysis)
    db.commit()
    return Response(status_code=204)


@app.get("/api/analyses/{analysis_id}/report")
def download_report(analysis_id: int, db: Session = Depends(get_db)) -> Response:
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise not_found()
    result = json.loads(analysis.result_json)
    report = f"ATS Resume Analysis\n\nEstimated ATS Compatibility: {result['overall_score']}/100 ({result['label']})\nResume: {analysis.resume.filename}\nGenerated: {analysis.created_at.isoformat()}\n\nScore Breakdown:\n" + "\n".join(f"- {item['label']}: {item['value']}/{20 if item['label'] in ['Parsing', 'Keywords', 'Job match'] else 15 if item['label'] == 'Experience' else 10 if item['label'] == 'Skills' else 5}" for item in result['scores']) + "\n\nRecommendations:\n" + "\n".join(f"- {item}" for item in result['recommendations'])
    return Response(content=report, media_type="text/plain", headers={"Content-Disposition": f'attachment; filename="ats-analysis-{analysis_id}.txt"'})


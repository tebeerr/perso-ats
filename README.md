
# ATS Resume Analyzer

A local, deterministic resume-review tool that estimates ATS compatibility. It accepts PDF and DOCX resumes, optionally matches them to a job description, stores results locally in SQLite, and exports a readable report.

> The score is an estimate based on transparent rules. It is not an employer's or a specific ATS vendor's score and does not guarantee an application outcome.

## Quick start

### Docker

```bash
docker compose up --build
```

Open `http://localhost:5173`. The API docs are at `http://localhost:8000/docs`.

### Local development

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

To run backend tests, install `requirements-dev.txt` in place of `requirements.txt`, then run `pytest`.

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

## What is implemented

- Secure PDF/DOCX validation (extension, MIME type, signature and 10 MB limit)
- Text extraction with PyMuPDF and python-docx
- Deterministic, explainable scoring for parsing, keywords, job match, sections, contact details, skills, experience and formatting
- Local SQLite analysis history, deletion and text report export
- React dashboard with upload, result, history, and settings views
- Unit tests for the scoring engine

## Project structure

`backend/` contains the FastAPI service and SQLite models. `frontend/` contains the Vite React application. Uploaded documents are processed in memory and their original binary content is not persisted.

## Known first-release limitations

- The document preview shows extracted text rather than a rendered original document.
- Keyword equivalence is dictionary-based; semantic matching is deliberately left behind an analysis-provider boundary for a later release.
- The report is plain text to keep the first release dependency-light.
- Analysis comparison and a PDF-formatted report are planned next; history, deletion and text export are available now.

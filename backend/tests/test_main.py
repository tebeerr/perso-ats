import json
from unittest.mock import MagicMock

from app.main import create_analysis
from app.models import Resume
from app.schemas import AnalyzeRequest


def test_create_analysis_persists_json_serializable_result():
    db = MagicMock()
    db.get.return_value = Resume(
        id=1,
        filename="resume.txt",
        file_type="txt",
        file_size=64,
        extracted_text="Jane Doe\njane@example.com\nExperience\nBuilt a React app with Python and Docker.",
    )
    db.refresh.side_effect = lambda analysis: setattr(analysis, "id", 42)

    response = create_analysis(AnalyzeRequest(resume_id=1), db)

    saved_analysis = db.add.call_args.args[0]
    saved_result = json.loads(saved_analysis.result_json)
    assert response.analysis_id == 42
    assert saved_result["scores"][0]["label"] == "Parsing"
    assert response.scores[0].label == "Parsing"

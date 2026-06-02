import pytest
from pydantic import ValidationError

from app.research.schemas import ResearchRequest


def test_research_request_requires_non_trivial_question() -> None:
    with pytest.raises(ValidationError):
        ResearchRequest(question="tiny")


def test_research_request_defaults_outputs() -> None:
    request = ResearchRequest(question="How should agent memory systems be evaluated?")
    assert "paper_draft" in request.target_outputs

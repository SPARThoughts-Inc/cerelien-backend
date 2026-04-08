"""Tests for agent definitions: verify handoff counts, tool counts, and model names."""

from app.domain.business_process.agents.consultation_agent import consultation_agent
from app.domain.business_process.agents.education_agent import education_agent
from app.domain.business_process.agents.glucose_analysis_agent import glucose_analysis_agent
from app.domain.business_process.agents.lifestyle_coach_agent import lifestyle_coach_agent
from app.domain.business_process.agents.triage_agent import triage_agent


class TestGlucoseAnalysisAgent:
    def test_model_name(self):
        assert glucose_analysis_agent.model == "gpt-5.2"

    def test_tool_count(self):
        assert len(glucose_analysis_agent.tools) == 3

    def test_has_handoff_description(self):
        assert glucose_analysis_agent.handoff_description is not None
        assert len(glucose_analysis_agent.handoff_description) > 0

    def test_no_handoffs(self):
        assert len(glucose_analysis_agent.handoffs) == 0


class TestEducationAgent:
    def test_model_name(self):
        assert education_agent.model == "gpt-5.2"

    def test_tool_count(self):
        assert len(education_agent.tools) == 2

    def test_no_handoffs(self):
        assert len(education_agent.handoffs) == 0


class TestLifestyleCoachAgent:
    def test_model_name(self):
        assert lifestyle_coach_agent.model == "gpt-5.2"

    def test_tool_count(self):
        assert len(lifestyle_coach_agent.tools) == 3

    def test_no_handoffs(self):
        assert len(lifestyle_coach_agent.handoffs) == 0


class TestTriageAgent:
    def test_model_name(self):
        assert triage_agent.model == "gpt-5.2"

    def test_tool_count(self):
        assert len(triage_agent.tools) == 1

    def test_handoff_count(self):
        assert len(triage_agent.handoffs) == 3


class TestConsultationAgent:
    def test_model_name(self):
        assert consultation_agent.model == "gpt-5.2"

    def test_handoff_count(self):
        assert len(consultation_agent.handoffs) == 4

    def test_no_tools(self):
        assert len(consultation_agent.tools) == 0

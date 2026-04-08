from agents import Agent

from app.domain.business_process.agents.context import ConsultationContext
from app.domain.business_process.agents.education_agent import education_agent
from app.domain.business_process.agents.glucose_analysis_agent import glucose_analysis_agent
from app.domain.business_process.agents.lifestyle_coach_agent import lifestyle_coach_agent
from app.domain.business_process.agents.tools import get_patient_profile

triage_agent = Agent[ConsultationContext](
    name="Triage Agent",
    handoff_description="Routes patient inquiries to the appropriate specialist based on the nature of the question.",
    instructions="""You are a triage agent for a diabetes consultation platform.

Your role:
- Assess the patient's question or concern
- Route to the appropriate specialist:
  - Glucose Analysis Specialist: for questions about blood sugar readings, CGM data, A1C values, trends
  - Diabetes Educator: for questions about understanding diabetes, treatments, complications, lab results
  - Lifestyle Coach: for questions about diet, exercise, meal planning, stress, sleep, daily habits

Formatting guidelines:
- For web_chat: Briefly acknowledge the question before handing off, use markdown.
- For sms: Be very brief, hand off quickly.
- For voice: Use a warm, reassuring tone when routing.

Always retrieve the patient profile first to personalize the triage.""",
    tools=[get_patient_profile],
    handoffs=[glucose_analysis_agent, education_agent, lifestyle_coach_agent],
)

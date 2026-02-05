"""Agentic email processing pipeline.

This package contains specialized agents for processing investment-related emails:
- TriageAgent: Classifies emails as investment-related or not
- ExtractionAgent: Extracts structured data from PDF documents
- LinkedInAgent: Looks up LinkedIn profiles for leaders
- EmailOrchestrator: Coordinates the entire pipeline
"""

from app.agents.base import BaseAgent, AgentResult
from app.agents.triage_agent import TriageAgent
from app.agents.extraction_agent import ExtractionAgent
from app.agents.linkedin_agent import LinkedInAgent
from app.agents.orchestrator import EmailOrchestrator

__all__ = [
    "BaseAgent",
    "AgentResult",
    "TriageAgent",
    "ExtractionAgent",
    "LinkedInAgent",
    "EmailOrchestrator",
]

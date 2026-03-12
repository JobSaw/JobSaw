"""
agents package -- Job description analysis agent chain.

Exposes the JobAnalysisOrchestrator as the primary entry point for
parsing raw job descriptions into structured hard skills, soft skills,
and work scope data.
"""

from agents.orchestrator import JobAnalysisOrchestrator

__all__ = ["JobAnalysisOrchestrator"]

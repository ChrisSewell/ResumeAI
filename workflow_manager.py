from typing import Dict, Any
import logging
from agents.job_analyzer import JobAnalyzer
from agents.profile_matcher import ProfileMatcher
from agents.resume_builder import ResumeGenerator
from agents.ats_analyzer import ATSAnalyzer
from agents.cover_letter_generator import CoverLetterGenerator
from document_generator.cover_letter_generator import CoverLetterDocumentGenerator

class WorkflowManager:
    """Manages the resume generation workflow."""

    def __init__(self):
        """Initialize workflow components."""
        self.logger = logging.getLogger("WorkflowManager")
        self.logger.info("Initializing workflow manager...")
        
        self.job_analyzer = JobAnalyzer()
        self.profile_matcher = ProfileMatcher()
        self.resume_generator = ResumeGenerator()
        self.ats_analyzer = ATSAnalyzer()
        self.cover_letter_generator = CoverLetterGenerator()
        self.cover_letter_doc_generator = CoverLetterDocumentGenerator()
        
        self.logger.info("Workflow manager initialized")
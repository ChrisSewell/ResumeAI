from typing import Dict, Any
from .base_agent import BaseAgent
from .models import ProfileMatch, JobRequirement
import logging

class ProfileMatcher(BaseAgent[ProfileMatch]):
    """Agent for matching candidate profiles against job requirements."""

    def __init__(self):
        super().__init__(ProfileMatch)
        self.logger = logging.getLogger(f"Agent.{self.__class__.__name__}")

    def process(self, job_requirements: dict, profile: dict) -> dict:
        """Process the job requirements and profile to generate a match score."""
        self.logger.info("Starting profile matching...")
        
        try:
            # Pre-process profile data for better matching
            professional_experience = profile.get('professional_experience', [])
            skills = {
                'technical': profile.get('skills', {}).get('technical', []),
                'management': profile.get('skills', {}).get('management', []),
                'soft': profile.get('skills', {}).get('soft', [])
            }
            
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Match candidate profile against job requirements. Return a JSON object with:\n"
                        "- qualifications_match: {requirement: score} (0.0-1.0)\n"
                        "- responsibilities_match: {responsibility: score} (0.0-1.0)\n"
                        "- technical_requirements_match: {requirement: score} (0.0-1.0)\n"
                        "- soft_skills_match: {skill: score} (0.0-1.0)\n"
                        "- overall_match_score: float (0.0-1.0)\n"
                        "- key_strengths: list of strings\n"
                        "- areas_for_improvement: list of strings\n"
                        "- recommendations: list of strings\n\n"
                        "Consider ALL skills categories (technical, management, soft) when matching."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Match this profile against requirements:\n"
                        f"Requirements: {job_requirements}\n"
                        f"Profile Experience: {professional_experience}\n"
                        f"Profile Skills: {skills}\n"
                        f"Profile Certifications: {profile.get('certifications', [])}"
                    )
                }
            ]
            
            result = self._create_completion(messages, self.default_model)
            
            self.logger.info(f"Profile matching completed with overall score: {result.overall_match_score:.2%}")
            self.logger.debug(f"Key strengths identified: {len(result.key_strengths)}")
            self.logger.debug(f"Areas for improvement: {len(result.areas_for_improvement)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Profile matching failed: {str(e)}")
            raise
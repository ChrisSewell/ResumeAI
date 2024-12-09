from typing import Dict, Any
from openai import OpenAI
from .base_agent import BaseAgent
from .models import JobRequirement
from config.model_settings import OPENAI_MODELS, MODEL_CONFIG
import json

class JobAnalyzer(BaseAgent[JobRequirement]):
    def __init__(self):
        super().__init__(JobRequirement)
    
    def process(self, job_data: Dict[str, Any]) -> JobRequirement:
        """Analyze job posting and extract key requirements."""
        self.logger.info("Starting job analysis...")
        
        try:
            details = job_data['job_listing']['details']
            self.logger.info(f"Analyzing job: {details['title']} at {job_data['job_listing']['company']}")
            
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Extract ONLY explicit requirements from job postings. "
                        "Format the response as a JSON object with these keys:\n"
                        "- required_qualifications (dict of str to list[str])\n"
                        "- key_responsibilities (dict of str to list[str])\n"
                        "- technical_requirements: {\n"
                        "    'technical': list[str],\n"
                        "    'management': list[str],\n"
                        "    'tools': list[str]\n"
                        "  }\n"
                        "- soft_skills: {\n"
                        "    'interpersonal': list[str],\n"
                        "    'organizational': list[str],\n"
                        "    'leadership': list[str]\n"
                        "  }\n"
                        "- preferences (optional, dict of str to list[str])"
                    )
                },
                {
                    "role": "user",
                    "content": f"Analyze this job posting:\nTitle: {details['title']}\nDescription: {details['description']}"
                }
            ]
            
            result = self._create_completion(messages, OPENAI_MODELS["job_analysis"])
            
            self.logger.info("Job analysis completed successfully")
            self.logger.debug(f"Identified {len(result.required_qualifications)} qualifications, "
                          f"{len(result.key_responsibilities)} responsibilities, "
                          f"{len(result.technical_requirements)} technical requirements")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Job analysis failed: {str(e)}")
            raise
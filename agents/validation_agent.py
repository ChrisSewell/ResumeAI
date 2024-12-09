from typing import Dict, Any, List, Set
from openai import OpenAI
from pydantic import BaseModel
from .base_agent import BaseAgent
from .models import (
    ValidatedResume,
    JobValidationResult,
    ProfileValidationResult,
    ResumeValidationResult,
    ValidationReport,
    JobRequirement,
    ProfileMatch,
    WorkExperience,
    ValidationResponse
)
from config.model_settings import OPENAI_MODELS, MODEL_CONFIG
import json
import time

class ValidationAgent(BaseAgent[ValidationResponse]):  # Change the response model
    """Agent for validating outputs from other agents."""
    
    def __init__(self):
        super().__init__(ValidationResponse)  # Use ValidationResponse
        self.confidence_threshold = 0.8
        self.logger.debug(f"Initialized ValidationAgent with confidence threshold: {self.confidence_threshold}")
    
    def process(self, data: Dict[str, Any]) -> ResumeValidationResult:
        """Process validation request."""
        raise NotImplementedError(
            "ValidationAgent doesn't use the general process method. "
            "Use validate_resume(), validate_job_analysis(), or validate_profile_matches() instead."
        )
    
    def validate_resume(
        self, 
        resume: ValidatedResume, 
        profile: Dict[str, Any], 
        job_requirements: JobRequirement,
        ats_analysis: Dict[str, Any] = None
    ) -> ResumeValidationResult:
        """Validate resume content with chunked processing for large resumes."""
        self.logger.info("Starting comprehensive resume validation...")
        
        try:
            # First, validate the overall structure and non-experience content
            base_validation = self._validate_base_content(resume, job_requirements, ats_analysis)
            
            # Create a complete ValidatedResume by combining base content with original work experience
            complete_resume = ValidatedResume(
                name=base_validation.validated_content.name,
                summary=base_validation.validated_content.summary,
                skills=base_validation.validated_content.skills,
                certifications=base_validation.validated_content.certifications,
                education=base_validation.validated_content.education,
                personal_information=base_validation.validated_content.personal_information,
                work_experience=resume.work_experience  # Use original work experience
            )
            
            # Return the final validation result
            return ResumeValidationResult(
                is_valid=base_validation.is_valid,
                validation_score=base_validation.validation_score,
                report=base_validation.report,
                validated_content=complete_resume,
                ats_analysis=ats_analysis or {}
            )
            
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            raise

    def _validate_base_content(
        self, 
        resume: ValidatedResume, 
        job_requirements: JobRequirement,
        ats_analysis: Dict[str, Any]
    ) -> ValidationResponse:
        """Validate the basic resume content excluding work experiences."""
        messages = [
            {
                "role": "system",
                "content": (
                    "Validate the basic resume content (excluding work experience). "
                    "Keep responses extremely concise. Return a JSON object with:\n"
                    "{\n"
                    "  \"is_valid\": boolean,\n"
                    "  \"validation_score\": float,\n"
                    "  \"report\": {\"summary\": string, \"details\": [strings]},\n"
                    "  \"validated_content\": {\n"
                    "    \"name\": string,\n"
                    "    \"summary\": string,\n"
                    "    \"skills\": {\"technical\": [], \"soft\": [], \"other\": []},\n"
                    "    \"certifications\": []\n"
                    "  }\n"
                    "}\n"
                    "IMPORTANT: Do not include work_experience in the response."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Validate this resume content:\n"
                    f"Name: {resume.name}\n"
                    f"Summary: {resume.summary}\n"
                    f"Skills: {resume.skills}\n"
                    f"Certifications: {resume.certifications}\n"
                    f"Requirements: {job_requirements.model_dump()}\n"
                    f"ATS Analysis: {ats_analysis}"
                )
            }
        ]
        
        return self._create_completion(messages, self.default_model)

    def _validate_work_experiences(
        self,
        experiences: List[WorkExperience],
        job_requirements: JobRequirement
    ) -> List[WorkExperience]:
        """Validate work experiences in smaller chunks."""
        validated_experiences = []
        chunk_size = 2  # Process 2 experiences at a time
        
        for i in range(0, len(experiences), chunk_size):
            chunk = experiences[i:i + chunk_size]
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Validate these work experiences. Keep the same structure but ensure "
                        "content is relevant and concise. Return a JSON array of work experiences."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Validate these experiences against requirements:\n"
                        f"Experiences: {[exp.model_dump() for exp in chunk]}\n"
                        f"Requirements: {job_requirements.model_dump()}"
                    )
                }
            ]
            
            try:
                # Temporarily change response model for this call
                original_model = self.response_model
                self.response_model = List[WorkExperience]
                
                chunk_result = self._create_completion(messages, self.default_model)
                validated_experiences.extend(chunk_result)
                
            except Exception as e:
                self.logger.warning(f"Error validating experience chunk: {str(e)}")
                # On error, keep original experiences
                validated_experiences.extend(chunk)
                
            finally:
                # Restore original response model
                self.response_model = original_model
        
        return validated_experiences

    def validate_job_analysis(self, job_analysis: JobRequirement, raw_job_data: Dict[str, Any]) -> JobValidationResult:
        """Validate job analysis against original data."""
        self.logger.info("Validating job analysis...")
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a precise job analysis validator. Verify the extracted requirements match the original posting. "
                    "Format response as JSON with: is_valid (bool), validation_score (float), "
                    "report (object with accuracy_score, completeness_score, relevance_score, "
                    "issues_found: list[str], suggestions: list[str]), and "
                    "validated_content (object matching input structure with required_qualifications, "
                    "key_responsibilities, technical_requirements, soft_skills, and preferences)."
                )
            },
            {
                "role": "user",
                "content": f"Validate job analysis against original data:\nAnalysis: {job_analysis.model_dump()}\nOriginal: {raw_job_data}"
            }
        ]
        
        try:
            completion = self.client.chat.completions.create(
                model=self.default_model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=self.default_config["temperature"]
            )
            
            response_json = json.loads(completion.choices[0].message.content)
            return JobValidationResult.model_validate(response_json)
            
        except Exception as e:
            self.logger.error(f"Error during job analysis validation: {str(e)}")
            raise

    def validate_profile_matches(
        self, 
        matches: ProfileMatch, 
        job_analysis: JobRequirement, 
        profile: Dict[str, Any]
    ) -> ResumeValidationResult:
        """Validate profile matches against job requirements and candidate profile."""
        self.logger.info("Validating profile matches...")
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a precise profile match validator. Verify accuracy and completeness. "
                    "Format response as JSON with: is_valid (bool), validation_score (float), "
                    "report (object with accuracy_score, completeness_score, relevance_score, "
                    "issues_found, suggestions), and validated_content (resume object)."
                )
            },
            {
                "role": "user",
                "content": f"Validate matches against requirements and profile:\nMatches: {matches.model_dump()}\nRequirements: {job_analysis.model_dump()}\nProfile: {profile}"
            }
        ]
        
        return self._create_completion(messages, OPENAI_MODELS["validation"])
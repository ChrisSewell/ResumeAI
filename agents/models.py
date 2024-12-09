from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel

class WorkExperience(BaseModel):
    """Model for work experience entries."""
    company: str
    position: str
    employment_period: str
    location: str
    industry: str
    responsibilities: List[str]
    skills_acquired: List[str] = []

class Certification(BaseModel):
    """Model for certification entries."""
    name: str
    description: str
    issuer: Optional[str] = ""
    date_obtained: Optional[str] = ""

class PersonalInformation(BaseModel):
    """Model for personal information."""
    name: str
    surname: str
    contact: Dict[str, str]
    online_presence: Dict[str, str]

class BaseValidatedResume(BaseModel):
    """Model for basic resume content without work experience."""
    name: str
    summary: str
    skills: Dict[str, List[str]]
    certifications: List[Certification] = []
    education: Optional[List[Dict[str, Any]]] = None
    personal_information: Optional[PersonalInformation] = None

class ValidatedResume(BaseValidatedResume):
    """Model for a complete validated resume including work experience."""
    work_experience: List[WorkExperience]

class ValidationReport(BaseModel):
    """Model for validation report."""
    summary: str
    details: List[str]

class BaseValidationResult(BaseModel):
    """Base validation result model."""
    is_valid: bool
    validation_score: float
    report: ValidationReport

class ResumeValidationResult(BaseModel):
    """Model for resume validation results."""
    is_valid: bool
    validation_score: float
    report: ValidationReport
    validated_content: BaseValidatedResume
    ats_analysis: Dict[str, Any]

class JobValidationResult(BaseValidationResult):
    """Model for job analysis validation results."""
    validated_content: Dict[str, Dict[str, List[str]]]  # Match JobRequirement structure

class ProfileValidationResult(BaseValidationResult):
    """Model for profile matching validation results."""
    validated_content: Dict[str, float]  # Match ProfileMatch structure

class JobRequirement(BaseModel):
    """Model for job requirements analysis."""
    required_qualifications: Dict[str, List[str]]
    key_responsibilities: Dict[str, List[str]]
    technical_requirements: Dict[str, List[str]]  # technical, management, tools
    soft_skills: Dict[str, List[str]]  # interpersonal, organizational, leadership
    preferences: Optional[Dict[str, List[str]]] = None

class MatchDetail(BaseModel):
    """Model for individual match details."""
    matches: List[str]
    gaps: List[str]
    score: float

class ProfileMatch(BaseModel):
    """Model for profile matching results."""
    qualifications_match: Dict[str, float]
    responsibilities_match: Dict[str, float]
    technical_requirements_match: Dict[str, float]
    soft_skills_match: Dict[str, float]
    overall_match_score: float
    key_strengths: List[str]
    areas_for_improvement: List[str]
    recommendations: List[str]

class KeywordInfo(BaseModel):
    """Model for keyword information."""
    name: str
    weight: int
    category: Optional[str] = None

class KeywordMatch(BaseModel):
    """Model for keyword matching results."""
    matched_keywords: List[Dict[str, Any]]  # word, context, strength
    missing_keywords: List[Dict[str, Any]]  # word, importance
    overall_match_score: float
    optimization_suggestions: List[str]
    ats_score: float

class ATSAnalysis(BaseModel):
    """Model for ATS keyword analysis."""
    technical_keywords: List[KeywordInfo]
    soft_skills: List[KeywordInfo]
    industry_terms: List[KeywordInfo]
    certifications: List[KeywordInfo]
    tools_and_technologies: List[KeywordInfo]

class CoverLetter(BaseModel):
    """Model for cover letter content."""
    greeting: str
    opening_paragraph: str
    body_paragraphs: List[str]
    closing_paragraph: str
    signature: str
    keywords_used: List[str]

class ValidationResponse(BaseModel):
    """Model for validation responses."""
    is_valid: bool
    validation_score: float
    report: ValidationReport
    validated_content: BaseValidatedResume
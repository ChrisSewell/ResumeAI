from typing import List, Dict, Any, Tuple, Optional
from openai import OpenAI
from .base_agent import BaseAgent
from .models import ValidatedResume, ProfileMatch, JobRequirement, WorkExperience, Certification, KeywordMatch, PersonalInformation
from config.model_settings import OPENAI_MODELS, MODEL_CONFIG
import logging
import json
from datetime import datetime, timedelta

class ResumeGenerator(BaseAgent[ValidatedResume]):
    """Agent for generating tailored resumes."""

    def __init__(self):
        super().__init__(ValidatedResume)
        self.logger = logging.getLogger(f"Agent.{self.__class__.__name__}")
        self.client = OpenAI()
        self.model_config = MODEL_CONFIG

    def _extract_work_experience(self, profile: Dict[str, Any]) -> List[WorkExperience]:
        """Extract and validate all work experience entries."""
        experiences = []
        professional_experience = profile.get('professional_experience', [])
        
        self.logger.info(f"Extracting {len(professional_experience)} work experiences")
        
        for exp in professional_experience:
            work_exp = WorkExperience(
                company=exp.get('company', ''),
                position=exp.get('position', ''),
                employment_period=exp.get('employment_period', ''),
                location=exp.get('location', ''),
                industry=exp.get('industry', ''),
                responsibilities=exp.get('responsibilities', []),
                skills_acquired=exp.get('skills_acquired', [])
            )
            experiences.append(work_exp)
            self.logger.debug(f"Added experience: {work_exp.company} - {work_exp.position}")
            
        return experiences

    def _enhance_work_experience(self, experience: WorkExperience, job_requirements: JobRequirement, 
                               ats_analysis: KeywordMatch) -> WorkExperience:
        """Enhance a single work experience entry while maintaining truthfulness."""
        try:
            # Get timing context for this experience
            start_date, end_date = self._parse_employment_period(experience.employment_period)
            current_date = datetime.now()
            
            # Determine experience timing context
            is_current = end_date and end_date >= current_date - timedelta(days=30)
            is_recent = end_date and end_date >= current_date - timedelta(days=180)
            experience_duration = (end_date - start_date).days / 365 if start_date and end_date else None
            
            # Build dynamic rules based on timing
            timing_context = []
            if is_current:
                timing_context.append("This is the current role")
            if is_recent:
                timing_context.append("This is a recent role")
            if experience_duration:
                timing_context.append(f"Duration: {experience_duration:.1f} years")
            
            # Add skill context
            skill_context = self._get_skill_context(experience.skills_acquired, job_requirements)
            
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Enhance this work experience entry while maintaining strict truthfulness. "
                        f"Context: {', '.join(timing_context)}\n"
                        f"Skills Context:\n{skill_context}\n\n"
                        "Rules:\n"
                        "1. Only highlight skills and achievements explicitly mentioned\n"
                        "2. Do not infer or add capabilities not clearly demonstrated\n"
                        "3. Use precise language that reflects actual level of involvement\n"
                        "4. Focus on transferable skills without overstating their application\n"
                        "5. If a skill is mentioned, preserve the original context\n"
                        "6. Use timing-appropriate language:\n"
                        "   - Current role: Use present tense ('managing', 'developing')\n"
                        "   - Recent role: Emphasize relevance ('recently managed', 'developed')\n"
                        "   - Past role: Use past tense ('managed', 'developed')\n"
                        "7. For skills mentioned in job requirements, provide specific context\n"
                        "Return a JSON object with these exact fields:\n"
                        "{\n"
                        "  \"responsibilities\": [\"string\"],\n"
                        "  \"skills_acquired\": [\"string\"]\n"
                        "}\n"
                        "Maintain factual accuracy while highlighting relevant experience."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Original experience: {experience.model_dump_json()}\n"
                        f"Target job requirements: {job_requirements.model_dump_json()}\n"
                        f"ATS Keywords: {ats_analysis.model_dump_json()}\n\n"
                        f"Enhance this experience while maintaining strict truthfulness."
                    )
                }
            ]
            
            completion = self.client.chat.completions.create(
                model=OPENAI_MODELS["resume"],
                messages=messages,
                **self.model_config
            )
            
            enhanced = json.loads(completion.choices[0].message.content)
            
            # Create a new WorkExperience to avoid modifying the original
            return WorkExperience(
                company=experience.company,
                position=experience.position,
                employment_period=experience.employment_period,
                location=experience.location,
                industry=experience.industry,
                responsibilities=enhanced.get('responsibilities', experience.responsibilities),
                skills_acquired=enhanced.get('skills_acquired', experience.skills_acquired)
            )
            
        except Exception as e:
            self.logger.error(f"Error enhancing experience {experience.company}: {str(e)}")
            return experience

    def _parse_employment_period(self, period: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Parse employment period string into start and end dates."""
        try:
            # Handle common formats
            start_str, end_str = period.split(" - ")
            
            def parse_date_part(date_str: str) -> Optional[datetime]:
                if date_str.lower() in ('current', 'present'):
                    return datetime.now()
                
                # Try different date formats
                for fmt in ('%m/%Y', '%Y/%m', '%Y-%m', '%m-%Y', '%Y'):
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
                return None
            
            return parse_date_part(start_str), parse_date_part(end_str)
        except Exception:
            return None, None

    def _get_summary_prompt(self, profile: Dict[str, Any], resume: ValidatedResume, job_requirements: JobRequirement) -> List[Dict[str, str]]:
        """Generate dynamic summary prompt based on actual profile data."""
        
        # Calculate date thresholds
        current_date = datetime.now()
        six_months_ago = current_date - timedelta(days=180)
        two_years_ago = current_date - timedelta(days=730)
        
        def parse_date(date_str: str) -> datetime:
            """Parse date string in various formats."""
            try:
                # Try different date formats
                for fmt in ('%Y', '%Y/%m', '%Y-%m', '%Y/%m/%d', '%Y-%m-%d'):
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
                return datetime.strptime(date_str.split()[0], '%Y')  # Fallback to year only
            except (ValueError, AttributeError, IndexError):
                return datetime.min

        # Get recent certifications
        recent_certs = [
            cert for cert in profile.get('certifications', [])
            if parse_date(cert.get('date_obtained', '')) >= six_months_ago
        ]
        
        # Get skills with timing context
        recent_skills = set()
        established_skills = set()
        total_experience = timedelta(0)
        current_role_skills = set()
        
        for exp in profile.get('professional_experience', []):
            start_date, end_date = self._parse_employment_period(exp.get('employment_period', ''))
            if start_date and end_date:
                duration = end_date - start_date
                total_experience += duration
                
                # Categorize skills based on recency
                skills = set(exp.get('skills_acquired', []))
                if end_date >= six_months_ago:
                    recent_skills.update(skills)
                    if end_date >= current_date - timedelta(days=30):  # Current role
                        current_role_skills.update(skills)
                elif end_date >= two_years_ago:
                    established_skills.update(skills)
        
        # Build dynamic rules based on profile
        rules = [
            "Use first-person perspective ('I have', 'my experience')",
            "Keep it brief and impactful",
            f"Total years of experience: {total_experience.days / 365:.1f}",
            "Be honest about experience levels:"
        ]
        
        # Add skill-based rules
        if current_role_skills:
            rules.append("Current role skills: " + ", ".join(sorted(current_role_skills)[:3]))
        if recent_skills - current_role_skills:  # Recent but not current
            rules.append("Recent experience with: " + 
                        ", ".join(sorted(recent_skills - current_role_skills)[:3]))
        if established_skills - recent_skills:  # Established but not recent
            rules.append("Previous experience in: " + 
                        ", ".join(sorted(established_skills - recent_skills)[:3]))
        
        # Add certification rules
        if recent_certs:
            cert_names = [cert['name'] for cert in recent_certs]
            rules.append(f"New certifications ({', '.join(cert_names)})")
        
        return [
            {
                "role": "system",
                "content": (
                    "Generate a concise first-person professional summary in 3-4 sentences maximum. "
                    "Rules:\n" + "\n".join(f"{i+1}. {rule}" for i, rule in enumerate(rules)) +
                    "\nReturn a JSON object with a single field 'summary'."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Write a concise first-person summary (3-4 sentences) that honestly represents "
                    f"my experience and growth areas.\n"
                    f"Resume: {resume.model_dump_json()}\n"
                    f"Job Requirements: {job_requirements.model_dump_json()}"
                )
            }
        ]

    def process(self, profile: dict, profile_match: ProfileMatch, 
               job_requirements: JobRequirement, ats_analysis: KeywordMatch) -> ValidatedResume:
        """Generate a tailored resume with ATS optimization."""
        self.logger.info("Starting resume generation...")
        
        try:
            # 1. First, extract ALL work experience
            all_experience = self._extract_work_experience(profile)
            if not all_experience:
                raise ValueError("No work experience found in profile")
            
            self.logger.info(f"Extracted {len(all_experience)} work experiences")
            
            # 2. Enhance each experience individually
            enhanced_experience = []
            for exp in all_experience:
                enhanced = self._enhance_work_experience(exp, job_requirements, ats_analysis)
                enhanced_experience.append(enhanced)
                self.logger.debug(f"Enhanced experience: {enhanced.company} - {enhanced.position}")
            
            # 3. Verify we haven't lost any experiences
            if len(enhanced_experience) != len(all_experience):
                self.logger.error("Experience count mismatch! Using original experiences.")
                enhanced_experience = all_experience
            
            # 4. Create the complete resume with ALL experiences
            resume = ValidatedResume(
                name=self._format_full_name(profile.get('personal_information', {})),
                summary="",  # Will be filled later
                work_experience=enhanced_experience,
                skills=self._extract_skills(profile.get('skills', {})),
                certifications=[
                    Certification(
                        name=cert.get('name', ''),
                        description=cert.get('description', ''),
                        issuer=cert.get('issuer', ''),
                        date_obtained=cert.get('date_obtained', '')
                    ) for cert in profile.get('certifications', [])
                ],
                personal_information=self._extract_personal_info(profile.get('personal_information', {}))
            )
            
            # 5. Generate an optimized summary
            messages = self._get_summary_prompt(profile, resume, job_requirements)
            
            completion = self.client.chat.completions.create(
                model=OPENAI_MODELS["resume"],
                messages=messages,
                **self.model_config
            )
            
            summary_response = json.loads(completion.choices[0].message.content)
            resume.summary = summary_response.get('summary', '')
            
            # 6. Final verification
            self.logger.info(f"Final resume contains {len(resume.work_experience)} work experiences")
            for exp in resume.work_experience:
                self.logger.debug(f"Final experience: {exp.company} - {exp.position}")
            
            return resume
            
        except Exception as e:
            self.logger.error(f"Error in resume generation: {str(e)}")
            self.logger.error(f"Full error details: {str(e)}", exc_info=True)
            raise

    def _format_full_name(self, personal_info: Dict[str, Any]) -> str:
        """Format full name from personal info dict."""
        name = personal_info.get('name', '')
        surname = personal_info.get('surname', '')
        return f"{name} {surname}".strip()

    def _extract_skills(self, skills_dict: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Extract and categorize skills from profile."""
        return {
            'technical': skills_dict.get('technical', []),
            'soft': skills_dict.get('soft', []),
            'other': skills_dict.get('management', [])  # Include any other categories
        }

    def _extract_personal_info(self, personal_info: Dict[str, Any]) -> Optional[PersonalInformation]:
        """Extract personal information safely."""
        if not personal_info:
            return None
        
        return PersonalInformation(
            name=personal_info.get('name', ''),
            surname=personal_info.get('surname', ''),
            contact=personal_info.get('contact', {}),
            online_presence=personal_info.get('online_presence', {})
        )

    def _get_skill_context(self, skills: List[str], job_requirements: JobRequirement) -> str:
        """Generate context about skills based on job requirements."""
        matching_skills = []
        related_skills = []
        learning_skills = []
        
        required_skills = set()
        for category in job_requirements.technical_requirements.values():
            required_skills.update(category)
        
        for skill in skills:
            if skill.lower() in {req.lower() for req in required_skills}:
                matching_skills.append(skill)
            elif any(req.lower() in skill.lower() or skill.lower() in req.lower() 
                    for req in required_skills):
                related_skills.append(skill)
            else:
                learning_skills.append(skill)
        
        context = []
        if matching_skills:
            context.append(f"Directly relevant skills: {', '.join(matching_skills[:3])}")
        if related_skills:
            context.append(f"Related skills: {', '.join(related_skills[:3])}")
        if learning_skills:
            context.append(f"Additional skills: {', '.join(learning_skills[:3])}")
        
        return "\n".join(context)
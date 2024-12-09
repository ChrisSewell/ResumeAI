from typing import Dict, Any, Optional, Tuple
from .base_agent import BaseAgent
from .models import CoverLetter, KeywordMatch, JobRequirement, ProfileMatch
from config.model_settings import OPENAI_MODELS
import logging
from datetime import datetime, timedelta

class CoverLetterGenerator(BaseAgent[CoverLetter]):
    """Agent for generating ATS-optimized cover letters."""
    
    def __init__(self):
        super().__init__(CoverLetter)
        self.logger = logging.getLogger(f"Agent.{self.__class__.__name__}")
    
    def process(self, input_data: Dict[str, Any]) -> CoverLetter:
        """Process method required by BaseAgent."""
        try:
            # Extract required data
            profile = input_data['profile']
            job_requirements = input_data['job_requirements']
            profile_match = input_data['profile_match']
            ats_analysis = input_data['ats_analysis']
            
            # Get dynamic context
            experience_context = self._get_experience_context(profile, job_requirements)
            skill_context = self._get_skill_matches(profile_match, ats_analysis)
            job_context = self._get_job_context(job_requirements)
            experience_match = self._analyze_experience_match(profile, job_requirements)
            
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Generate a professional cover letter based on the candidate's actual experience. "
                        f"\nJob Context:\n{job_context}\n"
                        f"\nCandidate Context:\n{experience_context}"
                        f"\nSkill Context:\n{skill_context}\n"
                        f"\nExperience Match:\n{experience_match}\n"
                        "Rules:\n"
                        "1. Use first-person perspective\n"
                        "2. Only reference skills and experience explicitly shown in profile\n"
                        "3. Be clear about experience levels (e.g., 'developing', 'experienced in')\n"
                        "4. Focus on transferable skills and actual achievements\n"
                        "5. Maintain honesty about capabilities and growth areas\n"
                        "6. Address key job requirements directly\n"
                        "7. Acknowledge any experience gaps professionally\n"
                        "8. Use experience match data to frame qualifications accurately\n"
                        "Return a JSON object with: greeting, opening_paragraph, body_paragraphs[], "
                        "closing_paragraph, signature, keywords_used[]"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Profile: {profile}\n"
                        f"Job Requirements: {job_requirements.model_dump()}\n"
                        f"Profile Match: {profile_match.model_dump()}\n"
                        f"ATS Analysis: {ats_analysis.model_dump()}"
                    )
                }
            ]
            
            return self._create_completion(messages, OPENAI_MODELS["cover_letter"])
            
        except Exception as e:
            self.logger.error(f"Cover letter generation failed: {str(e)}")
            raise

    def _get_experience_context(self, profile: Dict[str, Any], job_requirements: JobRequirement) -> str:
        """Generate context about candidate's experience relative to job requirements."""
        context = []
        
        # Get experience durations
        current_role = None
        total_experience = timedelta(0)
        
        for exp in profile.get('professional_experience', []):
            start_date, end_date = self._parse_employment_period(exp.get('employment_period', ''))
            if start_date and end_date:
                if end_date >= datetime.now() - timedelta(days=30):
                    current_role = exp
                duration = end_date - start_date
                total_experience += duration
        
        # Add experience context
        if total_experience.days > 0:
            context.append(f"Total professional experience: {total_experience.days / 365:.1f} years")
        
        if current_role:
            context.append(f"Current role: {current_role['position']} at {current_role['company']}")
        
        # Add certification context
        recent_certs = [
            cert for cert in profile.get('certifications', [])
            if self._is_recent_cert(cert.get('date_obtained', ''))
        ]
        if recent_certs:
            context.append("Recent certifications: " + 
                          ", ".join(cert['name'] for cert in recent_certs))
        
        return "\n".join(context)

    def _get_skill_matches(self, profile_match: ProfileMatch, ats_analysis: KeywordMatch) -> str:
        """Generate context about skill matches and gaps."""
        context = []
        
        # Add match scores
        if profile_match.technical_requirements_match:
            context.append("Technical skill matches:")
            for category, score in profile_match.technical_requirements_match.items():
                if score > 0:
                    context.append(f"- {category}: {score:.0%}")
        
        # Add keyword matches
        if ats_analysis.matched_keywords:
            strong_matches = [
                kw['word'] for kw in ats_analysis.matched_keywords 
                if kw.get('strength', 0) >= 4
            ][:3]  # Top 3 strong matches
            if strong_matches:
                context.append("Strong skill matches: " + ", ".join(strong_matches))
        
        # Add areas for improvement
        if profile_match.areas_for_improvement:
            context.append("Growth areas: " + 
                          ", ".join(profile_match.areas_for_improvement[:2]))
        
        return "\n".join(context)

    def _parse_employment_period(self, period: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Parse employment period string into start and end dates."""
        try:
            start_str, end_str = period.split(" - ")
            
            def parse_date_part(date_str: str) -> Optional[datetime]:
                if date_str.lower() in ('current', 'present'):
                    return datetime.now()
                
                for fmt in ('%m/%Y', '%Y/%m', '%Y-%m', '%m-%Y', '%Y'):
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
                return None
            
            return parse_date_part(start_str), parse_date_part(end_str)
        except Exception:
            return None, None

    def _is_recent_cert(self, date_str: str) -> bool:
        """Check if a certification is recent (within last 6 months)."""
        try:
            for fmt in ('%Y', '%Y/%m', '%Y-%m', '%Y/%m/%d', '%Y-%m-%d'):
                try:
                    cert_date = datetime.strptime(date_str, fmt)
                    return cert_date >= datetime.now() - timedelta(days=180)
                except ValueError:
                    continue
            return False
        except Exception:
            return False

    def _get_job_context(self, job_requirements: JobRequirement) -> str:
        """Generate context about the job requirements and level."""
        context = []
        
        # Get required experience level
        exp_reqs = job_requirements.required_qualifications.get('Education / Experience', [])
        for req in exp_reqs:
            if 'year' in req.lower():
                context.append(f"Required experience: {req}")
                break
        
        # Get key technical requirements
        tech_reqs = job_requirements.technical_requirements.get('technical', [])
        if tech_reqs:
            context.append("Key technical requirements: " + ", ".join(tech_reqs))
        
        # Get tools/technologies
        tools = job_requirements.technical_requirements.get('tools', [])
        if tools:
            context.append("Required tools: " + ", ".join(tools))
        
        # Get key responsibilities
        responsibilities = []
        for category, resp_list in job_requirements.key_responsibilities.items():
            responsibilities.extend(resp_list)
        if responsibilities:
            context.append("Key responsibilities:")
            for resp in responsibilities[:3]:  # Top 3 responsibilities
                context.append(f"- {resp}")
        
        return "\n".join(context)

    def _analyze_experience_match(self, profile: Dict[str, Any], job_requirements: JobRequirement) -> str:
        """Analyze how candidate's experience matches job requirements."""
        context = []
        
        # Get required years from job requirements
        required_years = 0
        for req in job_requirements.required_qualifications.get('Education / Experience', []):
            if 'year' in req.lower():
                try:
                    # Extract number from string like "4 years of experience"
                    required_years = float(''.join(c for c in req if c.isdigit() or c == '.'))
                    break
                except ValueError:
                    continue
        
        # Calculate total relevant experience
        relevant_experience = timedelta(0)
        related_experience = timedelta(0)
        
        # Get required skills
        required_skills = set()
        for category in job_requirements.technical_requirements.values():
            required_skills.update(skill.lower() for skill in category)
        
        for exp in profile.get('professional_experience', []):
            start_date, end_date = self._parse_employment_period(exp.get('employment_period', ''))
            if not (start_date and end_date):
                continue
            
            duration = end_date - start_date
            
            # Check skill overlap
            exp_skills = {skill.lower() for skill in exp.get('skills_acquired', [])}
            skill_overlap = len(required_skills & exp_skills)
            
            if skill_overlap >= len(required_skills) / 2:
                # More than half of required skills - count as directly relevant
                relevant_experience += duration
            elif skill_overlap > 0:
                # Some skill overlap - count as related experience
                related_experience += duration * 0.5  # Count at half weight
        
        total_relevant_years = (relevant_experience.days + related_experience.days) / 365
        
        # Generate context about experience match
        if required_years > 0:
            context.append(f"Experience match: {total_relevant_years:.1f} years relevant experience vs {required_years} years required")
            
            if total_relevant_years >= required_years:
                context.append("Meeting experience requirement")
            else:
                context.append(f"Growing towards experience requirement (currently at {(total_relevant_years/required_years)*100:.0f}%)")
        
        # Break down experience types
        if relevant_experience.days > 0:
            context.append(f"Directly relevant experience: {relevant_experience.days/365:.1f} years")
        if related_experience.days > 0:
            context.append(f"Related experience: {related_experience.days/365:.1f} years")
        
        return "\n".join(context)
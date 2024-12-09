from typing import Dict, Any, List
from .base_agent import BaseAgent
from .models import ATSAnalysis, KeywordMatch
from config.model_settings import OPENAI_MODELS

class ATSAnalyzer(BaseAgent[ATSAnalysis]):
    """Agent for analyzing job descriptions for ATS optimization."""
    
    def __init__(self):
        super().__init__(ATSAnalysis)
        self.logger.debug("Initialized ATSAnalyzer")
    
    def extract_keywords(self, job_data: Dict[str, Any]) -> ATSAnalysis:
        """Extract and categorize important keywords from job description."""
        self.logger.info("Extracting ATS keywords...")
        
        messages = [
            {
                "role": "system",
                "content": (
                    "Analyze the job description and extract keywords for ATS optimization. "
                    "Return a JSON object with these exact fields:\n"
                    "{\n"
                    "  \"technical_keywords\": [{\"name\": \"string\", \"weight\": number}],\n"
                    "  \"soft_skills\": [{\"name\": \"string\", \"weight\": number}],\n"
                    "  \"industry_terms\": [{\"name\": \"string\", \"weight\": number}],\n"
                    "  \"certifications\": [{\"name\": \"string\", \"weight\": number}],\n"
                    "  \"tools_and_technologies\": [{\"name\": \"string\", \"weight\": number}]\n"
                    "}"
                )
            },
            {
                "role": "user",
                "content": f"Extract ATS keywords from this job posting:\n{job_data}"
            }
        ]
        
        return self._create_completion(messages, OPENAI_MODELS["ats_analysis"])
    
    def analyze_keyword_matches(self, ats_keywords: ATSAnalysis, profile: Dict[str, Any]) -> KeywordMatch:
        """Analyze how well the profile matches identified keywords and calculate ATS score."""
        self.logger.info("Analyzing keyword matches...")
        
        # Temporarily store the current response model
        original_model = self.response_model
        
        try:
            # Set the response model to KeywordMatch for this method
            self.response_model = KeywordMatch
            
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Analyze how the candidate profile matches the ATS keywords. "
                        "Calculate an ATS score based on the percentage of matched keywords. "
                        "Return a JSON object with these exact fields:\n"
                        "{\n"
                        "  \"matched_keywords\": [{\"word\": \"string\", \"context\": \"string\", \"strength\": number}],\n"
                        "  \"missing_keywords\": [{\"word\": \"string\", \"importance\": number}],\n"
                        "  \"overall_match_score\": number,\n"
                        "  \"optimization_suggestions\": [\"string\"],\n"
                        "  \"ats_score\": number\n"
                        "}"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Compare profile against these ATS keywords:\n"
                        f"Keywords: {ats_keywords.model_dump_json()}\n"
                        f"Profile: {profile}"
                    )
                }
            ]
            
            keyword_match = self._create_completion(messages, OPENAI_MODELS["ats_analysis"])
            
            # Calculate ATS score
            total_keywords = len(ats_keywords.technical_keywords) + len(ats_keywords.soft_skills) + \
                             len(ats_keywords.industry_terms) + len(ats_keywords.certifications) + \
                             len(ats_keywords.tools_and_technologies)
            
            matched_keywords = len(keyword_match.matched_keywords)
            ats_score = (matched_keywords / total_keywords) * 100 if total_keywords > 0 else 0
            
            keyword_match.ats_score = ats_score
            
            return keyword_match
            
        finally:
            # Restore the original response model
            self.response_model = original_model
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the input data and return results."""
        self.logger.info("Processing ATS analysis...")
        
        ats_keywords = self.extract_keywords(input_data)
        profile = input_data.get('profile', {})
        keyword_matches = self.analyze_keyword_matches(ats_keywords, profile)
        
        return {
            'ats_keywords': ats_keywords,
            'keyword_matches': keyword_matches
        }
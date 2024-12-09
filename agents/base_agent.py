from abc import ABC, abstractmethod
from typing import Dict, Any, TypeVar, Generic, TypedDict, List
from pydantic import BaseModel
import yaml
import logging
from pathlib import Path
from config.model_settings import OPENAI_MODELS, MODEL_CONFIG
from openai import OpenAI
import json
from time import perf_counter

T = TypeVar('T', bound=BaseModel)

class SkillsDict(TypedDict):
    technical: List[str]
    management: List[str]
    soft: List[str]

class ProcessedProfile(TypedDict):
    personal_information: dict
    professional_experience: List[dict]
    skills: SkillsDict
    certifications: List[dict]
    education: List[dict]  # Empty but typed
    languages: List[dict]
    work_preferences: dict

class BaseAgent(ABC, Generic[T]):
    """Base class for all agents in the workflow."""
    
    def __init__(self, response_model: type[T]):
        self.name = self.__class__.__name__
        self.root_dir = Path(__file__).parent.parent
        self.logger = logging.getLogger(f"Agent.{self.name}")
        self.default_model = OPENAI_MODELS["default"]
        self.default_config = MODEL_CONFIG
        self.response_model = response_model
        self.client = OpenAI()
        
        # Add detailed debug logging
        self.logger.debug(f"Initializing {self.name}")
        self.logger.debug(f"Root directory: {self.root_dir}")
        self.logger.debug(f"Default model: {self.default_model}")
        self.logger.debug(f"Model config: {self.default_config}")
        self.logger.debug(f"Response model: {response_model.__name__}")

    def _create_completion(self, messages: List[Dict[str, str]], model: str) -> T:
        """Create a completion with timing and response logging."""
        try:
            start_time = perf_counter()
            self.logger.debug(f"Starting API call to model: {model}")
            
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                **self.default_config
            )
            
            elapsed_time = perf_counter() - start_time
            self.logger.info(f"API call completed in {elapsed_time:.2f} seconds")
            
            response_json = json.loads(completion.choices[0].message.content)
            self.logger.debug(f"Raw response: {json.dumps(response_json, indent=2)}")
            
            return self.response_model.model_validate(response_json)
            
        except Exception as e:
            self.logger.error(f"Error in {self.name} API call: {str(e)}")
            raise
    
    def load_yaml(self, filepath: Path) -> Dict[str, Any]:
        """Load data from a YAML file."""
        self.logger.info(f"Loading YAML file: {filepath}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self.logger.debug(f"Successfully loaded YAML from {filepath}")
                self.logger.debug(f"YAML content keys: {data.keys() if data else 'None'}")
                return data
        except Exception as e:
            self.logger.error(f"Error loading YAML file: {str(e)}")
            raise
    
    def _clean_yaml_content(self, content: str) -> str:
        """Clean YAML content by removing code block markers."""
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            start_idx = 0
            end_idx = len(lines)
            
            for i, line in enumerate(lines):
                if line.startswith("```"):
                    if start_idx == 0:
                        start_idx = i + 1
                    else:
                        end_idx = i
                        break
            
            content = "\n".join(lines[start_idx:end_idx]).strip()
        
        return content
    
    def _preprocess_profile_data(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess profile data with proper typing."""
        processed = {
            'personal_information': profile.get('personal_information', {}),
            'professional_experience': profile.get('professional_experience', []),
            'skills': {
                'technical': profile.get('skills', {}).get('technical', []),
                'management': profile.get('skills', {}).get('management', []),
                'soft': profile.get('skills', {}).get('soft', [])
            },
            'certifications': profile.get('certifications', []),
            'education': profile.get('education', []),
            'languages': profile.get('languages', []),
            'work_preferences': profile.get('work_preferences', {})
        }
        
        # Debug log the processed data
        self.logger.debug(f"Preprocessed profile data: {json.dumps(processed, indent=2)}")
        self.logger.debug(f"Number of professional experiences: {len(processed['professional_experience'])}")
        
        return processed
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the input data and return results."""
        pass
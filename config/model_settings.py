"""Configuration settings for AI models."""

# OpenAI Model Settings
OPENAI_MODELS = {
    "default": "gpt-4-turbo-preview",
    "job_analysis": "gpt-4-turbo-preview",
    "profile_match": "gpt-4-turbo-preview",
    "validation": "gpt-4-turbo-preview",
    "ats_analysis": "gpt-4-turbo-preview",
    "resume": "gpt-4-turbo-preview",
    "cover_letter": "gpt-4-turbo-preview"
}

# Model Configuration
MODEL_CONFIG = {
    "temperature": 0.1,
    "response_format": {"type": "json_object"},
    "max_tokens": 4096,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0
}


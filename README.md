# AI Resume Generator

An intelligent resume generation system that uses AI to analyze job descriptions and create tailored resumes. The system employs multiple specialized AI agents to analyze job requirements, match candidate profiles, and generate optimized resumes.

## Features

- 🔍 **Job Analysis**: Automatically extracts key requirements and qualifications from job descriptions.
- 🎯 **Profile Matching**: Evaluates candidate profiles against job requirements.
- 📝 **Resume Generation**: Creates tailored resumes highlighting relevant experience.
- ✅️ **Cover Letter Generation**: Generates ATS-optimized cover letters that address missing keywords.
- ✅ **Quality Validation**: Ensures generated content meets quality standards.
- 📊 **Detailed Reporting**: Provides match scores and improvement suggestions.
- 🎨 **ATS Optimization**: Analyzes and optimizes resumes for Applicant Tracking Systems.
- 🎨 **Rich Terminal Interface**: User-friendly CLI with progress indicators.

## Prerequisites

- Python 3.9+
- OpenAI API key (GPT-4 access required)
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-resume-generator.git
   cd ai-resume-generator
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your OpenAI API key:
   ```bash
   export OPENAI_API_KEY='your-api-key-here'  # On Windows: set OPENAI_API_KEY=your-api-key-here
   ```

## Usage

1. Create your profile:
   - Copy `data/about_me_template.yaml` to `data/about_me.yaml`.
   - Fill in your information following the template structure.

2. Add job description:
   - Copy `data/about_job_template.yaml` to `data/about_job.yaml`.
   - Add the job details you're applying for.

3. Run the generator:
   ```bash
   python resume_generator.py
   ```

4. Find your results:
   - Generated resume and cover letter will be in the `output` directory.
   - Check the terminal for a summary.
   - Review `logs/resume_generation.log` for detailed information.

## Project Structure

```
ai-resume-generator/
├── agents/                 # AI agent modules
│   ├── base_agent.py      # Base agent class
│   ├── job_analyzer.py    # Job requirements analysis
│   ├── profile_matcher.py # Profile matching logic
│   ├── resume_generator.py# Resume generation
│   ├── validation_agent.py# Content validation
│   └── models.py          # Data models
├── config/                # Configuration files
│   ├── logging_config.py  # Logging setup
│   └── model_settings.py  # AI model settings
├── data/                  # Data templates and files
│   ├── about_me_template.yaml
│   └── about_job_template.yaml
├── logs/                  # Log files
├── output/                # Generated results
├── requirements.txt       # Project dependencies
├── resume_generator.py    # Main CLI application
└── workflow_manager.py    # Workflow orchestration
```

## Configuration

- Adjust AI model settings in `config/model_settings.py`.
- Modify logging preferences in `config/logging_config.py`.
- Templates in the `data/` directory provide structure for input files.

## Development

For development work:

1. Install all dependencies (including optional ones):
   ```bash
   pip install -r requirements.txt
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Format code:
   ```bash
   black .
   ```

4. Type checking (with enhanced type stubs):
   ```bash
   mypy .
   ```

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Push to the branch.
5. Create a Pull Request.

## Free and Open

This project is completely free and open for anyone to use, modify, and distribute as they see fit. No restrictions or attribution required.

## Acknowledgments

- OpenAI for providing the GPT-4 API
- Rich library for terminal interface
- PyYAML and ruamel.yaml for YAML processing
- Pydantic for data validation
- python-docx for document generation

## Support

For support, please open an issue in the GitHub repository. 
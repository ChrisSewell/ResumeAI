#!/usr/bin/env python3
"""
Resume Generator CLI
A production-ready tool that uses AI agents to generate tailored resumes.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
import shutil
import yaml
from typing import Optional, List, Dict, Any
import os

from workflow_manager import WorkflowManager
from agents.models import ResumeValidationResult
from config.logging_config import setup_logging
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
from document_generator.resume_formatter import ResumeDocumentGenerator
from document_generator.cover_letter_generator import CoverLetterDocumentGenerator
from openai import OpenAI
from agents.base_agent import BaseAgent
from agents.models import (
    WorkExperience, 
    ValidatedResume, 
    ProfileMatch, 
    JobRequirement, 
    KeywordMatch, 
    PersonalInformation, 
    Certification,
    CoverLetter
)
import json

def clear_terminal():
    """Clear the terminal screen based on OS."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(console: Console):
    """Print the application header."""
    console.print("\n[bold cyan]╭──────────────────────────────────╮[/bold cyan]")
    console.print("[bold cyan]│      AI Resume Generator         │[/bold cyan]")
    console.print("[bold cyan]╰──────────────────────────────────╯[/bold cyan]")
    # Add a divider line after the header
    console.print("[dim]─" * 50 + "[/dim]\n")

def clear_output_directory(output_dir: Path) -> None:
    """Clear all files in the output directory."""
    logger = logging.getLogger(__name__)
    logger.info("Clearing output directory...")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(exist_ok=True)

def find_job_file(data_dir: Path) -> Optional[Path]:
    """Find the about_job.yaml file in the data directory."""
    job_file = data_dir / "about_job.yaml"
    if job_file.exists():
        return job_file
    return None

def save_results(resume: ValidatedResume, cover_letter: CoverLetter, ats_analysis: KeywordMatch, output_dir: Path) -> Path:
    """Save the workflow results to a YAML file."""
    logger = logging.getLogger(__name__)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"analysis_result_{timestamp}.yaml"
    
    # Combine results and convert to dict for YAML serialization
    full_results = {
        'resume': resume.model_dump(),
        'cover_letter': cover_letter.model_dump(),
        'ats_analysis': ats_analysis.model_dump()
    }
    
    with open(output_file, 'w') as f:
        yaml.safe_dump(full_results, f, default_flow_style=False)
    
    logger.debug(f"Results saved to: {output_file}")
    return output_file

def print_summary(resume: ValidatedResume, cover_letter: CoverLetter, ats_analysis: KeywordMatch) -> None:
    """Print a user-friendly summary of the workflow results."""
    console = Console()
    
    # Create summary panel
    summary_text = f"""
    [bold]✅ Resume Generation Complete[/bold]

    [bold]ATS Analysis:[/bold]
    ATS Score: {round(ats_analysis.ats_score)}%
    Matched Keywords: {len(ats_analysis.matched_keywords)}
    Missing Keywords: {len(ats_analysis.missing_keywords)}
    Overall Match Score: {ats_analysis.overall_match_score}
    
    [bold]Optimization Suggestions:[/bold]
    """
    
    suggestions_text = "\n".join(f"• {sugg}" for sugg in ats_analysis.optimization_suggestions)
    
    # Add cover letter summary
    cover_letter_text = f"""
    [bold]Cover Letter:[/bold]
    Keywords Used: {len(cover_letter.keywords_used)}
    """
    
    console.print(Panel(
        summary_text + suggestions_text + cover_letter_text,
        title="Resume Analysis Results",
        border_style="green",
        padding=(1, 2)
    ))

def parse_args():
    """Parse command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(
        description="AI-powered resume generator that tailors resumes to job descriptions."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory to save generated resumes (default: output)"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Directory containing job and profile data (default: data)"
    )
    return parser.parse_args()

def main() -> int:
    """Main workflow execution function."""
    # Clear the terminal
    clear_terminal()
    
    args = parse_args()
    logger = setup_logging()
    console = Console()
    
    try:
        # Hide INFO logs from libraries
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)
        
        print_header(console)
        
        # Initialize paths and find job file
        with console.status("[bold cyan]Initializing Agent Network...", spinner="dots"):
            logger.debug("Initializing system...")
            root_dir = Path(__file__).parent
            data_dir = root_dir / args.data_dir
            output_dir = root_dir / args.output_dir
            clear_output_directory(output_dir)
            
            # Find job file
            job_file = find_job_file(data_dir)
            if not job_file:
                console.print("\n[red]❌ Error:[/red] about_job.yaml not found in data directory")
                return 1
            
            logger.debug(f"Using job file: {job_file}")
            
            # Initialize workflow manager
            workflow = WorkflowManager()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            refresh_per_second=4,
            expand=True,
            transient=False
        ) as progress:
            task = progress.add_task("\n", total=None)  # Add newline before first task
            
            try:
                # Job Analysis Phase
                progress.update(
                    task, 
                    description="\n[bold blue]🔍 Job Analysis Agent[/bold blue] analyzing requirements...\n"
                )
                job_data = workflow.job_analyzer.load_yaml(job_file)
                job_requirements = workflow.job_analyzer.process(job_data)
                
                # Profile Matching Phase
                progress.update(
                    task, 
                    description="\n[bold green]🎯 Profile Matcher[/bold green] calculating match...\n"
                )
                about_me = workflow.profile_matcher.load_yaml("data/about_me.yaml")
                processed_profile = workflow.profile_matcher._preprocess_profile_data(about_me)
                profile_match = workflow.profile_matcher.process(job_requirements, processed_profile)
                
                # ATS Analysis Phase
                progress.update(
                    task, 
                    description="\n[bold cyan]🎯 ATS Analysis Agent[/bold cyan] analyzing keywords...\n"
                )
                ats_analysis = workflow.ats_analyzer.extract_keywords(job_data)
                keyword_matches = workflow.ats_analyzer.analyze_keyword_matches(ats_analysis, processed_profile)
                
                # Resume Generation Phase
                progress.update(
                    task, 
                    description="\n[bold magenta]📝 Resume Generation Agent[/bold magenta] crafting resume...\n"
                )
                resume = workflow.resume_generator.process(
                    profile=processed_profile,
                    profile_match=profile_match,
                    job_requirements=job_requirements,
                    ats_analysis=keyword_matches
                )
                
                # Cover Letter Generation Phase
                progress.update(
                    task, 
                    description="\n[bold yellow]✍️ Cover Letter Agent[/bold yellow] writing cover letter...\n"
                )
                cover_letter = workflow.cover_letter_generator.process({
                    'profile': about_me,
                    'job_requirements': job_requirements,
                    'profile_match': profile_match,
                    'ats_analysis': keyword_matches
                })
                
                # Generate documents
                progress.update(
                    task, 
                    description="\n[bold cyan]📄 Generating documents...\n"
                )
                
                doc_generator = ResumeDocumentGenerator()
                resume_doc_path = doc_generator.generate(
                    resume_data=resume,
                    job_requirements=job_requirements,
                    output_path=Path(args.output_dir)
                )
                
                cover_letter_doc_path = workflow.cover_letter_doc_generator.generate(
                    cover_letter=cover_letter,
                    company_name=job_data['job_listing']['company'],
                    output_path=Path(args.output_dir)
                )
                
                # Save results
                output_file = save_results(resume, cover_letter, keyword_matches, output_dir)
                
                # Update final message with more visual appeal
                progress.update(
                    task, 
                    description="\n[bold green]✨ Process Complete![/bold green] Documents generated successfully.\n"
                )
                
            except Exception as e:
                # More descriptive error message with visual consistency
                progress.update(
                    task, 
                    description="\n[bold red]❌ Error:[/bold red] " + 
                              f"[red]{str(e)}[/red]\n"
                )
                raise
        
        # Add a divider with some spacing
        console.print("\n[dim]" + "─" * 50 + "[/dim]\n")
        
        # Print user-friendly summary
        print_summary(resume, cover_letter, keyword_matches)
        
        # Add file info with consistent formatting and icons
        console.print("\n[bold]📁 Generated Files:[/bold]")
        console.print(f"[dim]📊 Analysis: {output_file}[/dim]")
        console.print(f"[dim]📄 Resume:   {resume_doc_path}[/dim]")
        console.print(f"[dim]✉️  Letter:   {cover_letter_doc_path}[/dim]")
        
        # Add final spacing
        console.print()
        
        return 0
        
    except Exception as e:
        console.print(f"\n[red bold]🚨 Error:[/red bold] {str(e)}")
        logger.exception("Detailed error information:")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
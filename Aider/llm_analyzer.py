import os
import json
import time
from groq import Groq
from dotenv import load_dotenv
from github_link_analyzer import GitHubLinkAnalyzer
from document_parser import DocumentParser
import numpy as np
from contextlib import suppress
load_dotenv()

import logging

# Configure logger
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)



class LLMAnalyzer:
    """
    extract_candidate_name: Extracts the candidate's name from a resume
    job_title: Extracts the job title from a job description
    analyze_resume_and_jd: Analyzes a resume and job description
    save_or_update_candidate_analysis: Saves or updates the candidate analysis in
    a MongoDB database
    """
    
    def __init__(self, db=None):
        
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        
        
        
        self.db = db
    
    

    def extract_candidate_name(self, resume_text: str) -> str:
        
        from contextlib import suppress

        with suppress(Exception):
            name_extraction = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert at extracting candidate names from resumes. Return ONLY the full name of the candidate, with no additional text or explanation."
                    },
                    {
                        "role": "user", 
                        "content": f"""
                        Extract the full name of the candidate from the following resume text:

                        {resume_text}

                        Instructions:
                        - Return ONLY the candidate's full name
                        - If no clear name is found, return 'Unknown Candidate'
                        - Do not include any additional text or explanation
                        - Prioritize the most professional or complete name format
                        """
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0,
                max_tokens=50  
            ).choices[0].message.content.strip()

            
            if not name_extraction or name_extraction.lower() == 'unknown candidate':
                return 'Unknown Candidate'
        
            return name_extraction
        return 'Unknown Candidate'
         






    from contextlib import suppress

    def job_title(self, jd_text: str) -> str:
       
        with suppress(Exception):
          
            title_extraction = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert at extracting job titles from job descriptions. Return ONLY the job title, with no additional text or explanation."
                    },
                    {
                        "role": "user", 
                        "content": f"""
                        Extract the Job Title from the following Job Description text:

                        {jd_text}

                        Instructions:
                        - Return ONLY the Job Title 
                        - If no clear title is found, return 'Unknown Title'
                        - Do not include any additional text or explanation
                        - Prioritize the most professional or complete title format
                        """
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0,
                max_tokens=50  
            ).choices[0].message.content.strip()
            
            
            if not title_extraction or title_extraction.lower() == 'unknown title':
                return 'Unknown Title'
            return title_extraction
        return 'Unknown Title'


    from contextlib import suppress

    def analyze_resume_and_jd(self, resume_text: str, jd_text: str, resume_pdf: str) -> tuple:
        try:
            # Initialize with default values
            candidate_name = self.extract_candidate_name(resume_text)
            job_title = self.job_title(jd_text)
            
            # Get GitHub analysis
            github_analyser = GitHubLinkAnalyzer()
            github_analysis = github_analyser.process_github_projects(resume_pdf, jd_text)
            
            # Get embeddings
            generate_embeddings = DocumentParser()
            embeddings = generate_embeddings.get_embeddings(jd_text)
            
            # Perform primary analysis
            try:
                with open('prompt1.txt', 'r') as f:
                    prompt_template = f.read()

                primary_analysis = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a professional HR recruiter analyzing resumes."},
                        {"role": "user", "content": f"""
                        Analyze the following resume and job description:
                        
                        Job Description:
                            {jd_text}

                        Resume:
                            {resume_text}

                        {prompt_template}
                        """}
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0
                ).choices[0].message.content
                
                if not primary_analysis:
                    primary_analysis = "Error: No analysis was generated"
            except Exception as e:
                logger.error(f"Error in primary analysis: {e}")
                primary_analysis = f"Error performing analysis: {str(e)}"

            job_data = {
                "Job Title": job_title, 
                "candidate_name": candidate_name,
                "analysis_text": primary_analysis,
                "github_analysis": github_analysis,
                "job_description": jd_text,
                "resume": resume_text,
                "embeddings": embeddings
            }
            
            return primary_analysis, job_data, github_analysis, embeddings
            
        except Exception as e:
            logger.error(f"Error in analyze_resume_and_jd: {e}")
            return (
                f"Error analyzing resume: {str(e)}", 
                None,
                None,
                None
            )

    

    
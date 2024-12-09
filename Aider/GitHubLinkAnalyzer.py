import fitz  # PyMuPDF
import re
import requests
import logging
from typing import List, Dict, Optional
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitHubLinkAnalyzer:
    def __init__(self):
        """
        Initialize the GitHub Link Analyzer with Groq client
        """
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    
    def extract_links_from_pdf(self, pdf_path: str) -> List[str]:
        """
        Extract all links from a PDF file using PyMuPDF
        
        :param pdf_path: Path to the PDF file
        :return: List of unique extracted links
        """
        try:
            # Open the PDF
            doc = fitz.open(pdf_path)
            
            # Set to store unique links
            all_links = set()
            
            # Iterate through all pages
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Get links from the page
                page_links = page.get_links()
                
                # Extract and store URI links
                for link in page_links:
                    if link.get('uri'):
                        all_links.add(link['uri'])
            
            # Close the document
            doc.close()
            
            return list(all_links)
        
        except Exception as e:
            logger.error(f"Error extracting links from PDF: {e}")
            return []
    
    def filter_github_links(self, links: List[str]) -> List[str]:
        """
        Filter out GitHub repository links
        
        :param links: List of all links
        :return: List of GitHub repository links
        """
        # Regex pattern to match GitHub repository URLs
        github_pattern = r'^https?://(?:www\.)?github\.com/[a-zA-Z0-9-]+/[a-zA-Z0-9-]+(?:/)?$'
        
        github_links = [
            link for link in links 
            if re.match(github_pattern, link) and 
               not link.endswith('/blob/') and 
               not link.endswith('/tree/')
        ]
        
        return list(set(github_links))
    
    def fetch_readme(self, github_link: str) -> Optional[str]:
        """
        Fetch README file from a GitHub repository
        
        :param github_link: GitHub repository URL
        :return: README content or None
        """
        try:
            # Possible README locations
            readme_urls = [
                github_link.replace('https://github.com/', 'https://raw.githubusercontent.com/') + '/main/README.md',
                github_link.replace('https://github.com/', 'https://raw.githubusercontent.com/') + '/master/README.md',
                github_link.rstrip('/') + '/raw/main/README.md',
                github_link.rstrip('/') + '/raw/master/README.md'
            ]
            
            for readme_url in readme_urls:
                try:
                    logger.info(f"Attempting to fetch README from: {readme_url}")
                    response = requests.get(readme_url, timeout=10)
                    
                    if response.status_code == 200:
                        logger.info("README successfully fetched")
                        return response.text
                
                except requests.RequestException as e:
                    logger.warning(f"Error fetching README from {readme_url}: {e}")
            
            logger.warning(f"No README found for {github_link}")
            return None
        
        except Exception as e:
            logger.error(f"Unexpected error in fetch_readme: {e}")
            return None
    
    def analyze_readme(self, readme_content: str, github_link: str, jd_text: str) -> str:
        """
        Analyze README using Groq's Llama 3.1 70B model
        
        :param readme_content: README content to analyze
        :param github_link: Repository URL for context
        :param jd_text: Job description text
        :return: Analysis results
        """
        if not readme_content:
            return "No README content available for analysis."
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert software project analyzer. Provide a comprehensive, structured analysis of the project README."
                    },
                    {
                        "role": "user",
                        "content": f"""Analyze the GitHub repository README:

                            Repository URL: {github_link}

                            Job Description Context:
                            {jd_text}

                            README Content:
                            {readme_content}

                            Please provide a detailed analysis with:
                            1. Project Overview
                            2. Key Technologies and Frameworks
                            3. Technical Complexity
                            4. Relevance to Job Description
                            5. Skills Demonstrated
                            6. Potential Interview Discussion Points

                            Format your response in clear, structured markdown."""
                    }
                ],
                model="llama-3.1-70b-versatile",
                max_tokens=1024,
                temperature=0.5
            )
            
            analysis = chat_completion.choices[0].message.content
            return analysis
        
        except Exception as e:
            logger.error(f"Error in README analysis for {github_link}: {e}")
            return f"Error in README analysis: {e}"
    
    def process_github_projects(self, resume_pdf: str, jd_text: str) -> Dict[str, Dict]:
        """
        Process GitHub projects from a PDF resume
        
        :param resume_pdf: Path to the PDF resume
        :param jd_text: Job description text
        :return: Dictionary of analyzed GitHub projects
        """
        # Extract all links from PDF
        all_links = self.extract_links_from_pdf(resume_pdf)
        
        # Filter GitHub repository links
        github_links = self.filter_github_links(all_links)
        
        # Store analysis results
        project_analyses = {}
        
        # Process each GitHub link
        for link in github_links:
            try:
                logger.info(f"Processing GitHub repository: {link}")
                
                # Fetch README content
                readme_content = self.fetch_readme(link)
                
                # If README exists, analyze it
                if readme_content:
                    readme_analysis = self.analyze_readme(readme_content, link, jd_text)
                    
                    project_analyses[link] = {
                        'readme_content': readme_content,
                        'analysis': readme_analysis
                    }
                else:
                    project_analyses[link] = {
                        'readme_content': None,
                        'analysis': "No README found for this repository."
                    }
            
            except Exception as e:
                logger.error(f"Error processing {link}: {e}")
                project_analyses[link] = {
                    'readme_content': None,
                    'analysis': f"Error processing repository: {e}"
                }
        
        return project_analyses
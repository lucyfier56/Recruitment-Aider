import fitz  # PyMuPDF
import re
import requests
import logging
from typing import List, Dict, Optional
from groq import Groq
import os
from contextlib import suppress
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitHubLinkAnalyzer:
    """
    extract_links_from_pdf: Extracts all links from a PDF file
    filter_github_links: Filters GitHub repository links from a list of links
    fetch_readme: Fetches the README content from a GitHub repository
    analyze_readme: Analyzes the README content of a GitHub repository
    """
    
    def __init__(self):
        
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    
    def extract_links_from_pdf(self, pdf_path: str) -> List[str]:
        try:
            logger.debug(f"Opening PDF file: {pdf_path}")
            with fitz.open(pdf_path) as doc:
                all_links = []
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    links = page.get_links()
                    logger.debug(f"Page {page_num}: Found {len(links)} links")
                    for link in links:
                        if 'uri' in link:
                            all_links.append(link['uri'])
                
                unique_links = list(dict.fromkeys(all_links))
                logger.debug(f"Total unique links found: {len(unique_links)}")
                return unique_links
        except Exception as e:
            logger.error(f"Error extracting links from PDF: {str(e)}")
            return []
    
    def filter_github_links(self, links: List[str]) -> List[str]:
        github_pattern = r'^https?://(?:www\.)?github\.com/[a-zA-Z0-9-]+/[a-zA-Z0-9-]+(?:/)?$'
        
        try:
            logger.debug(f"Filtering {len(links)} links")
            github_links = [
                link for link in links 
                if re.match(github_pattern, link) and 
                not link.endswith('/blob/') and 
                not link.endswith('/tree/')
            ]
            logger.debug(f"Found {len(github_links)} GitHub links: {github_links}")
            return github_links
        except Exception as e:
            logger.error(f"Error filtering GitHub links: {str(e)}")
            return []
    
    def fetch_readme(self, github_link: str) -> Optional[str]:
        
        readme_urls = [
            github_link.replace('https://github.com/', 'https://raw.githubusercontent.com/') + '/main/README.md',
            github_link.replace('https://github.com/', 'https://raw.githubusercontent.com/') + '/master/README.md',
            github_link.rstrip('/') + '/raw/main/README.md',
            github_link.rstrip('/') + '/raw/master/README.md'
        ]
        
        for readme_url in readme_urls:
            with suppress(requests.RequestException):
                logger.info(f"Attempting to fetch README from: {readme_url}")
                response = requests.get(readme_url, timeout=10)
                
                if response.status_code == 200:
                    logger.info("README successfully fetched")
                    return response.text
        
        logger.warning(f"No README found for {github_link}")
        return None

    
    

    def analyze_readme(self, github_link: str, jd_text: str) -> str:
        readme_content = self.fetch_readme(github_link)
            
        if not readme_content:
            return "No README content available for analysis."
        
        try:
            with suppress(Exception):
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
                    model="llama-3.3-70b-versatile",
                    max_tokens=1024,
                    temperature=0
                )
                
                analysis = chat_completion.choices[0].message.content
                return analysis
        
        except Exception as e:
            logger.error(f"Error in README analysis for {github_link}: {e}")
            return f"Error in README analysis: {e}"

    
    from contextlib import suppress

    def process_github_projects(self, resume_file, jd_text: str) -> Dict[str, Dict]:
        
        try:
            file_content = resume_file.read()
            
            doc = fitz.open(stream=file_content, filetype="pdf")
            
            all_links = []
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                links = page.get_links()
                logger.debug(f"Found {len(links)} links on page {page_num}")
                for link in links:
                    if 'uri' in link:
                        all_links.append(link['uri'])
                        logger.debug(f"Found link: {link['uri']}")
            
            doc.close()
            
            resume_file.seek(0)
            
    
            github_links = self.filter_github_links(all_links)
            logger.info(f"Found {len(github_links)} GitHub links: {github_links}")
            
            if not github_links:
                logger.info("No GitHub links found in the resume")
                return {}
                
            project_analyses = {}
            
            for link in github_links:
                try:
                    logger.info(f"Processing GitHub repository: {link}")
                    
                    project_analyses[link] = {}
                    
                    # Fetch and analyze README
                    readme_content = self.fetch_readme(link)
                    
                    if readme_content:
                        # Fixed: Passing correct parameters to analyze_readme
                        analysis = self.analyze_readme(link, jd_text)
                        project_analyses[link]['readme_content'] = readme_content
                        project_analyses[link]['analysis'] = analysis
                    else:
                        project_analyses[link]['readme_content'] = None
                        project_analyses[link]['analysis'] = "No README found for this repository."
                        
                except Exception as e:
                    logger.error(f"Error processing repository {link}: {str(e)}")
                    project_analyses[link] = {
                        'readme_content': None,
                        'analysis': f"Error analyzing repository: {str(e)}"
                    }
            
            return project_analyses
            
        except Exception as e:
            logger.error(f"Error in process_github_projects: {str(e)}")
            return {}
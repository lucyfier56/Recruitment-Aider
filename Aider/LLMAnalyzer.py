import os
import json
import time
from groq import Groq
from dotenv import load_dotenv
from GitHubLinkAnalyzer import GitHubLinkAnalyzer
from DocumentParser import DocumentParser
import numpy as np
from contextlib import suppress
load_dotenv()



class LLMAnalyzer:
    """
    extract_candidate_name: Extracts the candidate's name from a resume
    job_title: Extracts the job title from a job description
    analyze_resume_and_jd: Analyzes a resume and job description
    save_or_update_candidate_analysis: Saves or updates the candidate analysis in
    a MongoDB database
    """
    
    def __init__(self, output_dir='analysis_results', db=None):
        
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        
        
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
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
                model="llama-3.1-70b-versatile",
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
                model="llama-3.1-70b-versatile",
                temperature=0,
                max_tokens=50  
            ).choices[0].message.content.strip()
            
            
            if not title_extraction or title_extraction.lower() == 'unknown title':
                return 'Unknown Title'
            return title_extraction
        return 'Unknown Title'


    from contextlib import suppress

    def analyze_resume_and_jd(self, resume_text: str, jd_text: str, resume_pdf: str) -> str:
        
        candidate_name = 'Unknown Candidate'
        job_title = 'Unknown Title'
        github_analysis = "No Analysis Available"
        primary_analysis = "Analysis Failed"
        embeddings = []

        
        with suppress(Exception):
            
            candidate_name = self.extract_candidate_name(resume_text)

        with suppress(Exception):
            
            job_title = self.job_title(jd_text)

        with suppress(Exception):
            
            github_analyser = GitHubLinkAnalyzer()
            github_analysis = github_analyser.process_github_projects(resume_pdf, jd_text)

        with suppress(Exception):
            
            generate_embeddings = DocumentParser()
            embeddings = generate_embeddings.get_embeddings(jd_text)

        with suppress(Exception):
            
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
                model="llama-3.1-70b-versatile",
                temperature=0
            ).choices[0].message.content

        job_data = {
            "Job Title": job_title, 
            "candidate_name": candidate_name,
            "analysis_text": primary_analysis,
            "github_analysis": github_analysis,
            "job_description": jd_text,
            "resume": resume_text,
            "embeddings": embeddings
        }
        
        return job_data.get('analysis_text', None), job_data, github_analysis

    

    def save_or_update_candidate_analysis(self, db, job_data):
        
        if not db:
            print("MongoDB database connection is not established")
            return

        try:
            recruitment_db = db['recruitment_database']
            job_roles_collection = recruitment_db['job_roles']

            
            job_title = job_data.get("Job Title")
            candidate_name = job_data.get("candidate_name")
            job_description = job_data.get('job_description', '')
            current_embeddings = job_data.get('embeddings')

            
            if job_title is None or not job_title:
                print("Missing job title")
                return
            
            if candidate_name is None or not candidate_name:
                print("Missing candidate name")
                return
            if current_embeddings is None:
                print("Missing embeddings")
                return
            if not job_description:
                print("Missing job description")
                return

            
            candidate_doc = {
                'name': candidate_name,
                'resume': job_data.get('resume', ''),
                'analysis': job_data.get('analysis_text', ''),
                'github_projects': job_data.get('github_analysis', '')
            }

            def calculate_embedding_similarity(embedding1, embedding2):
                
                try:
                    from numpy import dot
                    from numpy.linalg import norm
                    import numpy as np
                    
                    
                    e1 = np.array(embedding1, dtype=np.float64)
                    e2 = np.array(embedding2, dtype=np.float64)
                    
                    
                    if e1.ndim != 1 or e2.ndim != 1:
                        e1 = e1.flatten()
                        e2 = e2.flatten()
                    
                    
                    if e1.size == 0 or e2.size == 0:
                        return 0.0
                    
                    
                    similarity = dot(e1, e2) / (norm(e1) * norm(e2))
                    return float(similarity)
                except Exception as e:
                    print(f"Error calculating embedding similarity: {e}")
                    return 0.0

            existing_job = job_roles_collection.find_one({"title": job_title})

            if existing_job:
                SIMILARITY_THRESHOLD = 0.95
                matching_description = None

                for desc in existing_job.get('descriptions', []):
                    similarity = calculate_embedding_similarity(current_embeddings, desc['embeddings'])
                    if similarity >= SIMILARITY_THRESHOLD:
                        matching_description = desc
                        break

                if matching_description:
                    existing_candidate = next(
                        (c for c in matching_description.get('candidates', []) 
                        if c['name'] == candidate_name),
                        None
                    )

                    if existing_candidate:
                        result = job_roles_collection.update_one(
                            {
                                "title": job_title,
                                "descriptions.text": matching_description['text'],
                                "descriptions.candidates.name": candidate_name
                            },
                            {"$set": {
                                "descriptions.$[desc].candidates.$[cand]": candidate_doc
                            }},
                            array_filters=[
                                {"desc.text": matching_description['text']},
                                {"cand.name": candidate_name}
                            ]
                        )
                    else:
                        
                        result = job_roles_collection.update_one(
                            {
                                "title": job_title,
                                "descriptions.text": matching_description['text']
                            },
                            {"$push": {
                                "descriptions.$.candidates": candidate_doc
                            }}
                        )
                else:
                    embeddings_list = current_embeddings.tolist() if hasattr(current_embeddings, 'tolist') else current_embeddings
                    new_description = {
                        "text": job_description,
                        "embeddings": embeddings_list,
                        "candidates": [candidate_doc]
                    }
                    result = job_roles_collection.update_one(
                        {"title": job_title},
                        {"$push": {"descriptions": new_description}}
                    )
            else:
                embeddings_list = current_embeddings.tolist() if hasattr(current_embeddings, 'tolist') else current_embeddings
                new_job = {
                    "title": job_title,
                    "descriptions": [{
                        "text": job_description,
                        "embeddings": embeddings_list,
                        "candidates": [candidate_doc]
                    }]
                }
                result = job_roles_collection.insert_one(new_job)

            print(f"Successfully processed {candidate_name} for {job_title}")

        except Exception as e:
            print(f"Error processing job role and candidate data in MongoDB: {e}")
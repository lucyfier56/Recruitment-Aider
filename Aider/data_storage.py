import datetime
import tempfile
from pymongo import MongoClient
from typing import Dict, Any
import numpy as np
from scipy.spatial.distance import cosine
from document_parser import DocumentParser
from llm_analyzer import LLMAnalyzer
from io import BytesIO
from github_link_analyzer import GitHubLinkAnalyzer
import os
import re

import logging

logger = logging.getLogger(__name__)

class RecruitmentDataStorage:
    def __init__(self, connection_string: str):
        try:
            self.client = MongoClient(connection_string)
            print("We are here!")
            self.db = self.client['recruitment_db']
            self.jobs_collection = self.db['jobs']
            # Test connection
            self.client.admin.command('ping')
            print("Connected to MongoDB successfully!")
        except Exception as e:
            print(f"MongoDB connection error: {e}")
            raise

    def _convert_numpy_to_list(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert NumPy arrays to lists in the dictionary"""
        converted_data = data.copy()
        for key, value in converted_data.items():
            if isinstance(value, np.ndarray):
                converted_data[key] = value.tolist()
            elif isinstance(value, dict):
                converted_data[key] = self._convert_numpy_to_list(value)
        return converted_data
    
    def find_similar_job(self, embeddings: list, job_role: str, threshold: float = 0.9) -> Dict[str, Any]:
        # Only get the job with matching role
        job = self.jobs_collection.find_one({"job_role": job_role})
        
        if not job:
            return None
            
        embeddings_array = np.array(embeddings)
        
        # Check each JD in the matching job role
        for jd in job.get('job_descriptions', []):
            stored_embeddings = np.array(jd.get('embeddings', []))
            if len(stored_embeddings) > 0:
                similarity = 1 - cosine(embeddings_array, stored_embeddings)
                
                if similarity >= threshold:
                    return job
        
        return None
    
    def add_jobrole(self, job_role: str, department: str, worktype: str, salary: str, required_experience: str) -> Dict[str, Any]:
        job = self.jobs_collection.find_one({"job_role": job_role})
        if job:
            return job
        else:
            job_data = {
                "job_role": job_role,
                "department": department,
                "worktype": worktype,
                "salary": salary,
                "required_experience": required_experience,
            }
            result = self.jobs_collection.insert_one(job_data)
            return self.jobs_collection.find_one({"_id": result.inserted_id})
    
    def upload_jd(self, job_role: str, job_description: str, location: str, title: str) -> Dict[str, Any]:
        # First check if the job role exists
        job = self.jobs_collection.find_one({"job_role": job_role})
        
        parse = DocumentParser()
        embeddings = parse.get_embeddings(job_description)
        embeddings = embeddings.tolist() if isinstance(embeddings, np.ndarray) else []
        
        new_jd = {
            "title": title,
            "location": location,
            "job_description": job_description,
            "embeddings": embeddings,
            "created_at": datetime.datetime.utcnow()
        }
        
        # If job role exists, check for similar JDs
        if job:
            similar_job = self.find_similar_job(embeddings, job_role)  # Pass job_role to limit search
            if similar_job:
                return {
                    "status": "duplicate",
                    "message": "Similar job description already exists for this role",
                    "data": self._convert_mongodb_doc(similar_job),
                    "total_jds": len(similar_job.get("job_descriptions", []))
                }
            
            # No similar JD found, add new one to existing role
            self.jobs_collection.update_one(
                {"_id": job["_id"]},
                {"$push": {"job_descriptions": new_jd}} if "job_descriptions" in job 
                else {"$set": {"job_descriptions": [new_jd]}}
            )
            
            updated_job = self.jobs_collection.find_one({"_id": job["_id"]})
            return {
                "status": "updated",
                "message": "New job description added to existing job role",
                "data": self._convert_mongodb_doc(updated_job),
                "total_jds": len(updated_job.get("job_descriptions", []))
            }
        
        # If job role doesn't exist, create new role and add JD
        else:
            job_data = {
                "job_role": job_role,
                "job_descriptions": [new_jd]
            }
            result = self.jobs_collection.insert_one(job_data)
            created_job = self.jobs_collection.find_one({"_id": result.inserted_id})
            
            return {
                "status": "created",
                "message": "New job role and job description created",
                "data": self._convert_mongodb_doc(created_job),
                "total_jds": 1
            }
    
    
    def _convert_mongodb_doc(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        if doc is None:
            return None
        
        doc_copy = doc.copy()
        
        for key, value in doc_copy.items():
            if key == "_id":
                doc_copy[key] = str(value)
            elif isinstance(value, datetime.datetime):
                doc_copy[key] = value.isoformat()
            elif isinstance(value, list):
                doc_copy[key] = [self._convert_mongodb_doc(item) if isinstance(item, dict) else item for item in value]
            elif isinstance(value, dict):
                doc_copy[key] = self._convert_mongodb_doc(value)
            
        return doc_copy
    
    def upload_resume(self, job_role: str, resume_content: str, pdf_content: bytes = None, job_title: str = None) -> Dict[str, Any]:
        if not job_role or not isinstance(job_role, str):
            return {"status": "error", "message": "Invalid job role provided"}
        
        if not job_title:
            return {"status": "error", "message": "Job title is required"}
        
        # Case-insensitive search
        job = self.jobs_collection.find_one({
            "job_role": {
                "$regex": f"^{re.escape(job_role)}$",
                "$options": "i"  # case-insensitive
            }
        })
        
        if not job or not job.get("job_descriptions"):
            # Debug logging
            logger.debug(f"Searching for job role: {job_role}")
            logger.debug(f"Available jobs: {[j['job_role'] for j in self.jobs_collection.find()]}")
            return {
                "status": "error", 
                "message": f"Job role '{job_role}' not found or no descriptions. Available roles: {[j['job_role'] for j in self.jobs_collection.find()]}"
            }

        # Find matching job description by title
        matching_jd = None
        for jd in job.get("job_descriptions", []):
            if jd.get("title", "").lower() == job_title.lower():
                matching_jd = jd
                break
        
        if not matching_jd:
            available_titles = [jd.get("title", "") for jd in job.get("job_descriptions", [])]
            return {
                "status": "error",
                "message": f"Job title '{job_title}' not found. Available titles: {', '.join(available_titles)}"
            }

        try:
            parse = DocumentParser()
            embeddings = parse.get_embeddings(resume_content)
            embeddings = embeddings.tolist() if isinstance(embeddings, np.ndarray) else []
            
            llm_analyzer = LLMAnalyzer()
            candidate_name = llm_analyzer.extract_candidate_name(resume_content)
            
            # Extract GitHub links from the original PDF content
            github_links = []
            if pdf_content:
                try:
                    with tempfile.NamedTemporaryFile(suffix='.pdf', mode='wb', delete=False) as temp_pdf:
                        temp_pdf.write(pdf_content)
                        temp_pdf.flush()
                        
                        github_analyzer = GitHubLinkAnalyzer()
                        logger.debug(f"Processing PDF file: {temp_pdf.name}")
                        links = github_analyzer.extract_links_from_pdf(temp_pdf.name)
                        logger.debug(f"Extracted links: {links}")
                        github_links = github_analyzer.filter_github_links(links)
                        logger.debug(f"Filtered GitHub links: {github_links}")
                        
                    os.unlink(temp_pdf.name)
                    
                except Exception as e:
                    logger.error(f"Error extracting GitHub links from PDF: {str(e)}")

            candidate_data = {
                "candidate_name": candidate_name,
                "resume_content": resume_content,
                "embeddings": embeddings,
                "github_links": github_links,
                "uploaded_at": datetime.datetime.utcnow()
            }

           
            jd_index = next(
                (i for i, jd in enumerate(job["job_descriptions"]) 
                if jd.get("title", "").lower() == job_title.lower()),
                None
            )

            if "candidates" in job["job_descriptions"][jd_index]:
                existing_candidates = job["job_descriptions"][jd_index]["candidates"]
                existing_candidate = next(
                    (c for c in existing_candidates if c["candidate_name"] == candidate_name),
                    None
                )
                
                if existing_candidate:
                    update_query = {
                        "_id": job["_id"],
                        f"job_descriptions.{jd_index}.candidates.candidate_name": candidate_name
                    }
                    update_operation = {
                        "$set": {
                            f"job_descriptions.{jd_index}.candidates.$": candidate_data
                        }
                    }
                    self.jobs_collection.update_one(update_query, update_operation)
                    status = "updated"
                    message = "Candidate information updated successfully"
                else:
                    update_query = {"_id": job["_id"]}
                    update_operation = {
                        "$push": {
                            f"job_descriptions.{jd_index}.candidates": candidate_data
                        }
                    }
                    self.jobs_collection.update_one(update_query, update_operation)
                    status = "created"
                    message = "New candidate added successfully"
            else:
                update_query = {"_id": job["_id"]}
                update_operation = {
                    "$set": {
                        f"job_descriptions.{jd_index}.candidates": [candidate_data]
                    }
                }
                self.jobs_collection.update_one(update_query, update_operation)
                status = "created"
                message = "First candidate added successfully"

            updated_job = self.jobs_collection.find_one({"_id": job["_id"]})
            
            return {
                "status": status,
                "message": message,
                "data": self._convert_mongodb_doc(updated_job),
                "candidate_name": candidate_name,
                "github_links": github_links
            }

        except Exception as e:
            logger.error(f"Resume upload error: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to process resume: {str(e)}"
            }


    def store_analysis(self, job_role: str, candidate_name: str, job_title: str) -> Dict[str, Any]:
        try:
            logger.debug(f"Starting analysis for candidate: {candidate_name}, job role: {job_role}, job title: {job_title}")
            
            # Case-insensitive job role search
            job = self.jobs_collection.find_one({
                "job_role": {
                    "$regex": f"^{re.escape(job_role)}$",
                    "$options": "i"
                }
            })
            
            if not job:
                logger.error(f"Job not found for role: {job_role}")
                return {"status": "failed", "message": "Job role not found"}
            
            matching_jd = None
            jd_index = None
            for idx, jd in enumerate(job.get("job_descriptions", [])):
                if jd.get("title", "").lower() == job_title.lower():
                    matching_jd = jd
                    jd_index = idx
                    break
                    
            if not matching_jd:
                logger.error(f"Job description not found for title: {job_title}")
                return {"status": "failed", "message": "Job description not found"}
                
            jd_text = matching_jd.get("job_description", "")
            if not jd_text:
                logger.error("Job description text is empty")
                return {"status": "failed", "message": "Job description text is empty"}
                
            candidate = next(
                (c for c in matching_jd.get("candidates", []) 
                if c["candidate_name"].lower() == candidate_name.lower()),
                None
            )
            
            if not candidate:
                logger.error(f"Candidate not found: {candidate_name}")
                return {"status": "failed", "message": "Candidate not found"}

            analyzer = LLMAnalyzer()
            analysis_result = analyzer.analyze_resume_and_jd(
                jd_text=jd_text,
                resume_text=candidate["resume_content"]
            )

            github_analyzer = GitHubLinkAnalyzer()
            
            analysis = {
                "analyses": [
                    {
                        "type": "candidate_analysis",
                        "content": analysis_result["analysis_text"]
                    }
                ],
                "github_links": candidate.get("github_links", [])
            }

            github_links = candidate.get("github_links", [])
            if github_links:
                try:
                    all_github_analyses = []
                    for link in github_links:
                        try:
                            repo_analysis = github_analyzer.analyze_readme(
                                github_link=link, 
                                jd_text=jd_text
                            )
                            if repo_analysis:
                                all_github_analyses.append(f"Analysis for {link}:\n{repo_analysis}")
                        except Exception as repo_error:
                            logger.error(f"Error analyzing GitHub repository {link}: {str(repo_error)}", exc_info=True)
                            all_github_analyses.append(f"Failed to analyze {link}: {str(repo_error)}")
                    
                    # Combine all analyses
                    if all_github_analyses:
                        analysis["analyses"].append({
                            "type": "github_analysis",
                            "content": "\n\n".join(all_github_analyses)
                        })
                    
                except Exception as e:
                    error_msg = f"Error processing GitHub repositories: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    analysis["analyses"].append({
                        "type": "github_analysis_error",
                        "content": error_msg
                    })

            update_query = {"_id": job["_id"]}
            update_operation = {
                "$set": {
                    f"job_descriptions.{jd_index}.candidates.$[cand].analysis": analysis
                }
            }
            array_filters = [
                {"cand.candidate_name": candidate["candidate_name"]}
            ]
            
            result = self.jobs_collection.update_one(
                update_query,
                update_operation,
                array_filters=array_filters
            )
            
            if result.modified_count == 0:
                logger.error("Failed to update analysis in database")
                return {"status": "error", "message": "Failed to store analysis in database"}

            updated_job = self.jobs_collection.find_one({"_id": job["_id"]})
            return {
                "status": "success",
                "message": "Analysis completed and stored successfully",
                "data": self._convert_mongodb_doc(updated_job),
                "candidate_name": candidate_name
            }

        except Exception as e:
            logger.error(f"Error in store_analysis: {str(e)}", exc_info=True)
            return {"status": "error", "message": f"Failed to store analysis: {str(e)}"}
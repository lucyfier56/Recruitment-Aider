from pymongo import MongoClient
from typing import Dict, Any
import numpy as np
from scipy.spatial.distance import cosine

class RecruitmentDataHandler:
    def __init__(self, connection_string: str):
        try:
            self.client = MongoClient(connection_string)
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

    def find_similar_job(self, embeddings: list, threshold: float = 0.9) -> Dict[str, Any]:
        all_jobs = self.jobs_collection.find({})
        
        embeddings_array = np.array(embeddings)
        for job in all_jobs:
            stored_embeddings = np.array(job['embeddings'])
            similarity = 1 - cosine(embeddings_array, stored_embeddings)
            
            if similarity >= threshold:
                return job
        
        return None

    def process_job_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            print("Original job data:", job_data)
            job_data = self._convert_numpy_to_list(job_data)
            print("Converted job data:", job_data)
            
            similar_job = self.find_similar_job(job_data["embeddings"])
            print("Similar job found:", similar_job)
            
            if similar_job:
                candidate = self.find_candidate(similar_job["_id"], job_data["candidate_name"])
                print("Existing candidate found:", candidate)
                
                if candidate:
                    self.update_candidate_analysis(similar_job["_id"], job_data)
                    return {
                        "status": "updated",
                        "job_id": str(similar_job["_id"]),
                        "message": "Candidate analysis updated"
                    }
                else:
                    self.add_candidate_to_job(similar_job["_id"], job_data)
                    return {
                        "status": "added",
                        "job_id": str(similar_job["_id"]),
                        "message": "New candidate added to existing job"
                    }
            else:
                job_id = self.create_new_job(job_data)
                return {
                    "status": "created",
                    "job_id": job_id,
                    "message": "New job created with first candidate"
                }
        except Exception as e:
            print(f"Error processing job data: {e}")
            raise

    # Rest of the methods remain the same as in previous version
    def find_candidate(self, job_id: str, candidate_name: str) -> Dict[str, Any]:
        job = self.jobs_collection.find_one(
            {
                "_id": job_id,
                "candidates.candidate_name": candidate_name
            },
            {"candidates.$": 1}
        )
        return job['candidates'][0] if job else None

    def update_candidate_analysis(self, job_id: str, candidate_data: Dict[str, Any]) -> None:
        self.jobs_collection.update_one(
            {
                "_id": job_id,
                "candidates.candidate_name": candidate_data["candidate_name"]
            },
            {
                "$set": {
                    "candidates.$.analysis_text": candidate_data["analysis_text"],
                    "candidates.$.github_analysis": candidate_data["github_analysis"],
                    "candidates.$.resume": candidate_data["resume"]
                }
            }
        )

    def add_candidate_to_job(self, job_id: str, candidate_data: Dict[str, Any]) -> None:
        candidate_info = {
            "candidate_name": candidate_data["candidate_name"],
            "analysis_text": candidate_data["analysis_text"],
            "github_analysis": candidate_data["github_analysis"],
            "resume": candidate_data["resume"]
        }
        
        self.jobs_collection.update_one(
            {"_id": job_id},
            {"$push": {"candidates": candidate_info}}
        )

    def create_new_job(self, job_data: Dict[str, Any]) -> str:
        try:
            job_document = {
                "job_title": job_data.get("Job Title"),
                "job_description": job_data.get("job_description"),
                "embeddings": job_data.get("embeddings"),
                "candidates": [{
                    "candidate_name": job_data.get("candidate_name"),
                    "analysis_text": job_data.get("analysis_text"),
                    "github_analysis": job_data.get("github_analysis"),
                    "resume": job_data.get("resume")
                }]
            }
            print("Inserting job document:", job_document)
            result = self.jobs_collection.insert_one(job_document)
            print("Insert result:", result.inserted_id)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating new job: {e}")
            raise
        
        
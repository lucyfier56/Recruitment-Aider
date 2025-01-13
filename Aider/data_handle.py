from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()
import os
from typing import Optional, Dict, Any, List
import json
from bson import ObjectId
from datetime import datetime
import traceback

class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class DataHandle:
    def __init__(self, connection_string: str = None):
        try:
            self.connection_string = connection_string or os.getenv("MONGODB_CONNECTION_STRING")
            if not self.connection_string:
                raise ValueError("MongoDB connection string not provided")
            
            self.client = MongoClient(self.connection_string)
            self.db = self.client['recruitment_db']
            self.jobs_collection = self.db['jobs']
            # Test connection
            self.client.admin.command('ping')
            print("Connected to MongoDB successfully!")
        except Exception as e:
            print(f"MongoDB connection error: {e}")
            raise

    def verify_connection(self) -> bool:
        try:
            self.client.admin.command('ping')
            return True
        except Exception as e:
            print(f"Connection verification failed: {e}")
            return False

    def get_jobrole(self, role: str) -> Optional[Dict[str, Any]]:
        if not self.verify_connection():
            print("Database connection is not active")
            return None
        
        try:
            query = {"job_role": {"$regex": f"^{role}$", "$options": "i"}}
            result = self.jobs_collection.find_one(query)
            
            if result:
                return json.loads(json.dumps(result, cls=JsonEncoder))
            
            available_roles = self.jobs_collection.distinct("job_role")
            print(f"Job role '{role}' not found. Available roles: {available_roles}")
            return None
            
        except Exception as e:
            print(f"Error retrieving job role: {e}")
            print(f"Error type: {type(e)}")  
            return None

    def get_all_job_titles(self) -> Optional[List[str]]:
        if not self.verify_connection():
            print("Database connection is not active")
            return None
            
        try:
            pipeline = [
                {
                    "$unwind": {"path": "$job_descriptions", "preserveNullAndEmptyArrays": False}
                },
                {
                    "$project": {
                        "title": "$job_descriptions.title"
                    }
                },
                {
                    "$match": {
                        "title": {"$exists": True, "$ne": None}
                    }
                }
            ]
            
            results = list(self.jobs_collection.aggregate(pipeline))
            titles = [doc['title'] for doc in results if 'title' in doc]
            
            if not titles:
                print("No job titles found in the database")
            return titles
            
        except Exception as e:
            print(f"Error retrieving job titles: {e}")
            return None

    def get_job_titles_by_role(self, role: str) -> Optional[List[str]]:
        if not self.verify_connection():
            print("Database connection is not active")
            return None
            
        try:
            pipeline = [
                {
                    "$match": {
                        "job_role": {"$regex": f"^{role}$", "$options": "i"}
                    }
                },
                {
                    "$unwind": {"path": "$job_descriptions", "preserveNullAndEmptyArrays": False}
                },
                {
                    "$project": {
                        "title": "$job_descriptions.title"
                    }
                },
                {
                    "$match": {
                        "title": {"$exists": True, "$ne": None}
                    }
                }
            ]
            
            results = list(self.jobs_collection.aggregate(pipeline))
            titles = [doc['title'] for doc in results if 'title' in doc]
            
            if not titles:
                available_roles = self.jobs_collection.distinct("job_role")
                print(f"No job titles found for role '{role}'. Available roles: {available_roles}")
            return titles
            
        except Exception as e:
            print(f"Error retrieving job titles for role {role}: {e}")
            return None

    def list_available_roles(self) -> List[str]:
        try:
            roles = self.jobs_collection.distinct("job_role")
            return roles
        except Exception as e:
            print(f"Error retrieving available roles: {e}")
            return []
    
    def get_all_candidates(self) -> Optional[List[Dict[str, Any]]]:
        if not self.verify_connection():
            print("Database connection is not active")
            return None
            
        
        try:
            
            
            pipeline = [
                {"$unwind": "$job_descriptions"},
                {"$unwind": "$job_descriptions.candidates"},
                {"$project": {
                    "_id": 0,
                    "candidate_name": "$job_descriptions.candidates.candidate_name"
                }},
                {"$group": {
                    "_id": "$candidate_name"
                }}
            ]
            
            result = list(self.jobs_collection.aggregate(pipeline))
            
            candidate_names = [doc["_id"] for doc in result]
            
            return candidate_names
            
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return []


    class JsonEncoder(json.JSONEncoder):
        def default(self, obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            return super().default(obj)

    def get_candidates_by_job_role(self, job_role: str) -> Optional[List[Dict[str, Any]]]:
        
        try:
            initial_check = self.jobs_collection.find_one({"job_role": job_role})
            if not initial_check:
                print(f"No job found with role: {job_role}")
                return []

            pipeline_stages = [
                [{
                    "$match": {
                        "job_role": job_role
                    }
                }],
                
                [{
                    "$match": {
                        "job_role": job_role
                    }
                },
                {
                    "$unwind": "$job_descriptions"
                }],
                
                [{
                    "$match": {
                        "job_role": job_role
                    }
                },
                {
                    "$unwind": "$job_descriptions"
                },
                {
                    "$unwind": "$job_descriptions.candidates"
                },
                {
                    "$project": {
                        "candidate_name": "$job_descriptions.candidates.candidate_name",
                        "resume_content": "$job_descriptions.candidates.resume_content",
                        "uploaded_at": "$job_descriptions.candidates.uploaded_at",
                        "github_links": "$job_descriptions.candidates.github_links",
                        "analysis": "$job_descriptions.candidates.analysis"
                    }
                }]
            ]
            
            for i, pipeline in enumerate(pipeline_stages, 1):
                print(f"\nChecking pipeline stage {i}:")
                results = list(self.jobs_collection.aggregate(pipeline))
                print(f"Number of documents after stage {i}: {len(results)}")
                if len(results) > 0:
                    print(f"Sample document structure: {json.dumps(results[0], indent=2, cls=JsonEncoder)}")
                else:
                    print("No results at this stage")
                    
            final_results = list(self.jobs_collection.aggregate(pipeline_stages[-1]))
            return json.loads(json.dumps(final_results, cls=JsonEncoder)) if final_results else []
            
        except Exception as e:
            print(f"Error retrieving candidates for role {job_role}: {e}")
            return None

    def get_candidate_by_name(self, candidate_name: str) -> Optional[Dict[str, Any]]:

        try:
            pipeline = [
                {
                    "$unwind": "$job_descriptions"
                },
                {
                    "$unwind": "$job_descriptions.candidates"
                },
                {
                    "$match": {
                        "job_descriptions.candidates.candidate_name": candidate_name
                    }
                },
                {
                    "$project": {
                        "candidate_name": "$job_descriptions.candidates.candidate_name",
                        "resume_content": "$job_descriptions.candidates.resume_content",
                        "uploaded_at": "$job_descriptions.candidates.uploaded_at",
                        "github_links": "$job_descriptions.candidates.github_links",
                        "analysis": "$job_descriptions.candidates.analysis",
                        "job_role": 1,
                        "job_description_title": "$job_descriptions.title",
                        "job_location": "$job_descriptions.location"
                    }
                }
            ]
            
            result = list(self.jobs_collection.aggregate(pipeline))
            return json.loads(json.dumps(result[0], cls=JsonEncoder)) if result else None
        except Exception as e:
            print(f"Error retrieving candidate {candidate_name}: {e}")
            return None

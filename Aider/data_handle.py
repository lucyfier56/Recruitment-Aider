from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()
import os
from typing import Optional, Dict, Any, List
import json
from bson import ObjectId


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
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
            query = {"job_role": role}
            result = self.jobs_collection.find_one(query)
            
            if result:
                return json.loads(json.dumps(result, cls=JsonEncoder))
            return None
            
        except Exception as e:
            print(f"Error retrieving job role: {e}")
            return None
    def get_all_job_titles(self) -> Optional[List[str]]:
        
        try:
            pipeline = [
                {
                    "$unwind": "$job_descriptions"
                },
                {
                    "$project": {
                        "title": "$job_descriptions.title"
                    }
                }
            ]
            
            results = list(self.jobs_collection.aggregate(pipeline))
            return [doc['title'] for doc in results] if results else []
            
        except Exception as e:
            print(f"Error retrieving job titles: {e}")
            return None

    def get_job_titles_by_role(self, role: str) -> Optional[List[str]]:
       
        try:
            pipeline = [
                {
                    "$match": {"job_role": role}
                },
                {
                    "$unwind": "$job_descriptions"
                },
                {
                    "$project": {
                        "title": "$job_descriptions.title"
                    }
                }
            ]
            
            results = list(self.jobs_collection.aggregate(pipeline))
            return [doc['title'] for doc in results] if results else []
            
        except Exception as e:
            print(f"Error retrieving job titles for role {role}: {e}")
            return None

        
        

# def main():
#     """
#     Main function to demonstrate the usage of DataHandle class with Software Engineer role.
#     """
#     try:
#         # Initialize the data handler
#         data_handler = DataHandle()
        
#         # Search for Software Engineer role
#         job_data = data_handler.get_jobrole("Software Engineer")
        
#         if job_data:
#             print("\nJob Role Information:")
#             print("-" * 20)
#             print(f"Role: {job_data.get('job_role', 'N/A')}")
            
#             # Display job descriptions if available
#             if 'job_descriptions' in job_data:
#                 for i, desc in enumerate(job_data['job_descriptions'], 1):
#                     print(f"\nPosition {i}:")
#                     print(f"Title: {desc.get('title', 'N/A')}")
#                     print(f"Location: {desc.get('location', 'N/A')}")
                    
#                     # Display a truncated version of the job description
#                     job_desc = desc.get('job_description', 'N/A')
#                     if len(job_desc) > 100:
#                         job_desc = job_desc[:100] + "..."
#                     print(f"Description: {job_desc}")
#         else:
#             print("\nNo job information found for Software Engineer role")
            
#     except Exception as e:
#         print(f"\nAn error occurred in main: {e}")
#         return 1
        
    # return 0

# if __name__ == "__main__":
#     exit_code = main()
#     exit(exit_code)
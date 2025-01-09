import datetime
from io import BytesIO
import json
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException,Form
from typing import List, Dict, Any, Optional, Union
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel, Field
import os
import logging
from bson import ObjectId
from document_parser import DocumentParser
from llm_analyzer import LLMAnalyzer
from data_storage import RecruitmentDataStorage
from dotenv import load_dotenv
load_dotenv()
from data_handle import DataHandle

from logging import getLogger

from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class JsonEncoder(json.JSONEncoder):
    """
    """
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.decode('utf-8')
        return super().default(obj)

class StoreAnalysisInput(BaseModel):
    job_role: str = Field(..., description="Job role to analyze against")
    resume_content: str = Field(..., description="Resume content to analyze")

class StoreAnalysisResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]]
    candidate_analysis: Optional[Dict[str, Any]]
    candidate_name: Optional[str]
    total_candidates: Optional[int]
    job_id: Optional[str]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime.datetime: lambda v: v.isoformat()
        }

app = FastAPI()



class DirectJDInput(BaseModel):
    job_role: str
    jd_content: str = Field(..., description="Job description content - can include multiple lines")
    location: str
    title: str
    
    class Config:
        json_encoders = {
            str: lambda v: v.replace('\n', '\\n')
        }

class UploadJDInput(BaseModel):
    job_role: str
    location: str
    title: str

class ParseResponse(BaseModel):
    content_text: str
    message: str

class JDResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]]
    total_jds: Optional[int]
    job_id: Optional[str]
    similar_jd: Optional[Dict[str, Any]]

class ResumeUploadInput(BaseModel):
    job_role: str
    resume_content: str = Field(..., description="Resume content - can include multiple lines")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Recruitment Analyzer API",
    description="API for analyzing resumes against job descriptions",
    version="1.0.0"
)

class AnalysisResponse(BaseModel):
    candidate_name: str
    job_title: str
    analysis_text: str
    github_analysis: Dict[str, Any]
    job_description: str
    resume_text: str
    embeddings: List[float]


class JobRole(BaseModel):
    _id: str
    job_role: str
    department: str
    worktype: str
    salary: str
    require_experience:str
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str
        }
class JobResponse(BaseModel):
    job_role: str
    jd_content: str
    location: str
    title: str
    
class ResumeResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]]
    job_id: Optional[str]
    similar_resume: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime.datetime: lambda v: v.isoformat()
        }



class JobTitlesResponse(BaseModel):
    status: str
    message: str
    titles: List[str]
    total_titles: int

    class Config:
        arbitrary_types_allowed = True


class CandidateBase(BaseModel):
    candidate_name: str
    resume_content: str
    uploaded_at: datetime.datetime
    github_links: Optional[List[str]]
    job_role: str

class CandidateDetail(CandidateBase):
    analysis: Optional[Dict[str, Any]]

class CandidateResponse(BaseModel):
    status: str
    message: str
    data: Optional[Union[List[CandidateBase], CandidateDetail]]
    total_candidates: Optional[int]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime.datetime: lambda v: v.isoformat()
        }

document_parser = DocumentParser()



@app.post("/jobs/", response_model=JobResponse)
async def create_role(job : JobRole):
    try:
        connection_string = os.getenv("MONGODB_CONNECTION_STRING") 
        data_handle =RecruitmentDataStorage(connection_string)
        result = data_handle.add_jobrole(
            job_role = job.job_role,
            department = job.department,
            worktype = job.worktype,
            salary = job.salary,
            required_experience = job.require_experience
        )
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail = "Failed to create job role"
            )
        
        response_data = {
            "_id" : str(result["_id"]),
            "job_role" : result["job_role"],
            "department" : result["department"],
            "worktype" : result["worktype"],
            "salary" : result["salary"],
            "required_experience" : result["required_experience"]
        }
        
        return JSONResponse(
            status_code=200,
            content = response_data
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail = f"Failed to create job role: {str(e)}"
        )




@app.post("/jobs/upload-jd/file", response_model=JDResponse)
async def upload_jd_file(
    job_role: str = Form(...),
    location: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        
        content = await parse_uploaded_file(file)
        
        # Initialize LLMAnalyzer and get job title
        llm_analyzer = LLMAnalyzer()
        title = llm_analyzer.job_title(content)
        data_handle =RecruitmentDataStorage(os.getenv("MONGODB_URI"))
        
        result = data_handle.upload_jd(
            job_role=job_role,
            job_description=content,
            location=location,
            title=title
        )
        
        return JSONResponse(
            status_code=200,
            content=result
        )
    except Exception as e:
        logger.error(f"Error processing file upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process job description: {str(e)}"
        )

@app.post("/jobs/upload-jd/direct", response_model=JDResponse)
async def upload_jd_direct(job_input: DirectJDInput):
    try:
        data_handle =RecruitmentDataStorage(os.getenv("MONGODB_URI"))
        
        
        result = data_handle.upload_jd(
            job_role=job_input.job_role,
            job_description=job_input.jd_content,
            location=job_input.location,
            title=job_input.title
        )
        
        return JSONResponse(
            status_code=200,
            content=result
        )
    except Exception as e:
        logger.error(f"Error processing direct input: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process job description: {str(e)}"
        )

async def parse_uploaded_file(file: UploadFile) -> str:
    try:
        allowed_extensions = ['.pdf', '.docx', '.txt']
        
        if not file or not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Invalid or missing file"
            )
           
        extension = os.path.splitext(file.filename)[1].lower()
        
        if extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
            )
       
        content = await file.read()

        content_text = document_parser.extract_text_from_file(
            file=content, 
            filename=file.filename
        )
        
        
        if isinstance(content_text, tuple):
            content_text = content_text[0]
        if isinstance(content_text, bytes):
            content_text = content_text.decode('utf-8')
            
        logger.info("Document parsed successfully")
        return content_text

    except ValueError as e:
        logger.error(f"Parsing error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/jobs/upload-resume/file", response_model=ResumeResponse)
async def upload_resume(
    job_role: str = Form(...),
    job_title: str = Form(...),
    file: UploadFile = File(...)
):
    try:
       
        pdf_content = await file.read()
        file_obj = BytesIO(pdf_content)
        
        content_text, error_msg = document_parser.extract_text_from_file(
            file=file_obj,
            filename=file.filename
        )
        
        if error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
            
        if not content_text:
            raise HTTPException(status_code=400, detail="No content could be extracted from the file")
        
        data_handle =RecruitmentDataStorage(os.getenv("MONGODB_CONNECTION_STRING"))
        upload_result = data_handle.upload_resume(
            job_role=job_role,
            job_title=job_title,
            resume_content=content_text,
            pdf_content=pdf_content
        )
        
        if upload_result["status"] in ["created", "updated"]:
            analysis_result = data_handle.store_analysis(
                job_role=job_role,
                candidate_name=upload_result["candidate_name"],
                job_title=job_title
            )
            upload_result["analysis"] = analysis_result.get("candidate_analysis")
        
        return JSONResponse(status_code=200, content=upload_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process resume: {str(e)}")


@app.post("/analysis/store", response_model=StoreAnalysisResponse)
async def store_analysis(job_role: str, candidate_name: str, job_title: str):
    try:
        data_handle =RecruitmentDataStorage(os.getenv("MONGODB_CONNECTION_STRING"))
        
        result = data_handle.store_analysis(
            job_role=job_role,
            candidate_name=candidate_name,
            job_title=job_title
        )
        
        if result["status"] in ["failed", "error"]:
            raise HTTPException(
                status_code=400 if result["status"] == "failed" else 500,
                detail=result["message"]
            )
            
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store analysis: {str(e)}"
        )

@app.get("/jobs/{job_role}", response_model=JobResponse)
async def get_jobrole(job_role: str):
    try:
        
        data_handle = DataHandle(os.getenv("MONGODB_CONNECTION_STRING"))
        result = data_handle.get_jobrole(job_role)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Job role not found"
            )
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail = f"Failed to retrieve job role: {str(e)}"
        )

@app.get("/jobs/titles/all", response_model=JobTitlesResponse)
async def get_all_titles():
    try:
        data_handle = DataHandle(os.getenv("MONGODB_CONNECTION_STRING"))
        titles = data_handle.get_all_job_titles()
        
        if titles is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve job titles"
            )
            
        result = {
            "status": "success",
            "message": "Job titles retrieved successfully",
            "titles": titles,
            "total_titles": len(titles)
        }
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except Exception as e:
        logger.error(f"Error retrieving job titles: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve job titles: {str(e)}"
        )
    finally:
        data_handle.close_connection()

@app.get("/jobs/titles/{role}", response_model=JobTitlesResponse)
async def get_titles_by_role(role: str):
    try:
        data_handle = DataHandle(os.getenv("MONGODB_CONNECTION_STRING"))
        titles = data_handle.get_job_titles_by_role(role)
        
        if titles is None:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve job titles for role: {role}"
            )
            
        if not titles:
            raise HTTPException(
                status_code=404,
                detail=f"No job titles found for role: {role}"
            )
            
        result = {
            "status": "success",
            "message": f"Job titles for role '{role}' retrieved successfully",
            "titles": titles,
            "total_titles": len(titles)
        }
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job titles for role {role}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve job titles: {str(e)}"
        )
    finally:
        data_handle.close_connection()
        
        
@app.get("/candidates/all", response_model=CandidateResponse)
async def get_all_candidates():
    try:
        data_handle = DataHandle(os.getenv("MONGODB_CONNECTION_STRING"))
        candidates = data_handle.get_all_candidates()
        
        if candidates is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve candidates"
            )
            
        result = {
            "status": "success",
            "message": "Candidates retrieved successfully",
            "data": candidates,
            "total_candidates": len(candidates)
        }
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except Exception as e:
        logger.error(f"Error retrieving candidates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve candidates: {str(e)}"
        )
    finally:
        data_handle.close_connection()

@app.get("/candidates/{candidate_name}", response_model=CandidateResponse)
async def get_candidate_by_name(candidate_name: str):
    try:
        data_handle = DataHandle(os.getenv("MONGODB_CONNECTION_STRING"))
        candidate = data_handle.get_candidate_by_name(candidate_name)
        
        if not candidate:
            raise HTTPException(
                status_code=404,
                detail=f"Candidate not found: {candidate_name}"
            )
            
        result = {
            "status": "success",
            "message": f"Candidate {candidate_name} retrieved successfully",
            "data": candidate,
            "total_candidates": 1
        }
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving candidate {candidate_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve candidate: {str(e)}"
        )
    finally:
        data_handle.close_connection()

@app.get("/candidates/role/{job_role}", response_model=CandidateResponse)
async def get_candidates_by_role(job_role: str):
    try:
        data_handle = DataHandle(os.getenv("MONGODB_CONNECTION_STRING"))
        candidates = data_handle.get_candidates_by_job_role(job_role)
        
        if candidates is None:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve candidates for role: {job_role}"
            )
            
        if not candidates:
            raise HTTPException(
                status_code=404,
                detail=f"No candidates found for role: {job_role}"
            )
            
        result = {
            "status": "success",
            "message": f"Candidates for role '{job_role}' retrieved successfully",
            "data": candidates,
            "total_candidates": len(candidates)
        }
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving candidates for role {job_role}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve candidates: {str(e)}"
        )
    finally:
        data_handle.close_connection()
        

def get_all_candidates(self) -> Optional[List[Dict[str, Any]]]:
    """
    Retrieve all candidates from the database
    """
    try:
        pipeline = [
            {
                "$unwind": "$candidates"
            },
            {
                "$project": {
                    "candidate_name": "$candidates.candidate_name",
                    "resume_content": "$candidates.resume_content",
                    "uploaded_at": "$candidates.uploaded_at",
                    "github_links": "$candidates.github_links",
                    "job_role": "$job_role"
                }
            }
        ]
        
        results = list(self.jobs_collection.aggregate(pipeline))
        return json.loads(json.dumps(results, cls=JsonEncoder)) if results else []
            
    except Exception as e:
        print(f"Error retrieving candidates: {e}")
        return None

def get_candidate_by_name(self, candidate_name: str) -> Optional[Dict[str, Any]]:
   
    try:
        pipeline = [
            {
                "$unwind": "$candidates"
            },
            {
                "$match": {
                    "candidates.candidate_name": candidate_name
                }
            },
            {
                "$project": {
                    "candidate_name": "$candidates.candidate_name",
                    "resume_content": "$candidates.resume_content",
                    "uploaded_at": "$candidates.uploaded_at",
                    "github_links": "$candidates.github_links",
                    "analysis": "$candidates.analysis",
                    "job_role": "$job_role"
                }
            }
        ]
        
        result = list(self.jobs_collection.aggregate(pipeline))
        return json.loads(json.dumps(result[0], cls=JsonEncoder)) if result else None
            
    except Exception as e:
        print(f"Error retrieving candidate {candidate_name}: {e}")
        return None

def get_candidates_by_job_role(self, job_role: str) -> Optional[List[Dict[str, Any]]]:
   
    try:
        pipeline = [
            {
                "$match": {
                    "job_role": job_role
                }
            },
            {
                "$unwind": "$candidates"
            },
            {
                "$project": {
                    "candidate_name": "$candidates.candidate_name",
                    "resume_content": "$candidates.resume_content",
                    "uploaded_at": "$candidates.uploaded_at",
                    "github_links": "$candidates.github_links",
                    "analysis": "$candidates.analysis"
                }
            }
        ]
        
        results = list(self.jobs_collection.aggregate(pipeline))
        return json.loads(json.dumps(results, cls=JsonEncoder)) if results else []
            
    except Exception as e:
        print(f"Error retrieving candidates for role {job_role}: {e}")
        return None

        
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
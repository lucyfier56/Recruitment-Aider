import datetime
from io import BytesIO
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException,Form
from typing import List, Dict, Any, Optional
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel, Field
import os
import logging
from bson import ObjectId
from document_parser import DocumentParser
from llm_analyzer import LLMAnalyzer
from data_storage import RecruitmentDataHandler
from dotenv import load_dotenv
load_dotenv()

from logging import getLogger

from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

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

# Set up proper logging
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
        # Allow population by field name for MongoDB _id
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

document_parser = DocumentParser()



@app.post("/jobs/", response_model=JobResponse)
async def create_role(job : JobRole):
    try:
        connection_string = os.getenv("MONGODB_URI") 
        data_handle = RecruitmentDataHandler(connection_string)
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
        data_handle = RecruitmentDataHandler(os.getenv("MONGODB_URI"))
        
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
        data_handle = RecruitmentDataHandler(os.getenv("MONGODB_URI"))
        
        
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
        # Validate file types
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
        # Read the PDF content
        pdf_content = await file.read()
        file_obj = BytesIO(pdf_content)
        
        # Extract text content
        content_text, error_msg = document_parser.extract_text_from_file(
            file=file_obj,
            filename=file.filename
        )
        
        if error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
            
        if not content_text:
            raise HTTPException(status_code=400, detail="No content could be extracted from the file")
        
        data_handle = RecruitmentDataHandler(os.getenv("MONGODB_URI"))
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
        data_handle = RecruitmentDataHandler(os.getenv("MONGODB_URI"))
        
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
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
from sentence_transformers import SentenceTransformer
from llama_parse import LlamaParse
import os
from dotenv import load_dotenv
import docx
import PyPDF2
import numpy as np
from typing import Union
from pathlib import Path
import logging
from contextlib import suppress

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentParser:
    def __init__(self):
        load_dotenv()
        
        api_key = os.getenv('LLAMA_CLOUD_API_KEY')
        if not api_key:
            raise ValueError("LLAMA_CLOUD_API_KEY') not found in environment variables")
            
        self.parser = LlamaParse(
            api_key=api_key,
            result_type="markdown"
        )
        
        with suppress(Exception):
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            return
            
        logger.error("Error initializing embedding model")
        self.embedding_model = None

    def extract_text_from_file(self, file: Union[str, Path, bytes]) -> str:
        filename = getattr(file, 'name', 
                         file.filename if hasattr(file, 'filename') else str(file))
        file_extension = os.path.splitext(filename)[1].lower()
        
        with suppress(Exception):
            if file_extension == '.pdf':
                pdf_reader = PyPDF2.PdfReader(file)
                return " ".join([page.extract_text() for page in pdf_reader.pages])
                
            elif file_extension == '.docx':
                doc = docx.Document(file)
                return " ".join([paragraph.text for paragraph in doc.paragraphs])
                
            elif file_extension == '.txt':
                if hasattr(file, 'getvalue'):
                    return file.getvalue().decode('utf-8')
                elif hasattr(file, 'read'):
                    content = file.read()
                    return content.decode('utf-8') if isinstance(content, bytes) else content
                return str(file)
                    
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
        
        logger.error(f"Error parsing document {filename}")
        return ""

    def parse_resume(self, resume_file: Union[str, Path, bytes]) -> str:
        with suppress(Exception):
            resume_text = self.extract_text_from_file(resume_file)
            
            if not resume_text:
                resume_text = self.parser.parse(resume_file)
            
            return resume_text
        
        filename = getattr(resume_file, 'name', str(resume_file))
        logger.error(f"Error parsing resume: {filename}")
        return ""

    def parse_job_description(self, jd_file: Union[str, Path, bytes]) -> str:
        with suppress(Exception):
            jd_text = self.extract_text_from_file(jd_file)
            
            if not jd_text:
                jd_text = self.parser.parse(jd_file)
            
            return jd_text
        
        filename = getattr(jd_file, 'name', str(jd_file))
        logger.error(f"Error parsing job description: {filename}")
        return ""
    
    def get_embeddings(self, text: str) -> np.ndarray:
        with suppress(Exception):
            if self.embedding_model is None:
                logger.error("Embedding model not initialized")
                return np.array([])

            return self.embedding_model.encode(text)
        
        logger.error("Error generating embeddings")
        return np.array([])
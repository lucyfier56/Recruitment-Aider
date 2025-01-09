from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
import docx
import PyPDF2
import numpy as np
from typing import Union, Tuple
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentParser:
    def __init__(self):
        load_dotenv()
        
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing embedding model: {str(e)}")
            self.embedding_model = None

    def extract_text_from_file(self, file: Union[str, Path, bytes], filename: str) -> str:
        """Returns tuple of (extracted_text, error_message)"""
        file_extension = os.path.splitext(filename)[1].lower()
        
        try:
            if file_extension == '.pdf':
                print("file extension is indeed pdf")
                pdf_reader = PyPDF2.PdfReader(file)
                text = " ".join([page.extract_text() for page in pdf_reader.pages])
                
                if not text.strip():
                    return "", "PDF appears to be empty or unreadable"
                return text, ""
                
            elif file_extension == '.docx':
                doc = docx.Document(file)
                text = " ".join([paragraph.text for paragraph in doc.paragraphs])
                if not text.strip():
                    return "", "DOCX appears to be empty or unreadable"
                return text, ""
                
            elif file_extension == '.txt':
                if hasattr(file, 'getvalue'):
                    text = file.getvalue().decode('utf-8')
                elif hasattr(file, 'read'):
                    content = file.read()
                    text = content.decode('utf-8') if isinstance(content, bytes) else content
                else:
                    text = str(file)
                if not text.strip():
                    return "", "Text file appears to be empty"
                return text, ""
                    
            else:
                return "", f"Unsupported file type: {file_extension}"
        
        except Exception as e:
            error_msg = f"Error parsing {filename}: {str(e)}"
            logger.error(error_msg)
            return "", error_msg

    def parse_resume(self, resume_file: Union[str, Path, bytes], filename: str) -> str:
        logger.info(f"Starting to parse resume: {filename}")
        
        text, error = self.extract_text_from_file(resume_file, filename)
        if text:
            logger.info(f"Successfully extracted text from resume")
            return text
        else:
            logger.error(f"Failed to parse resume: {error}")
            raise ValueError(f"Failed to parse resume: {error}")

    def parse_job_description(self, jd_file: Union[str, Path, bytes], filename: str) -> str:
        logger.info(f"Starting to parse job description: {filename}")
        
        text, error = self.extract_text_from_file(jd_file, filename)
        if text:
            logger.info("Successfully extracted text from job description")
            return text
        else:
            logger.error(f"Failed to parse job description: {error}")
            raise ValueError(f"Failed to parse job description: {error}")
    
    def get_embeddings(self, text: str) -> np.ndarray:
        if not text.strip():
            logger.error("Cannot generate embeddings for empty text")
            return np.array([])
            
        if self.embedding_model is None:
            logger.error("Embedding model not initialized")
            return np.array([])

        try:
            return self.embedding_model.encode(text)
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return np.array([])
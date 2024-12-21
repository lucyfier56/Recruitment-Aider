from sentence_transformers import SentenceTransformer
from llama_parse import LlamaParse
import os
from dotenv import load_dotenv
import docx
import PyPDF2
import numpy as np

load_dotenv()

class DocumentParser:
    def __init__(self):
        self.parser = LlamaParse(
            api_key=os.getenv('LLAMA_PARSE_API_KEY'),
            result_type="markdown"
        )
        
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Error initializing embedding model: {e}")
            self.embedding_model = None

    def extract_text_from_file(self, file):
       
        filename = getattr(file, 'name', file.filename if hasattr(file, 'filename') else 'unknown')
        file_extension = os.path.splitext(filename)[1].lower()
        
        try:
            if file_extension == '.pdf':
                pdf_reader = PyPDF2.PdfReader(file)
                text = " ".join([page.extract_text() for page in pdf_reader.pages])
                
            elif file_extension == '.docx':
                doc = docx.Document(file)
                text = " ".join([paragraph.text for paragraph in doc.paragraphs])
                
            elif file_extension == '.txt':
                if hasattr(file, 'getvalue'):
                    text = file.getvalue().decode('utf-8')
                elif hasattr(file, 'read'):
                    text = file.read().decode('utf-8') if isinstance(file.read(), bytes) else file.read()
                else:
                    text = file
                    
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
                
            return text
            
        except Exception as e:
            print(f"Error parsing document: {e}")
            return ""

    def parse_resume(self, resume_file):
    
        try:
            text = self.extract_text_from_file(resume_file)
            
            if not text:
                text = self.parser.parse(resume_file)
            
            return text
        except Exception as e:
            print(f"Error parsing resume: {e}")
            return ""

    def parse_job_description(self, jd_file):
        try:
            
            text = self.extract_text_from_file(jd_file)
            
            if not text:
                text = self.parser.parse(jd_file)
            
            return text
        except Exception as e:
            print(f"Error parsing job description: {e}")
            return ""
    
    def get_embeddings(self, jd_text: str) -> np.ndarray:
        
        try:
            if self.embedding_model is None:
                print("Embedding model not initialized")
                return np.array([])

            embeddings = self.embedding_model.encode(jd_text)
            
            return embeddings
            
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return np.array([])
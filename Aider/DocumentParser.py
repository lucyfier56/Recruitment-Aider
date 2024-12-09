from llama_parse import LlamaParse
import os
from dotenv import load_dotenv
import docx
import PyPDF2

load_dotenv()

class DocumentParser:
    def __init__(self):
        self.parser = LlamaParse(
            api_key=os.getenv('LLAMA_PARSE_API_KEY'),
            result_type="markdown"
        )
    
    def extract_text_from_file(self, file):
        """
        Extract text from different file types
        Supports PDF, DOCX, and TXT files
        """
        file_extension = os.path.splitext(file.name)[1].lower()
        
        try:
            if file_extension == '.pdf':
                pdf_reader = PyPDF2.PdfReader(file)
                text = " ".join([page.extract_text() for page in pdf_reader.pages])
            
            elif file_extension == '.docx':
                doc = docx.Document(file)
                text = " ".join([paragraph.text for paragraph in doc.paragraphs])
            
            elif file_extension == '.txt':
                text = file.getvalue().decode('utf-8')
            
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            return text
        
        except Exception as e:
            print(f"Error parsing document: {e}")
            return ""
    
    def parse_resume(self, resume_file):
        """Parse resume using Llama Parse or fallback to text extraction"""
        try:
            # First try text extraction
            text = self.extract_text_from_file(resume_file)
            
            # If text extraction fails, use Llama Parse
            if not text:
                text = self.parser.parse(resume_file)
            
            return text
        except Exception as e:
            print(f"Error parsing resume: {e}")
            return ""
    
    def parse_job_description(self, jd_file):
        """Parse job description using Llama Parse or text extraction"""
        try:
            # First try text extraction
            text = self.extract_text_from_file(jd_file)
            
            # If text extraction fails, use Llama Parse
            if not text:
                text = self.parser.parse(jd_file)
            
            return text
        except Exception as e:
            print(f"Error parsing job description: {e}")
            return ""
from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv()


class LLMAnalyzer:
    def __init__(self):
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    
    def analyze_resume_and_jd(self, resume_text: str, jd_text: str) -> str:
        """Analyze resume in context of job description"""
        # Resume and JD analysis
        primary_analysis = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a professional HR recruiter analyzing resumes."},
                {"role": "user", "content": f"""
                Analyze the following resume and job description:

                Job Description:
                {jd_text}

                Resume:
                    {resume_text}

                Please provide a detailed analysis with:
                1. General Overview of the candidate profile
                2. Resume Quality Score (1-10)
                3. Resume-JD Relevance Score (1-10)
                4. Key Strengths matching JD
                5. Skill Gaps compared to JD
                6. Recommended Interview Questions
                7. Analyze the Job Description and suggest what other role designation can be used for the same.
                8. Recommended HR Interview Questions aligning to the following values:
                    - Cultivating Happiness
                    - Crafting Excellence
                    - Delighting Customers
                9. Give everything in points and in a structured manner.
                

                Format the response in clear, structured markdown.
                """}
            ],
            model="llama-3.1-70b-versatile"
        ).choices[0].message.content
    
        return primary_analysis
import streamlit as st
import base64
from PIL import Image
import io
import os
import tempfile
from dotenv import load_dotenv

# MongoDB Imports
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Import other project modules
from document_parser import DocumentParser
from llm_analyzer import LLMAnalyzer
from github_link_analyzer import GitHubLinkAnalyzer
from data_storage import RecruitmentDataHandler



# def connect_to_mongodb():
#     """
#     Connect to MongoDB using environment variables
    
#     :return: MongoDB database connection or None
#     """
#     try:
#         db_password = os.getenv('DB_PASSWORD')
#         uri = f"mongodb+srv://rudrapandarp:{db_password}@cluster0.uomwx.mongodb.net/"
        
#         load_dotenv()
        
#         client = MongoClient(uri)
#         db = client['recruitment_database']
        
#         client.admin.command('ping')
#         print("Successfully connected to MongoDB!")
        
#         return db
#     except Exception as e:
#         st.error(f"Error connecting to MongoDB: {e}")
#         return None

def get_base64_of_bin_file(bin_file):
    """Convert image to base64"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(png_file):
    """Set background image for the app"""
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = f'''
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    .stApp::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        z-index: -1;
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)






def main():
    
    load_dotenv()

    
    st.set_page_config(
        page_title="Recruitment Aider", 
        page_icon="💡", 
        layout="wide"
    )
    
    
    st.markdown("""
    <style>
    /* Global Styles */
    body {
        color: #333;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header Styles */
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        color: #ffffff;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Card-like Containers */
    .stCard {
        border-radius: 15px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        padding: 20px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    .stCard:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(0,0,0,0.15);
    }
    </style>
    """, unsafe_allow_html=True)
    
    
    # db = connect_to_mongodb()
    
    
    document_parser = DocumentParser()
    
    llm_analyzer = LLMAnalyzer()
    
    db_password = os.getenv('DB_PASSWORD')
    connection_string = f"mongodb+srv://rudrapandarp:{db_password}@cluster0.uomwx.mongodb.net/"
    data_storage = RecruitmentDataHandler(connection_string)

    
    st.markdown('<h1 class="main-title">Recruitment Aider 💼</h1>', unsafe_allow_html=True)
    
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🎯 Intelligent Skill Mapping
        AI-powered precise alignment of candidate capabilities 
        with job requirements.
        """)
    
    with col2:
        st.markdown("""
        ### ⚡ Rapid Screening
        Instantly analyze multiple resumes, 
        saving hours of manual review.
        """)
    
    with col3:
        st.markdown("""
        ### 🔍 Deep Insights
        Comprehensive analysis highlighting 
        candidate strengths and potential gaps.
        """)
    
    
    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    
    
    col_jd, col_resumes = st.columns(2)
    
    with col_jd:
        st.markdown("#### 📄 Job Description")
        jd_file = st.file_uploader(
            "Upload Job Description", 
            type=['pdf', 'docx', 'txt'], 
            key="jd_uploader",
            help="Upload the job description document"
        )
    
    with col_resumes:
        st.markdown("#### 📋 Candidate Resumes")
        resume_files = st.file_uploader(
            "Upload Resumes", 
            accept_multiple_files=True, 
            type=['pdf', 'docx', 'txt'], 
            key="resume_uploader",
            help="Upload multiple candidate resumes"
        )
    
    
    process_button = st.button(
        "🚀 Analyze Resume & Job Match", 
        use_container_width=True,
        type="primary"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    
    # if not db:
    #     st.error("Failed to connect to MongoDB. Please check your connection settings.")
    #     return
    
    
    if process_button and jd_file and resume_files:
        
        with st.spinner('Processing documents...'):
            try:
               
                jd_text = document_parser.parse_job_description(jd_file)
                
                
               
                
                # Results Container
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.markdown("## 📊 Analysis Results")
                
                # Create a tabbed interface for results
                analysis_tabs = st.tabs([f"Resume {i+1}" for i in range(len(resume_files))])
                
                for tab, resume_file in zip(analysis_tabs, resume_files):
                    with tab:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(resume_file.name)[1]) as tmp_file:
                            tmp_file.write(resume_file.getvalue())
                            tmp_file_path = tmp_file.name
                        
                        try:
                            
                            resume_text = document_parser.parse_resume(resume_file)

                            analysis = llm_analyzer.analyze_resume_and_jd(resume_text, jd_text, resume_pdf=tmp_file_path)
                            
                            analysis_result = analysis[0]
                            
                            job_data =  llm_analyzer.analyze_resume_and_jd(resume_text, jd_text, resume_pdf=tmp_file_path)[1]

                            embeddings = llm_analyzer.analyze_resume_and_jd(resume_text, jd_text, resume_pdf=tmp_file_path)[3]
                            print(embeddings)
                            
                            results = data_storage.process_job_data(job_data)
                            print(results)
                            
                            st.markdown(f"### Analysis for {resume_file.name}")
                            st.markdown(analysis_result)
                            
                            st.markdown("### 🔗 GitHub Project Analysis")
                            
                            github_results = llm_analyzer.analyze_resume_and_jd(resume_text, jd_text, resume_pdf=tmp_file_path)[2]
                           
                            if github_results:
                                for repo, result in github_results.items():
                                    st.markdown(f"#### 🌐 Repository: {repo}")
                                    st.markdown(result['analysis'])
                            else:
                                st.info("No GitHub repositories found in the resume.")
                        
                        finally:
                            os.unlink(tmp_file_path)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.success('Analysis completed successfully!')
            
            except Exception as e:
                st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
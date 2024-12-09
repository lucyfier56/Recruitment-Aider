import streamlit as st
import base64
from PIL import Image
import io
import os
from DocumentParser import DocumentParser
from VecotoreStoreManager import VectorStoreManager
from LLMAnalyzer import LLMAnalyzer
from GitHubLinkAnalyzer import GitHubLinkAnalyzer
import tempfile
from dotenv import load_dotenv
import time

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
    # Load environment variables
    load_dotenv()

    # Page Configuration
    st.set_page_config(
        page_title="Recruitment Aider", 
        page_icon="💡", 
        layout="wide"
    )
    
    # Custom CSS for enhanced styling
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
    
    # Create a dedicated directory for document storage
    document_storage_dir = os.path.join(os.getcwd(), 'recruitment_documents')
    os.makedirs(document_storage_dir, exist_ok=True)
    
    # Initialize services
    document_parser = DocumentParser()
    vector_store = VectorStoreManager(storage_dir=document_storage_dir)
    llm_analyzer = LLMAnalyzer()
    github_analyzer = GitHubLinkAnalyzer()

    # Main Title and Subheader
    st.markdown('<h1 class="main-title">Recruitment Aider 💼</h1>', unsafe_allow_html=True)
    
    # Features Overview
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
    
    # Main Content Area
    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    
    # File Upload Columns
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
    
    # Process Button
    process_button = st.button(
        "🚀 Analyze Resume & Job Match", 
        use_container_width=True,
        type="primary"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Analysis Section
    if process_button and jd_file and resume_files:
        # Progress Indicators
        with st.spinner('Processing documents...'):
            try:
                # Parse Job Description
                jd_text = document_parser.parse_job_description(jd_file)
                
                # Add Job Description to Vector Store with more robust ID
                jd_doc_id = f"jd_{int(time.time())}_{jd_file.name}"
                vector_store.add_document(jd_doc_id, jd_text, 
                                          {'type': 'job_description', 'filename': jd_file.name})
                
                # Results Container
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.markdown("## 📊 Analysis Results")
                
                # Create a tabbed interface for results
                analysis_tabs = st.tabs([f"Resume {i+1}" for i in range(len(resume_files))])
                
                for tab, resume_file in zip(analysis_tabs, resume_files):
                    with tab:
                        # Create a temporary file to pass to GitHub link analyzer
                        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(resume_file.name)[1]) as tmp_file:
                            tmp_file.write(resume_file.getvalue())
                            tmp_file_path = tmp_file.name
                        
                        try:
                            # Parse Resume
                            resume_text = document_parser.parse_resume(resume_file)
                            
                            # Add Resume to Vector Store with more robust ID
                            resume_doc_id = f"resume_{int(time.time())}_{resume_file.name}"
                            vector_store.add_document(resume_doc_id, resume_text, 
                                                      {'type': 'resume', 'filename': resume_file.name})
                            
                            # Analyze Resume against Job Description
                            analysis_result = llm_analyzer.analyze_resume_and_jd(resume_text, jd_text)
                            
                            # Display Resume Analysis
                            st.markdown(f"### Analysis for {resume_file.name}")
                            st.markdown(analysis_result)
                            
                            # GitHub Project Analysis
                            st.markdown("### 🔗 GitHub Project Analysis")
                            
                            # Analyze GitHub projects
                            github_results = github_analyzer.process_github_projects(
                                resume_pdf=tmp_file_path, 
                                jd_text=jd_text
                            )
                            
                            # Display GitHub Project Analyses
                            if github_results:
                                for repo, result in github_results.items():
                                    st.markdown(f"#### 🌐 Repository: {repo}")
                                    st.markdown(result['analysis'])
                            else:
                                st.info("No GitHub repositories found in the resume.")
                        
                        finally:
                            # Clean up temporary file
                            os.unlink(tmp_file_path)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Optional: Display saved document locations
                st.info(f"Documents saved in: {document_storage_dir}")
                st.success('Analysis completed successfully!')
            
            except Exception as e:
                st.error(f"An error occurred: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    main()
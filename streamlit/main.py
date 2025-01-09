from fastapi import logger
import streamlit as st
import os
from llm_analyzer import LLMAnalyzer
from github_link_analyzer import GitHubLinkAnalyzer
from document_parser import DocumentParser
from dotenv import load_dotenv
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Resume & JD Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern Dark Theme CSS
st.markdown("""
    <style>
    /* Global styles and dark theme */
    [data-testid="stAppViewContainer"] {
        background-color: #1a1a1a;
        color: #e0e0e0;
    }
    
    .stApp {
        background-color: #1a1a1a;
    }
    
    /* Main container styling */
    .main {
        background-color: #1a1a1a;
        padding: 2rem;
    }
    
    /* Header/Title container */
    .title-container {
        background: linear-gradient(135deg, #2d2d2d, #1a1a1a);
        padding: 2.5rem;
        border-radius: 20px;
        border: 1px solid #333;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    /* Upload containers */
    .upload-container {
        background: #2d2d2d;
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #333;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .upload-container:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        border-color: #4a4a4a;
    }
    
    /* Analysis section */
    .analysis-container {
        background: #2d2d2d;
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #333;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    /* Custom button styling */
    .stButton > button {
        background: linear-gradient(135deg, #7b2ff7, #5b0eeb) !important;
        color: white !important;
        padding: 0.8rem 2rem !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(123,47,247,0.3) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        max-width: 300px !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #8f4ff8, #6b2eeb) !important;
        box-shadow: 0 6px 20px rgba(123,47,247,0.4) !important;
        transform: translateY(-2px) !important;
    }
    
    /* File uploader modifications */
    [data-testid="stFileUploader"] {
        border: 2px dashed #4a4a4a;
        border-radius: 10px;
        padding: 1rem;
        background: #252525;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #7b2ff7;
    }
    
    /* Success/Info/Warning message styling */
    .success-msg {
        background: #1e3b2f;
        color: #4caf50;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #4caf50;
    }
    
    .info-msg {
        background: #1e2b3b;
        color: #64b5f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #64b5f6;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #2d2d2d;
        border-radius: 10px;
        border: 1px solid #333;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background-color: #7b2ff7;
    }
    
    /* Typography */
    h1, h2, h3 {
        color: #e0e0e0;
        font-weight: 600;
    }
    
    p {
        color: #b0b0b0;
    }
    
    /* Code blocks */
    code {
        background-color: #252525;
        padding: 0.2em 0.4em;
        border-radius: 5px;
        font-size: 85%;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    # Modern Header
    st.markdown("""
        <div class='title-container'>
            <h1 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>🎯 Resume Matcher AI</h1>
            <p style='color: #b0b0b0; font-size: 1.2rem;'>Analyze your resume against job descriptions with AI precision</p>
        </div>
    """, unsafe_allow_html=True)

    # Initialize analyzers
    llm_analyzer = LLMAnalyzer()
    document_parser = DocumentParser()

    # File upload section with modern UI
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class='upload-container'>
                <h3 style='margin-bottom: 1rem;'>📄 Upload Resume</h3>
            </div>
        """, unsafe_allow_html=True)
        resume_file = st.file_uploader(
            "Upload your resume",
            type=['pdf', 'docx', 'txt'],
            key="resume_uploader",
            label_visibility="collapsed"
        )
        if resume_file:
            st.markdown(f"""
                <div class='success-msg'>
                    ✅ Resume uploaded: {resume_file.name}
                </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class='upload-container'>
                <h3 style='margin-bottom: 1rem;'>💼 Upload Job Description</h3>
            </div>
        """, unsafe_allow_html=True)
        jd_file = st.file_uploader(
            "Upload job description",
            type=['pdf', 'docx', 'txt'],
            key="jd_uploader",
            label_visibility="collapsed"
        )
        if jd_file:
            st.markdown(f"""
                <div class='success-msg'>
                    ✅ Job Description uploaded: {jd_file.name}
                </div>
            """, unsafe_allow_html=True)

    # Centered analyze button
    if resume_file and jd_file:
        # Add spacing before the button
        st.markdown("<div style='margin-top: 3rem;'></div>", unsafe_allow_html=True)
        
        # Create three columns with the middle one being smaller
        left_spacer, center_col, right_spacer = st.columns([1.5, 1, 1.5])
        with center_col:
            analyze_clicked = st.button("🚀 Analyze Match", key="analyze_button")
            
        # Add spacing after the button
        st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
            
        if analyze_clicked:
            with st.spinner("🔄 Processing documents..."):
                try:
                    # Parse documents
                    resume_text = document_parser.parse_resume(resume_file, resume_file.name)
                    jd_text = document_parser.parse_job_description(jd_file, jd_file.name)

                    # LLM Analysis
                    analysis_results = llm_analyzer.analyze_resume_and_jd(resume_text, jd_text)
                    
                    # Display Analysis Results
                    st.markdown("""
                        <div class='analysis-container'>
                            <h2>🎯 Match Analysis</h2>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                        <div style='background-color: #252525; padding: 1.5rem; border-radius: 10px; border: 1px solid #333;'>
                            {analysis_results["analysis_text"]}
                        </div>
                    """, unsafe_allow_html=True)

                    # GitHub Analysis
                    github_analyzer = GitHubLinkAnalyzer()
                    resume_file.seek(0)
                    
                    try:
                        github_results = github_analyzer.process_github_projects(resume_file, jd_text)
                        
                        if github_results:
                            st.markdown("""
                                <div class='analysis-container'>
                                    <h2>⚡ GitHub Projects Analysis</h2>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            for repo_link, analysis in github_results.items():
                                with st.expander(f"📂 {repo_link}"):
                                    if 'analysis' in analysis and analysis['analysis']:
                                        st.markdown(analysis['analysis'])
                                    else:
                                        st.warning("No analysis available for this repository")
                        else:
                            st.markdown("""
                                <div class='info-msg'>
                                    ℹ️ No GitHub projects found in the resume
                                </div>
                            """, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error analyzing GitHub projects: {str(e)}")
                        logger.error(f"GitHub analysis error: {str(e)}")

                except Exception as e:
                    st.error(f"An error occurred during analysis: {str(e)}")
                    logger.error(f"General analysis error: {str(e)}")

    else:
        st.markdown("""
            <div class='info-msg' style='text-align: center;'>
                👆 Upload both your resume and a job description to begin the analysis
            </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
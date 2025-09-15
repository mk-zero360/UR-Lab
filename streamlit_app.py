import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import json
import re
import random
from typing import Dict, List, Optional
import io
import base64
from streamlit_chat import message
import hashlib

# Advanced NLP libraries for text analysis
try:
    from textblob import TextBlob
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    
    # Initialize VADER sentiment analyzer
    @st.cache_resource
    def get_sentiment_analyzer():
        """Initialize and cache VADER sentiment analyzer"""
        return SentimentIntensityAnalyzer()
    
    NLP_AVAILABLE = True
    
except ImportError as e:
    NLP_AVAILABLE = False
    st.info("💡 Using basic text analysis. Install textblob and vaderSentiment for enhanced analysis.")

# Audio components
try:
    from audio_recorder_streamlit import audio_recorder
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# Import OpenAI and load environment variables
import openai
from dotenv import load_dotenv
load_dotenv()

# Predefined Segments Management
def load_predefined_segments_from_file(uploaded_file) -> Dict[str, Dict]:
    """
    Load predefined segments from uploaded Excel or CSV file
    
    Expected columns:
    - segment_name: Name of the segment
    - segment_description: Description of the segment
    - age_range: Age range (e.g., "25-35")
    - income_level: Income level (e.g., "Middle class")
    - location: Location (e.g., "Urban Germany")
    - tech_comfort: Tech comfort level (e.g., "High")
    - lifestyle: Lifestyle description
    - key_motivations: Comma-separated motivations
    - persona_count: Number of personas to generate (optional, defaults to 5)
    """
    try:
        # Determine file type and read accordingly
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            raise ValueError("Unsupported file format. Please use CSV or Excel files.")
        
        # Validate required columns
        required_columns = ['segment_name', 'segment_description', 'age_range']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        segments = {}
        for _, row in df.iterrows():
            segment_name = str(row['segment_name']).strip()
            if not segment_name or segment_name == 'nan':
                continue
                
            # Parse key_motivations if it exists
            key_motivations = []
            if 'key_motivations' in df.columns and pd.notna(row['key_motivations']):
                key_motivations = [m.strip() for m in str(row['key_motivations']).split(',') if m.strip()]
            
            segments[segment_name] = {
                'segment_name': segment_name,
                'segment_description': str(row['segment_description']) if pd.notna(row['segment_description']) else '',
                'age_range': str(row['age_range']) if pd.notna(row['age_range']) else '',
                'income_level': str(row['income_level']) if 'income_level' in df.columns and pd.notna(row['income_level']) else 'Not specified',
                'location': str(row['location']) if 'location' in df.columns and pd.notna(row['location']) else 'Not specified',
                'tech_comfort': str(row['tech_comfort']) if 'tech_comfort' in df.columns and pd.notna(row['tech_comfort']) else 'Not specified',
                'lifestyle': str(row['lifestyle']) if 'lifestyle' in df.columns and pd.notna(row['lifestyle']) else 'Not specified',
                'key_motivations': key_motivations,
                'persona_count': int(row['persona_count']) if 'persona_count' in df.columns and pd.notna(row['persona_count']) else 5
            }
        
        return segments
        
    except Exception as e:
        st.error(f"Error loading predefined segments: {str(e)}")
        return {}

def create_segment_template_download():
    """Create a downloadable template for predefined segments"""
    template_data = {
        'segment_name': [
            'Tech-Savvy Millennials',
            'Budget-Conscious Families',
            'Premium Service Seekers'
        ],
        'segment_description': [
            'Young professionals aged 25-35 who are early adopters of technology and value efficiency and innovation.',
            'Families with children who prioritize value for money and practical solutions for everyday challenges.',
            'Affluent customers who are willing to pay premium prices for high-quality products and exceptional service.'
        ],
        'age_range': ['25-35', '30-45', '40-60'],
        'income_level': ['Upper middle class', 'Middle class', 'High income'],
        'location': ['Urban Germany', 'Suburban Germany', 'Major German cities'],
        'tech_comfort': ['High', 'Medium', 'Medium'],
        'lifestyle': [
            'Fast-paced, career-focused, values convenience and innovation',
            'Family-oriented, practical, budget-conscious, values reliability',
            'Luxury-oriented, quality-focused, values exclusivity and personal service'
        ],
        'key_motivations': [
            'Efficiency, Innovation, Career advancement',
            'Family wellbeing, Value for money, Practicality',
            'Quality, Status, Exclusivity'
        ],
        'persona_count': [5, 5, 3]
    }
    
    df = pd.DataFrame(template_data)
    return df

# Avatar generation for personas
def get_persona_avatar_url(persona_name: str, persona_data: dict = None) -> str:
    """Generate a realistic human avatar URL for a persona using DiceBear API"""
    # Create a consistent seed based on persona name for consistent avatars
    seed = hashlib.md5(persona_name.encode()).hexdigest()[:10]
    
    # Determine gender and style based on persona data or name
    gender_styles = {
        'male': ['adventurer', 'big-smile', 'fun-emoji'],
        'female': ['adventurer', 'big-smile', 'fun-emoji'],
        'neutral': ['adventurer', 'big-smile', 'personas']
    }
    
    # Try to determine gender from persona data or name
    gender = 'neutral'
    if persona_data:
        # Look for gender indicators in persona background or description
        background = persona_data.get('background', '').lower()
        if any(word in background for word in ['herr', 'mann', 'er ', 'sein', 'ihm']):
            gender = 'male'
        elif any(word in background for word in ['frau', 'sie ', 'ihr', 'ihre']):
            gender = 'female'
    
    # Use name patterns as fallback
    if gender == 'neutral':
        male_names = ['thomas', 'michael', 'andreas', 'christian', 'stefan', 'markus', 'alexander']
        female_names = ['julia', 'anna', 'sarah', 'maria', 'lisa', 'petra', 'claudia']
        
        name_lower = persona_name.lower()
        if any(name in name_lower for name in male_names):
            gender = 'male'
        elif any(name in name_lower for name in female_names):
            gender = 'female'
    
    # Generate realistic human avatar
    style = random.choice(gender_styles[gender])
    
    # Use DiceBear's avataaars style for realistic human faces
    avatar_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={seed}&backgroundColor=b6e3f4,c0aede,d1d4f9&radius=50"
    
    # Add some variety based on persona characteristics
    if persona_data:
        age = persona_data.get('age', 35)
        # Convert age to int if it's a string or handle any other type
        try:
            if isinstance(age, str):
                age = int(age)
            elif not isinstance(age, (int, float)):
                age = 35
            age = int(age)  # Ensure it's an integer
        except (ValueError, TypeError):
            age = 35
        
        if age > 50:
            avatar_url += "&hair=shortHair01,shortHair02,shortHair03"
        elif age < 30:
            avatar_url += "&hair=longHair01,longHair02,curlyHair"
        
        # Add accessories for professional personas
        job = persona_data.get('job', '').lower()
        if any(word in job for word in ['manager', 'director', 'consultant', 'architect']):
            avatar_url += "&accessories=prescription02,sunglasses"
    
    return avatar_url

# Set up OpenAI - Compatible with both local .env and Streamlit Cloud secrets
try:
    # Try Streamlit secrets first (for cloud deployment)
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
except (AttributeError, FileNotFoundError, KeyError):
    # Fallback to environment variable (for local development)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

OPENAI_AVAILABLE = bool(OPENAI_API_KEY)

# Page config
st.set_page_config(
    page_title="zero360 Autonomous Research Lab",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for 3-column layout with left navigation
st.markdown("""
<style>
    /* zero360 Brand Colors - Official Palette */
    :root {
        /* zeroBlau Colors - Official Brand Blues */
        --zero360-blau-1: #02063f;  /* zeroBlau 1 - Dark Navy */
        --zero360-blau-2: #576fb4;  /* zeroBlau 2 - Medium Blue */
        --zero360-blau-3: #84a5ff;  /* zeroBlau 3 - Light Blue */
        --zero360-gelb: #fff700;    /* zeroGelb - Bright Yellow */
        
        /* Stripe-inspired color system */
        --primary: var(--zero360-blau-1);
        --primary-light: var(--zero360-blau-2);
        --primary-lighter: var(--zero360-blau-3);
        --accent: var(--zero360-gelb);
        
        /* Neutral grays - Stripe style */
        --gray-50: #fafafa;
        --gray-100: #f5f5f5;
        --gray-200: #e5e5e5;
        --gray-300: #d4d4d4;
        --gray-400: #a3a3a3;
        --gray-500: #737373;
        --gray-600: #525252;
        --gray-700: #404040;
        --gray-800: #262626;
        --gray-900: #171717;
        
        /* Semantic colors */
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
        --info: var(--primary-lighter);
        
        /* Spacing system */
        --space-1: 0.25rem;
        --space-2: 0.5rem;
        --space-3: 0.75rem;
        --space-4: 1rem;
        --space-6: 1.5rem;
        --space-8: 2rem;
        --space-12: 3rem;
        --space-16: 4rem;
        
        /* Border radius */
        --radius-sm: 0.375rem;
        --radius: 0.5rem;
        --radius-md: 0.75rem;
        --radius-lg: 1rem;
        --radius-xl: 1.5rem;
        
        /* Shadows */
        --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
        --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
        --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
        
        /* Typography */
        --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        --font-mono: ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace;
    }
    
    /* Remove default Streamlit padding and margins */
    .main .block-container {
        padding-top: 0.5rem;
        padding-bottom: 1rem;
        max-width: none;
    }
    
    /* Hide the main header/hero banner */
    .main-header {
        display: none;
    }
    
    /* Modern Card-style Navigation Bar */
    .nav-bar {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border: 1px solid var(--gray-200);
        color: var(--gray-900);
        padding: var(--space-4) var(--space-6);
        margin: calc(-1 * var(--space-4)) calc(-1 * var(--space-4)) var(--space-4) calc(-1 * var(--space-4));
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-sm);
        position: relative;
        top: -15px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        min-height: 70px;
        transition: all 0.2s ease;
    }
    
    .nav-bar:hover {
        box-shadow: var(--shadow-md);
    }
    
    /* Navigation buttons styling */
    .nav-buttons {
        display: flex;
        gap: var(--space-2);
        align-items: center;
    }
    
    /* Enhanced button styling for navigation - more subtle */
    .stButton > button[data-testid="baseButton-primary"] {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        font-weight: 500 !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button[data-testid="baseButton-primary"]:hover {
        background: rgba(255, 255, 255, 0.2) !important;
        border-color: rgba(255, 255, 255, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    
    .stButton > button[data-testid="baseButton-secondary"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: rgba(255, 255, 255, 0.8) !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button[data-testid="baseButton-secondary"]:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
    }
    
    .nav-bar h1 {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.025em;
        color: var(--gray-900);
    }
    
    .nav-bar .status-indicator {
        display: flex;
        gap: var(--space-3);
        align-items: center;
        font-size: 0.875rem;
    }
    
    .status-badge {
        background: var(--gray-100);
        color: var(--gray-700);
        padding: var(--space-1) var(--space-3);
        border-radius: var(--radius);
        border: 1px solid var(--gray-200);
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .status-badge:hover {
        background: var(--gray-50);
        transform: translateY(-1px);
        box-shadow: var(--shadow-sm);
    }
    
    .status-badge.success {
        background: rgba(16, 185, 129, 0.1);
        color: var(--success);
        border-color: rgba(16, 185, 129, 0.2);
    }
    
    .status-badge.error {
        background: rgba(239, 68, 68, 0.1);
        color: var(--error);
        border-color: rgba(239, 68, 68, 0.2);
    }
    
    /* Sidebar Styling - Always Visible */
    .css-1d391kg {
        background: linear-gradient(180deg, var(--gray-50) 0%, var(--gray-100) 100%);
        border-right: 1px solid var(--gray-200);
    }
    
    /* Force sidebar to always be visible */
    section[data-testid="stSidebar"] {
        width: 300px !important;
        min-width: 300px !important;
        max-width: 300px !important;
        transform: translateX(0px) !important;
        visibility: visible !important;
        display: block !important;
    }
    
    /* Hide sidebar collapse button */
    button[kind="header"] {
        display: none !important;
    }
    
    /* Ensure main content adjusts for always-visible sidebar */
    .main .block-container {
        padding-left: 1rem !important;
        max-width: calc(100vw - 320px) !important;
    }
    
    /* Alternative sidebar selectors for different Streamlit versions */
    .css-1d391kg,
    .css-1y4p8pa,
    .css-6qob1r,
    section[data-testid="stSidebar"] > div {
        transform: translateX(0px) !important;
        visibility: visible !important;
    }
    
    /* Hide the sidebar toggle chevron */
    .css-1rs6os .css-17ziqus,
    .css-1rs6os .css-1vbd788 {
        display: none !important;
    }
    
    /* 3-Column Layout */
    .three-column-container {
        display: grid;
        grid-template-columns: 1fr 2fr 1fr;
        gap: var(--space-6);
        min-height: calc(100vh - 120px);
    }
    
    .column {
        background: white;
        border-radius: var(--radius-lg);
        padding: var(--space-6);
        box-shadow: var(--shadow);
        border: 1px solid var(--gray-200);
        overflow-y: auto;
        max-height: calc(100vh - 140px);
    }
    
    .column h3 {
        color: var(--primary);
        margin-top: 0;
        margin-bottom: var(--space-4);
        font-size: 1.25rem;
        font-weight: 600;
        border-bottom: 2px solid var(--gray-100);
        padding-bottom: var(--space-2);
    }
    
    /* Left Column - Configuration */
    .left-column {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    /* Center Column - Main Content */
    .center-column {
        background: white;
    }
    
    /* Right Column - Analytics */
    .right-column {
        background: linear-gradient(135deg, #fefefe 0%, #f9fafb 100%);
    }
    
    /* Modern Card Components */
    .persona-preview {
        background: white;
        padding: var(--space-6);
        border-radius: var(--radius-lg);
        border: 1px solid var(--gray-200);
        margin: var(--space-4) 0;
        box-shadow: var(--shadow-sm);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .persona-preview:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
        border-color: var(--gray-300);
    }
    
    .persona-preview::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .persona-preview:hover::before {
        opacity: 1;
    }
    
    .example-persona {
        background: white;
        padding: var(--space-5);
        border-radius: var(--radius-lg);
        border: 1px solid var(--gray-200);
        margin: var(--space-3) 0;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: var(--shadow-sm);
        font-size: 0.875rem;
        position: relative;
        overflow: hidden;
    }
    
    .example-persona::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        background: linear-gradient(180deg, var(--primary) 0%, var(--primary-light) 100%);
        transition: all 0.3s ease;
    }
    
    .example-persona:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
        border-color: var(--gray-300);
    }
    
    .example-persona:hover::before {
        width: 6px;
        background: linear-gradient(180deg, var(--primary-light) 0%, var(--primary-lighter) 100%);
    }
    
    /* Enhanced Chat styling for streamlit-chat */
    .stChatMessage {
        margin: 8px 0 !important;
    }
    
    .stChatMessage > div {
        border-radius: 12px !important;
        padding: 12px 16px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* User messages */
    .stChatMessage[data-testid="chat-message-user"] > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        margin-left: 20% !important;
    }
    
    /* Assistant messages */
    .stChatMessage[data-testid="chat-message-assistant"] > div {
        background: #f8f9fa !important;
        color: #333 !important;
        margin-right: 20% !important;
        border: 1px solid #e9ecef !important;
    }
    
    /* Chat input styling */
    .stChatInput > div > div > input {
        border-radius: 20px !important;
        border: 2px solid #e9ecef !important;
        padding: 12px 16px !important;
    }
    
    .stChatInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1) !important;
    }
    
    .chat-container {
        background: var(--gray-50);
        border-radius: var(--radius);
        padding: var(--space-4);
        margin: var(--space-4) 0;
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid var(--gray-200);
    }
    
    .ai-message {
        background: var(--primary);
        color: white;
        margin-right: var(--space-6);
    }
    
    /* Modern Metric Cards */
    .metric-card {
        background: white;
        padding: var(--space-6);
        border-radius: var(--radius-lg);
        border: 1px solid var(--gray-200);
        margin: var(--space-3) 0;
        box-shadow: var(--shadow-sm);
        color: var(--gray-900);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
        border-color: var(--gray-300);
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .metric-card:hover::before {
        opacity: 1;
    }
    
    .metric-card h4 {
        margin: 0 0 var(--space-3) 0;
        font-size: 0.875rem;
        color: var(--gray-600);
        font-weight: 500;
        letter-spacing: 0.025em;
    }
    
    .metric-card h2 {
        margin: 0;
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--primary);
        letter-spacing: -0.025em;
    }
    
    .metric-card p {
        margin: var(--space-2) 0 0 0;
        font-size: 0.75rem;
        color: var(--gray-500);
        line-height: 1.4;
    }
    
    .sentiment-positive {
        border-left: 4px solid var(--success);
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
    }
    
    .sentiment-neutral {
        border-left: 4px solid var(--info);
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    }
    
    .sentiment-negative {
        border-left: 4px solid var(--error);
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
    }
    
    /* Modern Subtle Buttons */
    .stButton > button {
        background: white;
        color: var(--gray-700);
        border: 1px solid var(--gray-300);
        border-radius: var(--radius-md);
        padding: var(--space-3) var(--space-6);
        font-weight: 500;
        font-size: 0.875rem;
        transition: all 0.2s ease;
        box-shadow: var(--shadow-sm);
        width: 100%;
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button:hover {
        background: var(--gray-50);
        border-color: var(--gray-400);
        color: var(--gray-900);
        transform: translateY(-1px);
        box-shadow: var(--shadow);
    }
    
    /* Primary button variant */
    .stButton > button[type="primary"],
    .stButton > button[data-testid="baseButton-primary"]:not([class*="nav-bar"]) {
        background: var(--primary) !important;
        color: white !important;
        border: 1px solid var(--primary) !important;
        font-weight: 600 !important;
    }
    
    .stButton > button[type="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:not([class*="nav-bar"]):hover {
        background: var(--primary-light) !important;
        border-color: var(--primary-light) !important;
        transform: translateY(-1px);
        box-shadow: var(--shadow-md) !important;
    }
    
    /* Secondary/outline button variant */
    .stButton > button[data-testid="baseButton-secondary"]:not([class*="nav-bar"]) {
        background: transparent !important;
        color: var(--primary) !important;
        border: 1px solid var(--primary) !important;
    }
    
    .stButton > button[data-testid="baseButton-secondary"]:not([class*="nav-bar"]):hover {
        background: var(--primary) !important;
        color: white !important;
    }
    
    /* Modern Form Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        font-size: 0.875rem;
        border: 1px solid var(--gray-300) !important;
        border-radius: var(--radius-md) !important;
        box-shadow: var(--shadow-sm) !important;
        transition: all 0.2s ease !important;
        background: white !important;
        padding: var(--space-3) !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div:focus-within {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(2, 6, 63, 0.1) !important;
        outline: none !important;
    }
    
    .stTextInput > div > div > input:hover,
    .stTextArea > div > div > textarea:hover,
    .stSelectbox > div > div:hover {
        border-color: var(--gray-400) !important;
    }
    
    /* Enhanced form labels */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label {
        font-weight: 500 !important;
        color: var(--gray-700) !important;
        font-size: 0.875rem !important;
        margin-bottom: var(--space-2) !important;
    }
    
    /* Scrollbars */
    ::-webkit-scrollbar {
        width: 4px;
        height: 4px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--gray-100);
        border-radius: var(--radius);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--gray-300);
        border-radius: var(--radius);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--gray-400);
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Make content fit without scrolling */
    .main {
        overflow: hidden;
    }
    
    /* Modern Card Container Classes */
    .card {
        background: white;
        border: 1px solid var(--gray-200);
        border-radius: var(--radius-lg);
        padding: var(--space-6);
        box-shadow: var(--shadow-sm);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
        border-color: var(--gray-300);
    }
    
    .card-header {
        margin-bottom: var(--space-4);
        padding-bottom: var(--space-3);
        border-bottom: 1px solid var(--gray-100);
    }
    
    .card-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--gray-900);
        margin: 0;
        letter-spacing: -0.025em;
    }
    
    .card-description {
        font-size: 0.875rem;
        color: var(--gray-600);
        margin: var(--space-1) 0 0 0;
        line-height: 1.5;
    }
    
    /* Subtle accent borders */
    .card-accent-top::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%);
        opacity: 0.8;
    }
    
    .card-accent-left::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        background: linear-gradient(180deg, var(--primary) 0%, var(--primary-light) 100%);
        opacity: 0.8;
    }
    
    /* Grid layouts */
    .grid-2 {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: var(--space-4);
    }
    
    .grid-3 {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: var(--space-4);
    }
    
    .grid-4 {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: var(--space-4);
    }
    
    @media (max-width: 768px) {
        .grid-2, .grid-3, .grid-4 {
            grid-template-columns: 1fr;
        }
        
        /* On mobile, allow sidebar to be smaller but still visible */
        section[data-testid="stSidebar"] {
            width: 250px !important;
            min-width: 250px !important;
            max-width: 250px !important;
        }
        
        .main .block-container {
            max-width: calc(100vw - 270px) !important;
        }
    }
</style>

<script>
// Force sidebar to stay open
document.addEventListener('DOMContentLoaded', function() {
    // Hide sidebar toggle button if it exists
    const toggleButton = document.querySelector('button[kind="header"]');
    if (toggleButton) {
        toggleButton.style.display = 'none';
    }
    
    // Ensure sidebar is always expanded
    const sidebar = document.querySelector('section[data-testid="stSidebar"]');
    if (sidebar) {
        sidebar.style.transform = 'translateX(0px)';
        sidebar.style.visibility = 'visible';
        sidebar.style.display = 'block';
    }
});

// Monitor for dynamic changes and maintain sidebar visibility
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        const toggleButton = document.querySelector('button[kind="header"]');
        if (toggleButton) {
            toggleButton.style.display = 'none';
        }
        
        const sidebar = document.querySelector('section[data-testid="stSidebar"]');
        if (sidebar) {
            sidebar.style.transform = 'translateX(0px)';
            sidebar.style.visibility = 'visible';
            sidebar.style.display = 'block';
        }
    });
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});
</script>
""", unsafe_allow_html=True)

# Placeholder for future predefined personas (to be added later)
EXAMPLE_PERSONAS = {}

# Built-in Segmentation Frameworks
BUILT_IN_SEGMENTS = {
    "GfK Roper Consumer Styles": {
        "description": "Global segmentation model with 8 segments based on fundamental values, attitudes, and technological affinity.",
        "segments": {
            "Alphas": {
                "segment_name": "Alphas",
                "segment_description": "Traditional and ambitious consumers who value hard work, achievement, and conventional success. They are confident leaders who believe in traditional values and social hierarchies.",
                "age_range": "35-65",
                "income_level": "Upper middle to high income",
                "location": "Urban and suburban areas",
                "tech_comfort": "Medium",
                "lifestyle": "Traditional, achievement-oriented, status-conscious, values hierarchy and conventional success",
                "key_motivations": ["Achievement", "Status", "Leadership", "Traditional values", "Recognition"],
                "persona_count": 4
            },
            "Rooted": {
                "segment_name": "Rooted",
                "segment_description": "Thrifty and practical consumers who spend significant time with media and value stability. They are cautious with money and prefer familiar, reliable solutions.",
                "age_range": "45-75",
                "income_level": "Lower middle to middle income",
                "location": "Rural and suburban areas",
                "tech_comfort": "Low to Medium",
                "lifestyle": "Frugal, media-heavy consumption, values stability and familiarity, risk-averse",
                "key_motivations": ["Security", "Value for money", "Familiarity", "Stability", "Practicality"],
                "persona_count": 5
            },
            "Trend Surfers": {
                "segment_name": "Trend Surfers",
                "segment_description": "Health and fitness-conscious consumers who value social recognition and staying current with trends. They are active, social, and image-conscious.",
                "age_range": "25-45",
                "income_level": "Middle to upper middle income",
                "location": "Urban areas",
                "tech_comfort": "High",
                "lifestyle": "Active, health-conscious, trend-aware, socially engaged, image-focused",
                "key_motivations": ["Social recognition", "Health and fitness", "Trends", "Social status", "Appearance"],
                "persona_count": 4
            },
            "Easy Going": {
                "segment_name": "Easy Going",
                "segment_description": "Consumers primarily concerned about financial security and maintaining a comfortable lifestyle. They prefer simple, straightforward solutions.",
                "age_range": "30-60",
                "income_level": "Middle income",
                "location": "Mixed urban and suburban",
                "tech_comfort": "Medium",
                "lifestyle": "Relaxed, financially cautious, comfort-seeking, avoids complexity",
                "key_motivations": ["Financial security", "Comfort", "Simplicity", "Peace of mind", "Stability"],
                "persona_count": 5
            },
            "Dreamers": {
                "segment_name": "Dreamers",
                "segment_description": "Optimistic consumers motivated by the pursuit of happiness and personal fulfillment. They are idealistic and value emotional satisfaction over material success.",
                "age_range": "20-50",
                "income_level": "Variable income",
                "location": "Mixed locations",
                "tech_comfort": "Medium to High",
                "lifestyle": "Optimistic, idealistic, emotion-driven, values experiences over possessions",
                "key_motivations": ["Happiness", "Personal fulfillment", "Emotional satisfaction", "Dreams and aspirations", "Authenticity"],
                "persona_count": 4
            },
            "Adventurers": {
                "segment_name": "Adventurers",
                "segment_description": "Passionate and experience-driven consumers who seek excitement and new challenges. They are willing to take risks for rewarding experiences.",
                "age_range": "25-55",
                "income_level": "Middle to high income",
                "location": "Urban areas and travel-oriented",
                "tech_comfort": "High",
                "lifestyle": "Adventurous, experience-seeking, risk-taking, passionate about interests",
                "key_motivations": ["Adventure", "Passion", "New experiences", "Excitement", "Personal growth"],
                "persona_count": 3
            },
            "Open-minds": {
                "segment_name": "Open-minds",
                "segment_description": "Balanced consumers seeking harmony between self-actualization, social responsibility, and personal pleasure. They value sustainability and ethical consumption.",
                "age_range": "30-55",
                "income_level": "Upper middle income",
                "location": "Urban and progressive communities",
                "tech_comfort": "High",
                "lifestyle": "Balanced, socially conscious, values sustainability, seeks personal growth",
                "key_motivations": ["Self-actualization", "Social responsibility", "Balance", "Sustainability", "Ethical consumption"],
                "persona_count": 4
            },
            "Homebodies": {
                "segment_name": "Homebodies",
                "segment_description": "Security-oriented consumers who desire material comfort and social status through possessions. They prefer familiar environments and proven solutions.",
                "age_range": "35-70",
                "income_level": "Middle to upper middle income",
                "location": "Suburban and residential areas",
                "tech_comfort": "Low to Medium",
                "lifestyle": "Home-focused, security-oriented, values possessions and comfort, traditional family values",
                "key_motivations": ["Material security", "Status through possessions", "Comfort", "Family", "Tradition"],
                "persona_count": 5
            }
        }
    },
    "Sinus Milieus (Germany)": {
        "description": "German sociological segmentation model with 10 milieus based on social status and value orientation.",
        "segments": {
            "Conservative Establishment": {
                "segment_name": "Conservative Establishment",
                "segment_description": "Upper-class traditional milieu with strong sense of responsibility and conservative values. They maintain established structures and prefer proven solutions.",
                "age_range": "50-80",
                "income_level": "High income",
                "location": "Affluent urban and suburban areas",
                "tech_comfort": "Low to Medium",
                "lifestyle": "Traditional, conservative, responsibility-focused, maintains social structures",
                "key_motivations": ["Tradition", "Responsibility", "Social order", "Quality", "Exclusivity"],
                "persona_count": 3
            },
            "Liberal Intellectual Milieu": {
                "segment_name": "Liberal Intellectual Milieu",
                "segment_description": "Highly educated progressive milieu that values intellectual discourse, cultural engagement, and social justice. They are critical thinkers and change advocates.",
                "age_range": "35-70",
                "income_level": "High income",
                "location": "Urban cultural centers",
                "tech_comfort": "High",
                "lifestyle": "Intellectual, progressive, culturally engaged, values education and discourse",
                "key_motivations": ["Intellectual stimulation", "Social justice", "Cultural engagement", "Progressive change", "Education"],
                "persona_count": 4
            },
            "Performer Milieu": {
                "segment_name": "Performer Milieu",
                "segment_description": "Success-oriented efficiency milieu focused on career advancement and material success. They are competitive, ambitious, and technology-savvy.",
                "age_range": "25-50",
                "income_level": "High income",
                "location": "Major urban centers",
                "tech_comfort": "Very High",
                "lifestyle": "Career-focused, competitive, efficiency-oriented, technology-savvy, status-conscious",
                "key_motivations": ["Career success", "Efficiency", "Competition", "Status", "Innovation"],
                "persona_count": 4
            },
            "Expeditive Milieu": {
                "segment_name": "Expeditive Milieu",
                "segment_description": "Young, pragmatic milieu that is flexible, success-oriented, and globally connected. They value mobility, networking, and quick solutions.",
                "age_range": "20-40",
                "income_level": "Upper middle to high income",
                "location": "Metropolitan areas",
                "tech_comfort": "Very High",
                "lifestyle": "Flexible, pragmatic, globally connected, mobile, networking-focused",
                "key_motivations": ["Flexibility", "Success", "Global connectivity", "Mobility", "Networking"],
                "persona_count": 4
            },
            "Adaptive Pragmatist Milieu": {
                "segment_name": "Adaptive Pragmatist Milieu",
                "segment_description": "Modern mainstream milieu that balances family life with professional ambitions. They are practical, adaptable, and seek work-life balance.",
                "age_range": "30-60",
                "income_level": "Middle to upper middle income",
                "location": "Suburban and urban areas",
                "tech_comfort": "High",
                "lifestyle": "Balanced, family-oriented, adaptable, practical, seeks harmony",
                "key_motivations": ["Work-life balance", "Family", "Practicality", "Adaptability", "Harmony"],
                "persona_count": 5
            },
            "Socio-ecological Milieu": {
                "segment_name": "Socio-ecological Milieu",
                "segment_description": "Environmentally and socially conscious milieu that prioritizes sustainability and social responsibility. They value authentic, ethical consumption.",
                "age_range": "25-55",
                "income_level": "Middle to upper middle income",
                "location": "Progressive urban and rural communities",
                "tech_comfort": "Medium to High",
                "lifestyle": "Environmentally conscious, socially responsible, values authenticity and sustainability",
                "key_motivations": ["Sustainability", "Social responsibility", "Authenticity", "Environmental protection", "Ethical consumption"],
                "persona_count": 4
            }
        }
    },
    "zero360 User Segments": {
        "description": "Contemporary German market segments based on modern consumer behaviors and digital adoption patterns.",
        "segments": {
            "Junge Berufsstarter": {
                "segment_name": "Junge Berufsstarter",
                "segment_description": "Junge Erwachsene zwischen 20-29 Jahren in den ersten Berufsjahren. Erstes regelmäßiges Einkommen, leben urban, nutzen alle digitalen Kanäle selbstverständlich. Experimentierfreudig bei neuen Marken und Services, steigendes Budget.",
                "age_range": "20-29",
                "income_level": "Niedrig bis Mittel (€25.000 - €45.000)",
                "location": "Großstädte, urbane Zentren",
                "tech_comfort": "Sehr hoch",
                "lifestyle": "Digital Native, WG-Leben oder erste eigene Wohnung, hohe Social Media Nutzung, experimentierfreudig bei Marken, Ausgehen und Networking wichtig, Work-Life-Balance suchend",
                "key_motivations": ["Karriereentwicklung", "Unabhängigkeit", "Soziale Anerkennung", "Neue Erfahrungen", "Preis-Leistung"],
                "persona_count": 5
            },
            "Premium-Käufer": {
                "segment_name": "Premium-Käufer",
                "segment_description": "Konsumenten mit hoher Kaufkraft und Luxuspräferenz. Qualität und Exklusivität vor Preis. Markentreu, erwarten exzellenten Service und besondere Einkaufserlebnisse.",
                "age_range": "30-70",
                "income_level": "Sehr hoch (€100.000+)",
                "location": "Beste Lagen, Großstädte",
                "tech_comfort": "Hoch",
                "lifestyle": "Luxusmarken, Statussymbole, Business Class, Premium-Services, Kunst und Kultur, Gourmet-Restaurants, Persönlicher Service",
                "key_motivations": ["Exklusivität", "Prestige", "Qualität", "Service", "Individualität"],
                "persona_count": 3
            },
            "Umweltbewusste Millennials": {
                "segment_name": "Umweltbewusste Millennials",
                "segment_description": "Starkes Umweltbewusstsein, reduzieren ökologischen Fußabdruck. Second-Hand und Sharing selbstverständlich. Unterstützen Purpose-Brands, boykottieren Umweltsünder.",
                "age_range": "28-40",
                "income_level": "Mittel (€35.000 - €65.000)",
                "location": "Großstädte, Szeneviertel",
                "tech_comfort": "Hoch",
                "lifestyle": "Second-Hand, Sharing Economy, Veggie/Vegan, Fahrrad/ÖPNV, Zero Waste, Aktivismus, Social Media für Causes",
                "key_motivations": ["Nachhaltigkeit", "Klimaschutz", "Fairness", "Authentizität", "Minimalismus"],
                "persona_count": 4
            },
            "Hybride Arbeiter": {
                "segment_name": "Hybride Arbeiter",
                "segment_description": "Flexibles Arbeitsmodell Home-Office/Büro. Schätzen Flexibilität, investieren in Home-Office. Work-Life-Integration statt Trennung.",
                "age_range": "25-55",
                "income_level": "Mittel bis Hoch (€40.000 - €85.000)",
                "location": "Städte und Umland",
                "tech_comfort": "Hoch",
                "lifestyle": "Home-Office Setup, Collaboration Tools, Flexible Zeiten, Coworking, Digital Nomad Tendenz, Selbstorganisation",
                "key_motivations": ["Flexibilität", "Work-Life-Integration", "Produktivität", "Autonomie", "Balance"],
                "persona_count": 4
            },
            "Generation Z": {
                "segment_name": "Generation Z",
                "segment_description": "Jüngste Konsumentengeneration, mit Internet aufgewachsen. Permanent online, Social Media zentral. Nachhaltigkeit und Purpose wichtig, kritisch gegenüber traditionellen Marken.",
                "age_range": "16-24",
                "income_level": "Niedrig (Taschengeld bis €30.000)",
                "location": "Überall, digital vernetzt",
                "tech_comfort": "Sehr hoch",
                "lifestyle": "Always-on, TikTok/Instagram native, Streaming statt TV, Gaming, Influencer-orientiert, Umweltbewusst, Diversität wichtig",
                "key_motivations": ["Authentizität", "Nachhaltigkeit", "Individualität", "Soziale Gerechtigkeit", "Instant Gratification"],
                "persona_count": 5
            },
            "Early Adopter": {
                "segment_name": "Early Adopter",
                "segment_description": "Technologiebegeisterte Erstkäufer neuer Produkte. Risikobereit, Meinungsführer, beeinflussen soziales Umfeld. Gut informiert über Neuheiten, überdurchschnittliches Einkommen.",
                "age_range": "25-45",
                "income_level": "Mittel bis Hoch (€50.000 - €100.000)",
                "location": "Großstädte, Tech-Hubs",
                "tech_comfort": "Sehr hoch",
                "lifestyle": "Tech-Gadgets, Crowdfunding-Backer, Beta-Tester, Tech-Blogs, Messen und Events, Opinion Leader, Social Media aktiv",
                "key_motivations": ["Innovation", "Erste sein", "Technologie", "Status", "Einfluss"],
                "persona_count": 4
            }
        }
    }
}

# Demo responses for different personas
DEMO_RESPONSES = {
    "Luxus-Bauherr": [
        "Das klingt interessant, aber entspricht das wirklich dem Premium-Standard, den ich für meine Villa erwarte?",
        "Wie unterscheidet sich das von dem, was jeder haben kann? Ich suche nach wirklich exklusiven Lösungen.",
        "Die Technologie ist beeindruckend, aber wird sie auch in zehn Jahren noch zeitgemäß sein?",
        "Können Sie mir Referenzen von vergleichbaren Projekten zeigen? Ich kenne die meisten Premium-Anbieter.",
        "Das Design gefällt mir, aber wie sieht es mit der handwerklichen Perfektion aus? Ich dulde keine Kompromisse bei der Qualität."
    ]
}

# Initialize session state for autonomous research
def initialize_session_state():
    defaults = {
        # Autonomous interview system
        'autonomous_interviews': [],  # List of completed autonomous interviews
        'current_product': {},  # Single product to test across all interviews
        'research_active': False,
        'interviews_completed': 0,
        'max_interviews': 10,
        
        # Current single interview (for monitoring)
        'current_interview': None,
        'current_interview_id': None,
        
        # UI state
        'current_step': 0,  # 0: Demographics, 1: Define Product, 2: Generate Interviews, 3: Analyze Results
        'flow_completed': [False, False, False, False],
        
        # New: Target demographics and personas
        'target_demographics': {},
        'assembled_personas': [],
        
        # Interview context configuration
        'interview_context': {
            'customer_status': 'Potential new customer (never used product)',
            'product_knowledge': 'Basic awareness',
            'purchase_intent': 'Considering purchase soon',
            'interview_setting': 'Product discovery interview',
            'conversation_style': 'Casual and exploratory',
            'specific_context': ''
        },
        
        # Legacy (for backward compatibility during transition)
        'demo_mode': False,
        'voice_mode': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Autonomous Interview Generation
def generate_diverse_persona() -> Dict:
    """Generate a diverse persona using AI with improved name diversity"""
    if not OPENAI_AVAILABLE:
        # No fallback personas available - return basic persona structure
        return {
            "name": "Sample Persona",
            "age": 35,
            "job": "Professional",
            "company": "Sample Company",
            "experience": "Sample experience description",
            "pain_points": "Sample pain points",
            "goals": "Sample goals",
            "personality": "Sample personality description"
        }
    
    # Diverse German names to ensure variety
    german_names = {
        'male_first': ['Alexander', 'Andreas', 'Bernd', 'Christian', 'Daniel', 'David', 'Dennis', 'Dirk', 'Felix', 'Florian', 'Frank', 'Günther', 'Hans', 'Heiko', 'Holger', 'Jan', 'Jens', 'Joachim', 'Jörg', 'Kai', 'Klaus', 'Lars', 'Lukas', 'Manuel', 'Marco', 'Marcus', 'Mario', 'Martin', 'Matthias', 'Max', 'Michael', 'Nico', 'Oliver', 'Patrick', 'Peter', 'Philipp', 'Ralf', 'Robert', 'Sebastian', 'Stefan', 'Thomas', 'Thorsten', 'Tim', 'Tobias', 'Uwe', 'Wolfgang'],
        'female_first': ['Alexandra', 'Andrea', 'Angela', 'Anja', 'Anna', 'Annette', 'Antje', 'Barbara', 'Birgit', 'Brigitte', 'Carmen', 'Carola', 'Claudia', 'Daniela', 'Doris', 'Eva', 'Gabi', 'Heike', 'Ines', 'Jana', 'Jennifer', 'Jessica', 'Julia', 'Karin', 'Katja', 'Katrin', 'Kerstin', 'Kristina', 'Laura', 'Lea', 'Lisa', 'Manuela', 'Maria', 'Marion', 'Martina', 'Melanie', 'Monika', 'Nadine', 'Nicole', 'Petra', 'Sabine', 'Sandra', 'Sara', 'Silke', 'Simone', 'Stefanie', 'Susanne', 'Tanja', 'Ute', 'Vanessa'],
        'surnames': ['Müller', 'Schmidt', 'Schneider', 'Fischer', 'Weber', 'Meyer', 'Wagner', 'Becker', 'Schulz', 'Hoffmann', 'Schäfer', 'Koch', 'Bauer', 'Richter', 'Klein', 'Wolf', 'Schröder', 'Neumann', 'Schwarz', 'Zimmermann', 'Braun', 'Krüger', 'Hofmann', 'Hartmann', 'Lange', 'Schmitt', 'Werner', 'Schmitz', 'Krause', 'Meier', 'Lehmann', 'Schmid', 'Schulze', 'Maier', 'Köhler', 'Herrmann', 'König', 'Walter', 'Mayer', 'Huber', 'Kaiser', 'Fuchs', 'Peters', 'Lang', 'Scholz', 'Möller', 'Weiß', 'Jung', 'Hahn', 'Schubert', 'Vogel', 'Friedrich', 'Keller', 'Günther', 'Frank', 'Berger', 'Winkler', 'Roth', 'Beck', 'Lorenz', 'Baumann', 'Franke', 'Albrecht', 'Ludwig', 'Winter', 'Kraus', 'Martin', 'Schenk', 'Krämer', 'Vogt', 'Stein', 'Jäger', 'Otto', 'Sommer', 'Groß', 'Seidel', 'Heinrich', 'Brandt', 'Haas', 'Schreiber', 'Graf', 'Schulte', 'Dietrich', 'Ziegler', 'Kuhn', 'Kühn', 'Pohl', 'Engel', 'Horn', 'Busch', 'Bergmann', 'Thomas', 'Voigt', 'Sauer', 'Arnold', 'Wolff', 'Pfeiffer']
    }
    
    import random
    
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Pre-select a diverse name to ensure variety
        gender = random.choice(['male', 'female'])
        first_name = random.choice(german_names[f'{gender}_first'])
        surname = random.choice(german_names['surnames'])
        full_name = f"{first_name} {surname}"
        
        response = client.chat.completions.create(
            model="gpt-4o",  # Use latest model for better quality
            messages=[
                {"role": "system", "content": f"""You are a persona generator for user research. Create diverse, realistic personas for bathroom/sanitary product research.

Generate a JSON object with these exact fields:
- name: Use exactly this name: "{full_name}"
- age: Age between 25-70
- job: Job title (varied professional backgrounds)
- company: Company description
- experience: Background and experience with bathroom products/renovations
- pain_points: Current challenges and frustrations
- goals: What they want to achieve
- personality: Communication style and decision-making approach

Make each persona unique with different demographics, life situations, and perspectives. Focus on realistic German customers with diverse backgrounds, income levels, family situations, and living arrangements. Avoid stereotypes and create authentic, multi-dimensional characters."""},
                {"role": "user", "content": "Generate a unique persona for bathroom product research."}
            ],
            max_tokens=800,
            temperature=0.9  # High temperature for diversity
        )
        
        import json
        persona_text = response.choices[0].message.content.strip()
        # Extract JSON from response if wrapped in markdown
        if "```json" in persona_text:
            persona_text = persona_text.split("```json")[1].split("```")[0]
        elif "```" in persona_text:
            persona_text = persona_text.split("```")[1]
            
        persona = json.loads(persona_text)
        return persona
        
    except Exception as e:
        st.error(f"Error generating persona: {str(e)}")
        # Return basic fallback persona
        return {
            "name": "Sample Persona",
            "age": 35,
            "job": "Professional",
            "company": "Sample Company",
            "experience": "Sample experience description",
            "pain_points": "Sample pain points",
            "goals": "Sample goals",
            "personality": "Sample personality description"
        }

def generate_interview_questions(persona: Dict, product: Dict, num_questions: int = 8, interview_context: Dict = None) -> List[str]:
    """Generate diverse interview questions for a persona and product with context"""
    if not OPENAI_AVAILABLE:
        return [
            f"Was ist Ihr erster Eindruck vom {product.get('name', 'Produkt')}?",
            "Welche Bedenken hätten Sie bei der Anschaffung?",
            "Wie würde das Ihren Alltag verändern?",
            "Was ist Ihnen bei Badezimmerprodukten am wichtigsten?",
            "Haben Sie schon mal ähnliche Produkte verwendet?",
            "Welche Probleme soll das Produkt für Sie lösen?",
            "Würden Sie das weiterempfehlen?",
            "Was fehlt Ihnen noch für eine Kaufentscheidung?"
        ]
    
    # Default context if none provided
    if interview_context is None:
        interview_context = {
            "customer_status": "Potential new customer (never used product)",
            "product_knowledge": "Basic awareness",
            "purchase_intent": "Considering purchase soon",
            "interview_setting": "Product discovery interview",
            "conversation_style": "Casual and exploratory",
            "specific_context": ""
        }
    
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Build context-aware prompt
        context_prompt = f"""
Interview Context:
- Customer Status: {interview_context.get('customer_status', 'Potential new customer')}
- Product Knowledge: {interview_context.get('product_knowledge', 'Basic awareness')}  
- Purchase Intent: {interview_context.get('purchase_intent', 'Considering purchase soon')}
- Interview Setting: {interview_context.get('interview_setting', 'Product discovery interview')}
- Conversation Style: {interview_context.get('conversation_style', 'Casual and exploratory')}
- Specific Context: {interview_context.get('specific_context', 'N/A')}

Persona: {persona.get('name', 'Person')} - {persona.get('job', 'Professional')}, Age {persona.get('age', 'Unknown')}
Product: {product.get('name', 'Product')}
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",  # Use improved model
            messages=[
                {"role": "system", "content": f"""You are a user research expert. Generate {num_questions} diverse, contextually appropriate interview questions in German.

{context_prompt}

Questions should:
1. Match the interview context and customer relationship
2. Be appropriate for the persona's knowledge level and intent
3. Follow natural conversation flow (avoid starting with job/professional role unless relevant)
4. Explore different aspects based on the scenario
5. Be open-ended and encourage detailed responses
6. Be in natural, conversational German
7. Consider the specific context if provided

For example:
- If "No prior knowledge": Start with awareness and discovery questions
- If "Existing customer": Focus on experience and satisfaction
- If "Ready to buy": Focus on final concerns and decision factors
- If "Just browsing": Focus on needs assessment and education

Return ONLY a JSON array of question strings, no other text."""},
                {"role": "user", "content": f"Generate {num_questions} contextually appropriate interview questions for this specific scenario."}
            ],
            max_tokens=800,
            temperature=0.8
        )
        
        import json
        questions_text = response.choices[0].message.content.strip()
        # Extract JSON from response if wrapped in markdown
        if "```json" in questions_text:
            questions_text = questions_text.split("```json")[1].split("```")[0]
        elif "```" in questions_text:
            questions_text = questions_text.split("```")[1]
            
        questions = json.loads(questions_text)
        return questions
        
    except Exception as e:
        st.error(f"Error generating questions: {str(e)}")
        return [
            f"Was ist Ihr erster Eindruck vom {product.get('name', 'Produkt')}?",
            "Welche Bedenken hätten Sie bei der Anschaffung?",
            "Wie würde das Ihren Alltag verändern?"
        ]

def conduct_autonomous_interview(persona: Dict, product: Dict, questions: List[str]) -> Dict:
    """Conduct a full autonomous interview with a persona"""
    interview_data = {
        'id': f"interview_{len(st.session_state.autonomous_interviews) + 1}",
        'persona': persona,
        'product': product,
        'timestamp': datetime.now(),
        'conversation': [],
        'metrics': {
            'sentiment_score': 0.5,
            'conviction_level': 0.5,
            'main_concerns': []
        },
        'status': 'running'
    }
    
    # Simulate conversation
    for i, question in enumerate(questions):
        # Add question
        interview_data['conversation'].append({
            'role': 'user',
            'content': question,
            'timestamp': datetime.now()
        })
        
        # Get AI response
        ai_response = get_openai_response(question, persona, product)
        interview_data['conversation'].append({
            'role': 'assistant',
            'content': ai_response,
            'timestamp': datetime.now()
        })
        
        # Update progress
        progress = (i + 1) / len(questions)
        if 'progress_placeholder' in st.session_state:
            st.session_state.progress_placeholder.progress(progress, f"Question {i+1}/{len(questions)}")
    
    # Calculate final metrics
    interview_data['metrics'] = calculate_interview_metrics(interview_data['conversation'])
    interview_data['status'] = 'completed'
    
    return interview_data

def calculate_interview_metrics(conversation: List[Dict]) -> Dict:
    """Calculate comprehensive metrics for a completed interview using NLU"""
    ai_messages = [msg['content'] for msg in conversation if msg['role'] == 'assistant']
    
    if not ai_messages:
        return {
            'sentiment_score': 0.5,
            'conviction_level': 0.5,
            'main_concerns': [],
            'emotions': {},
            'keywords': [],
            'dominant_emotion': 'neutral'
        }
    
    # Calculate average sentiment
    sentiments = [analyze_sentiment(msg) for msg in ai_messages]
    avg_sentiment = sum(sentiments) / len(sentiments)
    
    # Calculate conviction level
    conviction = calculate_conviction(conversation)
    
    # Extract concerns from all messages
    all_concerns = []
    for msg in ai_messages:
        all_concerns.extend(extract_concerns(msg))
    
    # Analyze emotions across all messages
    all_emotions = {}
    for msg in ai_messages:
        emotions = analyze_emotions(msg)
        for emotion, score in emotions.items():
            all_emotions[emotion] = all_emotions.get(emotion, 0) + score
    
    # Normalize emotion scores
    if all_emotions:
        total_emotion_score = sum(all_emotions.values())
        if total_emotion_score > 0:
            all_emotions = {k: v/total_emotion_score for k, v in all_emotions.items()}
    
    # Find dominant emotion
    dominant_emotion = 'neutral'
    if all_emotions:
        dominant_emotion = max(all_emotions.keys(), key=lambda k: all_emotions[k])
    
    # Extract keywords from all messages
    all_keywords = []
    for msg in ai_messages:
        all_keywords.extend(extract_keywords(msg))
    
    # Get unique keywords
    unique_keywords = list(set(all_keywords))[:10]  # Top 10 unique keywords
    
    return {
        'sentiment_score': avg_sentiment,
        'conviction_level': conviction,
        'main_concerns': list(set(all_concerns)),
        'emotions': all_emotions,
        'keywords': unique_keywords,
        'dominant_emotion': dominant_emotion
    }

# AI Response Functions
def get_openai_response(message: str, persona: Dict, product: Dict) -> str:
    """Get response from OpenAI API"""
    if not OPENAI_AVAILABLE:
        return "Entschuldigung, ich kann momentan nicht antworten. Bitte überprüfen Sie die API-Konfiguration."
    
    try:
        prompt = create_persona_prompt(persona, product)
        
        # Use the new OpenAI client format
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o",  # Use improved model
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=400,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        return f"Entschuldigung, es gab einen Fehler bei der Verbindung zur API: {str(e)}"

def create_persona_prompt(persona: Dict, product: Dict) -> str:
    """Create detailed persona prompt following best practices"""
    
    # Special handling for couple persona
    if "Sandra & Marco" in persona.get('name', ''):
        return f"""
# ROLE & OBJECTIVE
Sie sind Sandra & Marco Keller, ein Ehepaar mit drei Kindern (4, 8 und 11 Jahre). Ihr Ziel ist es, als potenzielle Kunden authentisch auf Produktvorstellungen zu reagieren und realistische Fragen aus Familiensicht zu stellen.

# PERSONALITY & TONE
- Sprechen Sie als Paar ("wir", "uns", "unser")
- Sandra: Organisiert, pragmatisch, detailorientiert
- Marco: Zahlenorientiert, vorsichtig bei Ausgaben
- Gemeinsam: Familienorientiert, zeitgestresst aber liebevoll

# CONTEXT
## Ihre Situation:
- Alter: Sandra 37, Marco 39 Jahre
- Jobs: {persona.get('job', 'Teilzeit-Controllerin & Vertriebsleiter')}
- Unternehmen: {persona.get('company', 'Energieversorgung & Medizintechnik')}
- Wohnsituation: {persona.get('experience', 'Reihenhaus mit drei Kindern')}

## Aktuelle Herausforderungen:
{persona.get('pain_points', 'Morgenstress im Bad, Budget-Druck, Organisationsaufwand')}

## Ihre Ziele:
{persona.get('goals', 'Familienalltag vereinfachen, robuste Lösungen finden')}

# REFERENCE PRONUNCIATIONS
- zero360: "ZERO-three-six-zero" (englisch)

# CONTEXT: PRODUKT IM GESPRÄCH
{product.get('description', 'Ein zero360 Produkt')}

Value Proposition: {product.get('value_prop', 'Verbesserung des Alltags')}

# INSTRUCTIONS / RULES
## DO:
- Reagieren Sie authentisch als Paar mit drei Kindern
- Stellen Sie praktische Fragen zur Familientauglichkeit
- Erwähnen Sie konkrete Alltagssituationen (Morgenstress, Kinder, Putzen)
- Zeigen Sie Interesse, aber auch berechtigte Budgetsorgen
- Denken Sie an Sicherheit und Robustheit für Kinder
- Antworten Sie auf Deutsch in 1-3 prägnanten Sätzen

## DON'T:
- Sprechen Sie niemals als Einzelperson ("ich")
- Vergessen Sie nicht die drei Kinder in Ihren Überlegungen
- Seien Sie nicht unrealistisch optimistisch - zeigen Sie echte Bedenken
- Ignorieren Sie nicht finanzielle Aspekte

# CONVERSATION FLOW
Sie befinden sich in einem User Research Interview. Reagieren Sie natürlich auf Produktvorstellungen mit einer Mischung aus Interesse und kritischen Nachfragen, wie es echte Eltern tun würden.

# SAFETY & ESCALATION
Bleiben Sie immer in der Rolle des Ehepaars. Falls technische Details zu komplex werden, fragen Sie nach einfacheren Erklärungen.
"""
    else:
        return f"""
# ROLE & OBJECTIVE
Sie sind {persona.get('name', 'eine Person')} und arbeiten als {persona.get('job', 'Fachkraft')}. Ihr Ziel ist es, als potenzielle/r Kunde/in authentisch auf Produktvorstellungen zu reagieren und realistische Fragen aus Ihrer beruflichen und persönlichen Perspektive zu stellen.

# PERSONALITY & TONE
{persona.get('personality', 'Professionell, kritisch, aber aufgeschlossen')}

# CONTEXT
## Ihre Situation:
- Alter: {persona.get('age', 30)} Jahre
- Position: {persona.get('job', 'Fachkraft')}
- Unternehmen: {persona.get('company', 'Ein Unternehmen')}
- Erfahrung: {persona.get('experience', 'Berufserfahrung')}

## Aktuelle Herausforderungen:
{persona.get('pain_points', 'Berufliche und persönliche Herausforderungen')}

## Ihre Ziele:
{persona.get('goals', 'Verbesserungen in Beruf und Alltag')}

# REFERENCE PRONUNCIATIONS
- zero360: "ZERO-three-six-zero" (englisch)

# CONTEXT: PRODUKT IM GESPRÄCH
{product.get('description', 'Ein zero360 Produkt')}

Value Proposition: {product.get('value_prop', 'Nutzen für den Anwender')}

# INSTRUCTIONS / RULES
## DO:
- Reagieren Sie authentisch aus Ihrer spezifischen Perspektive
- Stellen Sie kritische Fragen basierend auf Ihren Pain Points
- Erwähnen Sie konkrete Beispiele aus Ihrem Arbeits-/Lebensalltag
- Zeigen Sie sowohl Interesse als auch berechtigte Skepsis
- Berücksichtigen Sie Ihre spezielle Lebenssituation
- Antworten Sie auf Deutsch in 1-3 prägnanten Sätzen

## DON'T:
- Seien Sie nicht unrealistisch begeistert
- Ignorieren Sie nicht Ihre spezifischen Bedürfnisse und Einschränkungen
- Vergessen Sie nicht Ihre berufliche Expertise
- Seien Sie nicht unhöflich, aber durchaus kritisch

# CONVERSATION FLOW
Sie befinden sich in einem User Research Interview. Reagieren Sie natürlich auf Produktvorstellungen mit einer Mischung aus professionellem Interesse und kritischen Nachfragen.

# SAFETY & ESCALATION
Bleiben Sie immer in Ihrer Rolle. Falls Fragen außerhalb Ihres Expertisebereichs gestellt werden, verweisen Sie höflich auf Ihre spezifische Perspektive.
"""

# Removed old question generation functions - now using AI-generated questions in autonomous research

# Analytics Functions
def analyze_sentiment(text: str) -> float:
    """Advanced sentiment analysis using TextBlob and VADER"""
    if NLP_AVAILABLE and text.strip():
        try:
            # Use VADER for sentiment analysis (better for informal text)
            analyzer = get_sentiment_analyzer()
            vader_scores = analyzer.polarity_scores(text)
            
            # VADER compound score ranges from -1 to 1, convert to 0-1
            vader_sentiment = (vader_scores['compound'] + 1) / 2
            
            # Use TextBlob as secondary analysis
            blob = TextBlob(text)
            textblob_sentiment = (blob.sentiment.polarity + 1) / 2
            
            # Average the two approaches for more robust analysis
            combined_sentiment = (vader_sentiment + textblob_sentiment) / 2
            
            return max(0.0, min(1.0, combined_sentiment))
            
        except Exception as e:
            # Fall back to simple analysis if NLP fails
            pass
    
    # Fallback: Enhanced keyword-based sentiment analysis
    positive_words = [
        'gut', 'toll', 'super', 'perfekt', 'interessant', 'hilfreich', 'gefällt', 'liebe', 
        'positiv', 'zufrieden', 'empfehlen', 'begeistert', 'fantastisch', 'großartig',
        'excellent', 'great', 'good', 'amazing', 'wonderful', 'love', 'like', 'positive'
    ]
    negative_words = [
        'schlecht', 'problem', 'schwierig', 'teuer', 'kompliziert', 'frustrierend', 
        'negativ', 'enttäuscht', 'unzufrieden', 'ärgerlich', 'furchtbar', 'schrecklich',
        'bad', 'terrible', 'awful', 'hate', 'dislike', 'negative', 'poor', 'disappointing'
    ]
    
    text_lower = text.lower()
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)
    
    if pos_count + neg_count == 0:
        return 0.5
    
    return pos_count / (pos_count + neg_count)

def analyze_emotions(text: str) -> Dict[str, float]:
    """Analyze emotions in text using TextBlob and enhanced keyword matching"""
    emotions = {}
    
    if NLP_AVAILABLE and text.strip():
        try:
            # Use TextBlob for basic sentiment analysis as emotion base
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # Map sentiment to basic emotions
            if polarity > 0.3:
                emotions['joy'] = min(1.0, polarity)
                emotions['trust'] = min(1.0, polarity * 0.8)
            elif polarity < -0.3:
                emotions['anger'] = min(1.0, abs(polarity))
                emotions['sadness'] = min(1.0, abs(polarity) * 0.8)
            
            # High subjectivity might indicate surprise or strong emotions
            if subjectivity > 0.7:
                emotions['surprise'] = min(1.0, subjectivity * 0.6)
                
        except Exception as e:
            pass
    
    # Enhanced emotion detection based on keywords (German + English)
    emotion_keywords = {
        'joy': [
            'freude', 'glücklich', 'begeistert', 'toll', 'super', 'fantastisch', 'wunderbar',
            'joy', 'happy', 'excited', 'great', 'amazing', 'wonderful', 'love', 'delighted'
        ],
        'trust': [
            'vertrauen', 'sicher', 'zuverlässig', 'glaubwürdig', 'professionell', 'qualität',
            'trust', 'reliable', 'safe', 'secure', 'professional', 'quality', 'confident'
        ],
        'fear': [
            'angst', 'sorge', 'bedenken', 'risiko', 'unsicher', 'zweifel', 'vorsicht',
            'fear', 'worry', 'concern', 'risk', 'uncertain', 'doubt', 'anxious'
        ],
        'anger': [
            'ärger', 'frustriert', 'wütend', 'schlecht', 'problem', 'ärgerlich',
            'anger', 'frustrated', 'angry', 'annoyed', 'irritated', 'upset'
        ],
        'surprise': [
            'überrascht', 'wow', 'erstaunlich', 'unglaublich', 'überraschend', 'unerwartet',
            'surprised', 'wow', 'amazing', 'incredible', 'unexpected', 'astonishing'
        ],
        'sadness': [
            'traurig', 'enttäuscht', 'bedauerlich', 'schade', 'unglücklich',
            'sad', 'disappointed', 'unfortunate', 'regret', 'unhappy'
        ]
    }
    
    text_lower = text.lower()
    
    for emotion, keywords in emotion_keywords.items():
        # Count keyword matches
        matches = sum(1 for keyword in keywords if keyword in text_lower)
        if matches > 0:
            # Calculate score based on matches and keyword list size
            keyword_score = min(1.0, matches / max(len(keywords) * 0.3, 1))
            
            # Combine with any existing score from TextBlob
            existing_score = emotions.get(emotion, 0)
            emotions[emotion] = max(existing_score, keyword_score)
    
    return emotions

def extract_keywords(text: str) -> List[str]:
    """Extract key terms and topics from text using TextBlob and enhanced filtering"""
    keywords = []
    
    if NLP_AVAILABLE and text.strip():
        try:
            # Use TextBlob for noun phrase extraction
            blob = TextBlob(text)
            noun_phrases = blob.noun_phrases
            
            # Add significant noun phrases
            for phrase in noun_phrases:
                if len(phrase) > 3:  # Filter short phrases
                    keywords.append(phrase.lower())
            
        except Exception as e:
            pass
    
    # Enhanced keyword extraction using regex and filtering
    # Extract words of 4+ characters
    words = re.findall(r'\b\w{4,}\b', text.lower())
    
    # Comprehensive stop words (German + English)
    stop_words = {
        # German
        'dass', 'eine', 'eines', 'einer', 'haben', 'wird', 'sind', 'kann', 'auch', 
        'aber', 'oder', 'und', 'der', 'die', 'das', 'den', 'dem', 'des', 'sich', 
        'nicht', 'mit', 'für', 'auf', 'von', 'zu', 'im', 'ist', 'war', 'hat',
        'wurde', 'werden', 'sein', 'ihre', 'seiner', 'diesem', 'diese', 'dieses',
        'wenn', 'dann', 'weil', 'durch', 'nach', 'vor', 'über', 'unter', 'zwischen',
        # English
        'that', 'have', 'will', 'are', 'can', 'also', 'but', 'and', 'the', 'with',
        'for', 'from', 'not', 'was', 'has', 'been', 'would', 'could', 'should',
        'this', 'these', 'those', 'when', 'then', 'because', 'through', 'after',
        'before', 'over', 'under', 'between'
    }
    
    # Filter meaningful words
    filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
    
    # Combine with noun phrases
    all_keywords = keywords + filtered_words
    
    # Count frequency and return top keywords
    from collections import Counter
    word_counts = Counter(all_keywords)
    top_keywords = [word for word, count in word_counts.most_common(8)]
    
    return top_keywords

def extract_concerns(text: str) -> List[str]:
    """Extract main concerns from text"""
    concern_patterns = [
        r'(kosten|preis|budget|teuer)',
        r'(zeit|dauer|schnell|langsam)',
        r'(sicher|risiko|datenschutz)',
        r'(komplex|kompliziert|schwierig)',
        r'(integration|kompatibel)',
        r'(support|hilfe|schulung)'
    ]
    
    concerns = []
    text_lower = text.lower()
    
    for pattern in concern_patterns:
        if re.search(pattern, text_lower):
            if 'kosten' in pattern and re.search(pattern, text_lower):
                concerns.append('💰 Kosten')
            elif 'zeit' in pattern and re.search(pattern, text_lower):
                concerns.append('⏱️ Zeit')
            elif 'sicher' in pattern and re.search(pattern, text_lower):
                concerns.append('🔒 Sicherheit')
            elif 'komplex' in pattern and re.search(pattern, text_lower):
                concerns.append('🧩 Komplexität')
            elif 'integration' in pattern and re.search(pattern, text_lower):
                concerns.append('🔗 Integration')
            elif 'support' in pattern and re.search(pattern, text_lower):
                concerns.append('🆘 Support')
    
    return list(set(concerns))

def calculate_conviction(chat_history: List) -> float:
    """Calculate conviction level based on chat progression"""
    if not chat_history:
        return 0.0
    
    positive_indicators = 0
    total_messages = len([msg for msg in chat_history if msg['role'] == 'assistant'])
    
    for msg in chat_history:
        if msg['role'] == 'assistant':
            sentiment = analyze_sentiment(msg['content'])
            if sentiment > 0.6:
                positive_indicators += 1
    
    return min(positive_indicators / max(total_messages, 1), 1.0)

# Removed old manual interview functions - now using autonomous research

# New: Autonomous Research Navigation Bar
def render_nav_bar():
    """Render navigation bar for autonomous research flow"""
    st.markdown(f"""
    <div class="nav-bar">
        <h1>🤖 zero360 Autonomous Research Lab</h1>
        <div class="status-indicator">
            <div class="status-badge {'success' if OPENAI_AVAILABLE else 'error'}">
                {'✅ AI Ready' if OPENAI_AVAILABLE else '⚠️ API Key Missing'}
            </div>
            <div class="status-badge {'success' if NLP_AVAILABLE else 'error'}">
                {'✅ Advanced NLP models loaded successfully!' if NLP_AVAILABLE else '⚠️ Basic NLP only'}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Step-based navigation with progress indicator
    st.markdown("### 🚀 Autonomous Research Flow")
    
    # Progress indicator using Streamlit columns instead of HTML
    st.markdown("**Progress:**")
    
    steps = [
        ("👥 Demographics", st.session_state.flow_completed[0]),
        ("🚀 Product", st.session_state.flow_completed[1]),
        ("🤖 Generate", st.session_state.flow_completed[2]),
        ("📊 Analyze", st.session_state.flow_completed[3])
    ]
    
    progress_cols = st.columns(4)
    
    for i, (step_name, completed) in enumerate(steps):
        with progress_cols[i]:
            is_current = st.session_state.current_step == i
            
            if completed:
                status_icon = "✅"
                status_text = "Complete"
            elif is_current:
                status_icon = "🔵"
                status_text = "Current"
            else:
                status_icon = "⚪"
                status_text = "Pending"
            
            st.markdown(f"""
            <div style="text-align: center; padding: 15px; border-radius: 12px; background: {'#f0f9ff' if is_current else '#f8fafc'}; border: {'2px solid #3b82f6' if is_current else '1px solid #e2e8f0'};">
                <div style="font-size: 32px; margin-bottom: 8px;">{status_icon}</div>
                <div style="font-size: 16px; font-weight: 700; margin: 8px 0;">Step {i + 1}</div>
                <div style="font-size: 14px; color: #64748b; font-weight: 500;">{step_name}</div>
                <div style="font-size: 12px; color: #9ca3af; margin-top: 4px;">{status_text}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Step navigation buttons
    step_cols = st.columns(4)
    
    step_buttons = [
        ("Step 1: Target Demographics", 0, "👥"),
        ("Step 2: Define Product", 1, "🚀"),
        ("Step 3: Generate Interviews", 2, "🤖"),
        ("Step 4: Analyze Results", 3, "📊")
    ]
    
    for i, (label, step_num, emoji) in enumerate(step_buttons):
        with step_cols[i]:
            is_current = st.session_state.current_step == step_num
            is_completed = st.session_state.flow_completed[step_num]
            
            # Determine button type and availability
            if is_completed:
                button_type = "secondary"
                disabled = False
            elif is_current:
                button_type = "primary"
                disabled = False
            elif step_num == 0:  # Step 1 is always available
                button_type = "secondary"
                disabled = False
            elif step_num > 0 and st.session_state.flow_completed[step_num - 1]:  # Previous step completed
                button_type = "secondary"
                disabled = False
            else:
                button_type = "secondary"
                disabled = True
            
            if st.button(f"{emoji} {label}", 
                        key=f"step_{step_num}", 
                        use_container_width=True,
                        type=button_type,
                        disabled=disabled):
                st.session_state.current_step = step_num
                st.rerun()
    
    st.markdown("---")

# Sidebar for Autonomous Research Stats
def render_sidebar_stats():
    """Render sidebar with autonomous research stats"""
    with st.sidebar:
        st.markdown("### 🤖 Autonomous Research")
        
        # Current demographics info
        if st.session_state.target_demographics:
            st.markdown("#### 👥 Target Demographics")
            demographics = st.session_state.target_demographics
            st.info(f"**{demographics.get('segment_name', 'Custom Segment')}**")
            st.write(f"Age: {demographics.get('age_range', 'Not defined')}")
            st.write(f"Personas: {len(st.session_state.assembled_personas)}")
        
        # Current product info
        if st.session_state.current_product:
            st.markdown("#### 🚀 Current Product")
            product = st.session_state.current_product
            st.info(f"**{product.get('name', 'Unnamed Product')}**")
            st.write(f"Target: {product.get('target_market', 'Not defined')}")
        
        # Interview progress
        if st.session_state.autonomous_interviews:
            st.markdown("#### 📊 Interview Progress")
            completed = len([i for i in st.session_state.autonomous_interviews if i['status'] == 'completed'])
            st.metric("Completed Interviews", completed)
            st.metric("Total Interviews", len(st.session_state.autonomous_interviews))
            
            # Quick stats from completed interviews
            if completed > 0:
                completed_interviews = [i for i in st.session_state.autonomous_interviews if i['status'] == 'completed']
                avg_sentiment = sum(i['metrics']['sentiment_score'] for i in completed_interviews) / len(completed_interviews)
                avg_conviction = sum(i['metrics']['conviction_level'] for i in completed_interviews) / len(completed_interviews)
                
                st.metric("Avg Sentiment", f"{avg_sentiment:.1%}")
                st.metric("Avg Conviction", f"{avg_conviction:.1%}")
        else:
            st.markdown("#### ℹ️ Getting Started")
            st.info("Define your target demographics in Step 1 to begin autonomous research.")
        
        # Current interview status
        if st.session_state.research_active:
            st.markdown("#### ⚡ Status")
            st.warning("🔄 Research in progress...")
            if st.session_state.current_interview:
                current = st.session_state.current_interview
                st.write(f"**Current:** {current['persona']['name']}")
                st.write(f"**Status:** {current['status']}")
        
        # Quick actions
        st.markdown("#### 🔧 Quick Actions")
        if st.button("🔄 Reset All", use_container_width=True):
            st.session_state.autonomous_interviews = []
            st.session_state.current_product = {}
            st.session_state.target_demographics = {}
            st.session_state.assembled_personas = []
            st.session_state.research_active = False
            st.session_state.interviews_completed = 0
            st.session_state.current_step = 0
            st.session_state.flow_completed = [False, False, False, False]
            st.rerun()

# Removed old column rendering functions - now using autonomous research flow

def render_main_content():
    """Render main content based on current autonomous research step"""
    step = st.session_state.current_step
    
    if step == 0:
        render_step0_define_demographics()
    elif step == 1:
        render_step1_define_product()
    elif step == 2:
        render_step2_generate_interviews()
    elif step == 3:
        render_step3_analyze_results()
    else:
        # Default to step 0 if no valid step is set
        st.session_state.current_step = 0
        render_step0_define_demographics()


def render_step0_define_demographics():
    """Step 1: Define Target Demographics and Assemble Personas"""
    st.markdown("## Step 1: Define Target Demographics & Segment 👥")
    st.markdown("Define your target user demographics and segment. AI will assemble a representative group of personas based on your specifications.")
    
    # Demographics Definition
    # Option 1: Custom Demographics
    st.markdown("#### ✏️ Define Custom Demographics")
    
    with st.expander("🎨 Create Custom Demographics", expanded=False):
        with st.form("custom_demographics_form"):
            st.markdown("Define your target demographics and segment characteristics:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                segment_name = st.text_input("Segment Name*", placeholder="e.g., Tech-Savvy Renovators")
                age_range = st.text_input("Age Range*", placeholder="e.g., 30-50")
                income_level = st.selectbox("Income Level", 
                                          ["Low (< €30k)", "Medium (€30k-60k)", "Medium-High (€60k-100k)", 
                                           "High (€100k+)", "Business/Corporate", "Varied"])
                location = st.text_input("Geographic Location", placeholder="e.g., Urban Germany, Suburban areas")
            
            with col2:
                lifestyle = st.text_area("Lifestyle & Characteristics", 
                                       placeholder="Describe their lifestyle, values, and characteristics...")
                tech_comfort = st.selectbox("Technology Comfort", ["Low", "Medium", "High", "Varied"])
            
            motivations = st.text_area("Key Motivations (one per line)", 
                                     placeholder="Quality\nInnovation\nValue for money\nConvenience")
            segment_description = st.text_area("Segment Description*", 
                                             placeholder="Detailed description of this demographic segment...")
            
            persona_count = st.slider("Number of Personas to Generate", min_value=3, max_value=8, value=5,
                                    help="How many representative personas should AI create for this demographic?")
            
            if st.form_submit_button("🤖 Create Demographics & Generate Personas", type="primary"):
                if segment_name and age_range and segment_description:
                    motivations_list = [m.strip() for m in motivations.split('\n') if m.strip()] if motivations else []
                    
                    custom_demographics = {
                        'segment_name': segment_name,
                        'age_range': age_range,
                        'income_level': income_level,
                        'location': location,
                        'lifestyle': lifestyle,
                        'tech_comfort': tech_comfort,
                        'key_motivations': motivations_list,
                        'segment_description': segment_description,
                        'persona_count': persona_count
                    }
                    
                    st.session_state.target_demographics = custom_demographics
                    st.success(f"✅ Custom demographics '{segment_name}' created!")
                    # Auto-generate personas
                    generate_personas_for_demographic(custom_demographics, segment_name)
                    st.rerun()
                else:
                    st.error("Please fill in all required fields marked with *")
    
    # Option 2: Built-in Segment Browser
    st.markdown("#### 🎯 Browse Built-in Segments")
    st.markdown("Select from professionally researched segmentation frameworks:")
    
    # Quick overview of available segments
    with st.expander("📊 Quick Overview of Available Segments", expanded=False):
        for framework_name, framework_info in BUILT_IN_SEGMENTS.items():
            st.markdown(f"**{framework_name}** ({len(framework_info['segments'])} segments)")
            st.caption(framework_info['description'])
            
            # Show segment names in a compact format
            segments_list = list(framework_info['segments'].keys())
            if len(segments_list) > 6:
                displayed_segments = segments_list[:6] + [f"... and {len(segments_list) - 6} more"]
            else:
                displayed_segments = segments_list
            
            st.markdown(f"*{', '.join(displayed_segments)}*")
            st.markdown("---")
    
    # Framework selection
    framework_options = ["Select a framework..."] + list(BUILT_IN_SEGMENTS.keys())
    selected_framework = st.selectbox(
        "Choose a segmentation framework:",
        framework_options,
        key="selected_framework",
        help="Each framework offers different perspectives on consumer segmentation"
    )
    
    if selected_framework and selected_framework != "Select a framework...":
        framework_data = BUILT_IN_SEGMENTS[selected_framework]
        
        # Show framework description
        st.info(f"**{selected_framework}**: {framework_data['description']}")
        
        # Segment selection within framework
        segment_options = ["Select a segment..."] + list(framework_data["segments"].keys())
        selected_built_in_segment = st.selectbox(
            f"Choose a segment from {selected_framework}:",
            segment_options,
            key="selected_built_in_segment"
        )
        
        if selected_built_in_segment and selected_built_in_segment != "Select a segment...":
            segment_data = framework_data["segments"][selected_built_in_segment]
            
            # Show segment preview with enhanced styling
            with st.expander(f"📋 Preview: {selected_built_in_segment}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Age Range:** {segment_data.get('age_range', 'Not specified')}")
                    st.write(f"**Income Level:** {segment_data.get('income_level', 'Not specified')}")
                    st.write(f"**Location:** {segment_data.get('location', 'Not specified')}")
                with col2:
                    st.write(f"**Tech Comfort:** {segment_data.get('tech_comfort', 'Not specified')}")
                    st.write(f"**Personas to Generate:** {segment_data.get('persona_count', 5)}")
                    if segment_data.get('key_motivations'):
                        st.write(f"**Key Motivations:** {', '.join(segment_data['key_motivations'])}")
                
                st.write("**Description:**")
                st.write(segment_data.get('segment_description', 'No description provided'))
                
                if segment_data.get('lifestyle'):
                    st.write("**Lifestyle & Characteristics:**")
                    st.write(segment_data['lifestyle'])
            
            # Button to use this segment
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(f"🎯 Use '{selected_built_in_segment}' Segment", 
                           key=f"use_builtin_segment_{selected_built_in_segment}",
                           type="primary"):
                    st.session_state.target_demographics = segment_data.copy()
                    st.session_state.assembled_personas = []  # Reset personas
                    st.success(f"✅ Selected built-in segment: {selected_built_in_segment}")
                    
                    # Auto-generate personas for this segment
                    generate_personas_for_demographic(segment_data, selected_built_in_segment)
                    st.rerun()
            
            with col2:
                # Add framework badge
                framework_short = selected_framework.split()[0]  # Get first word
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 8px 12px; border-radius: 20px; 
                           text-align: center; font-size: 12px; font-weight: bold;">
                    {framework_short}
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Option 3: Bulk Data Import
    st.markdown("#### 📊 Custom Data Import")
    st.markdown("Upload your own custom demographic segments:")
    
    # Initialize session state for predefined segments
    if 'predefined_segments' not in st.session_state:
        st.session_state.predefined_segments = {}
    
    # File upload section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload Predefined Segments (CSV or Excel)",
            type=['csv', 'xlsx', 'xls'],
            help="Upload a file with predefined demographic segments. Download the template below to see the required format."
        )
        
        if uploaded_file is not None:
            with st.spinner("Loading predefined segments..."):
                loaded_segments = load_predefined_segments_from_file(uploaded_file)
                if loaded_segments:
                    st.session_state.predefined_segments.update(loaded_segments)
                    st.success(f"✅ Loaded {len(loaded_segments)} predefined segments!")
    
    with col2:
        # Download template
        template_df = create_segment_template_download()
        csv_template = template_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Template",
            data=csv_template,
            file_name="predefined_segments_template.csv",
            mime="text/csv",
            help="Download a CSV template with example segments"
        )
    
    # Display loaded segments
    if st.session_state.predefined_segments:
        st.markdown("**Available Predefined Segments:**")
        
        # Create selectbox for segments
        segment_options = ["Select a segment..."] + list(st.session_state.predefined_segments.keys())
        selected_segment = st.selectbox(
            "Choose a predefined segment:",
            segment_options,
            key="selected_predefined_segment"
        )
        
        if selected_segment and selected_segment != "Select a segment...":
            segment_data = st.session_state.predefined_segments[selected_segment]
            
            # Show segment preview
            with st.expander(f"📋 Preview: {selected_segment}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Age Range:** {segment_data.get('age_range', 'Not specified')}")
                    st.write(f"**Income Level:** {segment_data.get('income_level', 'Not specified')}")
                    st.write(f"**Location:** {segment_data.get('location', 'Not specified')}")
                with col2:
                    st.write(f"**Tech Comfort:** {segment_data.get('tech_comfort', 'Not specified')}")
                    st.write(f"**Lifestyle:** {segment_data.get('lifestyle', 'Not specified')}")
                    if segment_data.get('key_motivations'):
                        st.write(f"**Key Motivations:** {', '.join(segment_data['key_motivations'])}")
                
                st.write("**Description:**")
                st.write(segment_data.get('segment_description', 'No description provided'))
            
            # Button to use this segment
            if st.button(f"🎯 Use '{selected_segment}' Segment", key=f"use_segment_{selected_segment}"):
                st.session_state.target_demographics = segment_data.copy()
                st.session_state.assembled_personas = []  # Reset personas
                st.success(f"✅ Selected predefined segment: {selected_segment}")
                
                # Auto-generate personas for this segment
                generate_personas_for_demographic(segment_data, selected_segment)
                st.rerun()
    
    else:
        st.info("📋 No predefined segments loaded. Upload a CSV or Excel file to get started, or download the template above.")
    
    # Show current demographics and assembled personas
    if st.session_state.target_demographics:
        st.markdown("### ✅ Current Target Demographics")
        demographics = st.session_state.target_demographics
        
        st.success(f"👥 **{demographics.get('segment_name', 'Custom Segment')}**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Age Range:** {demographics.get('age_range', 'Not specified')}")
            st.write(f"**Income Level:** {demographics.get('income_level', 'Not specified')}")
            st.write(f"**Location:** {demographics.get('location', 'Not specified')}")
            st.write(f"**Tech Comfort:** {demographics.get('tech_comfort', 'Not specified')}")
        with col2:
            st.write(f"**Lifestyle:** {demographics.get('lifestyle', 'Not specified')}")
            if demographics.get('key_motivations'):
                st.write(f"**Key Motivations:** {', '.join(demographics['key_motivations'])}")
        
        st.write("**Segment Description:**")
        st.write(demographics.get('segment_description', 'No description provided'))
        
        # Show assembled personas
        if st.session_state.assembled_personas:
            st.markdown("### 🤖 AI-Assembled Personas")
            st.info(f"Generated {len(st.session_state.assembled_personas)} representative personas for this demographic segment:")
            
            persona_cols = st.columns(min(3, len(st.session_state.assembled_personas)))
            
            for i, persona in enumerate(st.session_state.assembled_personas):
                col = persona_cols[i % len(persona_cols)]
                
                with col:
                    with st.expander(f"👤 {persona.get('name', 'Persona')} ({persona.get('age', '?')})", expanded=False):
                        st.write(f"**Job:** {persona.get('job', 'Not specified')}")
                        st.write(f"**Company:** {persona.get('company', 'Not specified')}")
                        st.write("**Background:**")
                        experience = persona.get('experience', 'No background provided')
                        if isinstance(experience, str):
                            st.write(experience[:200] + ("..." if len(experience) > 200 else ""))
                        else:
                            st.write(str(experience)[:200] + "...")
                        
                        st.write("**Key Concerns:**")
                        pain_points = persona.get('pain_points', 'No concerns listed')
                        if isinstance(pain_points, str):
                            st.write(pain_points[:150] + ("..." if len(pain_points) > 150 else ""))
                        elif isinstance(pain_points, list):
                            st.write('; '.join(pain_points)[:150] + ("..." if len('; '.join(pain_points)) > 150 else ""))
                        else:
                            st.write(str(pain_points)[:150] + "...")
            
            # Regenerate personas button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🔄 Regenerate Personas", use_container_width=True):
                    generate_personas_for_demographic(demographics, demographics.get('segment_name', 'Custom'))
                    st.rerun()
        
        # Navigation buttons
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col3:
            if st.session_state.assembled_personas:
                if st.button("➡️ Continue to Step 2: Define Product", type="primary", use_container_width=True):
                    st.session_state.flow_completed[0] = True
                    st.session_state.current_step = 1
                    st.rerun()
            else:
                st.button("➡️ Generate personas first", disabled=True, use_container_width=True)

def generate_personas_for_demographic(demographics: Dict, segment_name: str):
    """Generate representative personas based on demographic data using AI"""
    if not OPENAI_AVAILABLE:
        st.error("OpenAI API not available. Cannot generate personas without API access.")
        st.session_state.assembled_personas = []
        return
    
    try:
        with st.spinner(f"🤖 Assembling {demographics.get('persona_count', 5)} representative personas for {segment_name}..."):
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            
            personas = []
            persona_count = demographics.get('persona_count', 5)
            
            for i in range(persona_count):
                response = client.chat.completions.create(
                    model="gpt-4o",  # Use improved model
                    messages=[
                        {"role": "system", "content": f"""You are a persona generator for user research. Create realistic, diverse personas that represent the target demographic segment.

TARGET DEMOGRAPHIC SEGMENT: {segment_name}
- Age Range: {demographics.get('age_range', 'Not specified')}
- Income Level: {demographics.get('income_level', 'Not specified')}
- Location: {demographics.get('location', 'Not specified')}
- Lifestyle: {demographics.get('lifestyle', 'Not specified')}
- Tech Comfort: {demographics.get('tech_comfort', 'Not specified')}
- Key Motivations: {', '.join(demographics.get('key_motivations', []))}
- Segment Description: {demographics.get('segment_description', 'Not specified')}

Generate a JSON object with these exact fields (all values must be STRINGS):
- name: Full German name appropriate for the demographic (STRING)
- age: Specific age within the range (NUMBER as INTEGER)
- job: Job title that fits the income/lifestyle profile (STRING)
- company: Company description that matches the profile (STRING)  
- experience: Background with bathroom products/renovations fitting their experience level (STRING - paragraph format)
- pain_points: Current challenges and frustrations relevant to this demographic (STRING - paragraph format, not a list)
- goals: What they want to achieve, aligned with key motivations (STRING - paragraph format)
- personality: Communication style and decision-making approach fitting the segment (STRING - paragraph format)

IMPORTANT: All fields except 'age' must be strings. Do not use arrays/lists for any field. Write pain_points, goals, etc. as coherent paragraphs.

Make each persona unique while staying within the demographic parameters. Focus on realistic German customers that truly represent this segment."""},
                        {"role": "user", "content": f"Generate persona {i+1} of {persona_count} for the {segment_name} demographic segment. Make it distinct from previous personas while staying within the demographic parameters."}
                    ],
                    max_tokens=800,
                    temperature=0.8
                )
                
                persona_text = response.choices[0].message.content.strip()
                # Extract JSON from response if wrapped in markdown
                if "```json" in persona_text:
                    persona_text = persona_text.split("```json")[1].split("```")[0]
                elif "```" in persona_text:
                    persona_text = persona_text.split("```")[1]
                
                import json
                try:
                    persona = json.loads(persona_text)
                    # Ensure all fields are proper types
                    if isinstance(persona.get('pain_points'), list):
                        persona['pain_points'] = '; '.join(persona['pain_points'])
                    if isinstance(persona.get('goals'), list):
                        persona['goals'] = '; '.join(persona['goals'])
                    if isinstance(persona.get('experience'), list):
                        persona['experience'] = '; '.join(persona['experience'])
                    personas.append(persona)
                except json.JSONDecodeError as e:
                    st.warning(f"Failed to parse persona {i+1}, skipping")
                    # Skip invalid personas instead of using fallback
            
            st.session_state.assembled_personas = personas
            st.success(f"✅ Successfully generated {len(personas)} personas for {segment_name}!")
            
    except Exception as e:
        st.error(f"Error generating personas: {str(e)}")
        st.session_state.assembled_personas = []

def render_step1_define_product():
    """Step 2: Define Product for Autonomous Research"""
    st.markdown("## Step 2: Define Product to Test 🚀")
    st.markdown("Define the product you want to test with autonomous AI-generated interviews. The system will create diverse personas and conduct interviews automatically.")
    
    # Option 1: Quick Products
    st.markdown("### 🚀 Quick Product Templates")
    st.markdown("Select from pre-defined products:")
    
    DEFAULT_PRODUCTS = {
        "🏠 FlexSpace System": {
            "name": "FlexSpace System",
            "description": "Modulares Duschsystem mit magnetischer Wandschiene, das sich an verändernde Lebenssituationen anpasst. Komponenten können werkzeuglos angebracht werden - von Handbrausen auf Kinderhöhe bis zu Duschsitzen mit Haltegriffen.",
            "value_prop": "Maximale Flexibilität durch modularen Aufbau. Passt sich an alle Lebensphasen an - von der ersten Wohnung bis zum altersgerechten Bad.",
            "target_market": "Mieter, junge Familien, Menschen in Veränderungsphasen",
            "key_features": ["Magnetische Wandschiene", "Werkzeuglose Montage", "Modulare Komponenten", "Höhenverstellbar"]
        },
        "🤖 AIR System": {
            "name": "AIR (Adaptive Intelligent Room)",
            "description": "Intelligentes Badezimmersystem mit dezenten Sensoren in den Armaturen. Erfasst Nutzungsmuster, analysiert Wasserqualität in Echtzeit und optimiert selbstständig.",
            "value_prop": "KI-gesteuerte Optimierung des gesamten Badezimmers. Automatische Anpassung an Nutzergewohnheiten, präventive Wartung und professionelle Datenanalyse.",
            "target_market": "Luxussegment, Hotels, technikaffine Haushalte",
            "key_features": ["KI-gesteuerte Optimierung", "Echtzeitanalyse", "Präventive Wartung", "Personalisierte Einstellungen"]
        },
        "🔗 Connect Hub": {
            "name": "Connect Hub",
            "description": "Zentrale Steuereinheit, die alle Wasseranwendungen im Haus intelligent vernetzt. Überwacht Verbrauch, erkennt Leckagen und optimiert Wassertemperatur.",
            "value_prop": "Ein Gerät revolutioniert das gesamte Wassermanagement. Intelligente Vernetzung aller Geräte mit präventiver Wartung.",
            "target_market": "Hausmodernisierer, Smart Home Enthusiasten",
            "key_features": ["Zentrale Steuerung", "Leckage-Erkennung", "Verbrauchsoptimierung", "Smart Home Integration"]
        },
        "🌱 PureFlow System": {
            "name": "PureFlow System",
            "description": "Revolutionäres Dreifachsystem für nachhaltiges Wassermanagement mit Recycling. Filtert, reinigt und bereitet Wasser für verschiedene Anwendungen auf.",
            "value_prop": "Nachhaltigkeit ohne Verzicht. Massive Kosteneinsparungen bei reduziertem CO2-Fußabdruck.",
            "target_market": "Umweltbewusste Familien, Nachhaltigkeits-orientierte Haushalte",
            "key_features": ["Wasser-Recycling", "Dreifach-Filtersystem", "CO2-Reduktion", "Kosteneinsparung"]
        }
    }
    
    # Display products in grid
    product_cols = st.columns(2)
    products_list = list(DEFAULT_PRODUCTS.items())
    
    for i, (emoji_name, product_data) in enumerate(products_list):
        col = product_cols[i % 2]
        
        with col:
            with st.container():
                st.markdown(f"**{emoji_name}**")
                st.markdown(f"**{product_data['name']}**")
                st.markdown(f"{product_data['value_prop']}")
                st.markdown(f"_Target: {product_data['target_market']}_")
                
                if st.button(f"Select {emoji_name}", key=f"prod_select_{i}", use_container_width=True):
                    st.session_state.current_product = product_data.copy()
                    st.session_state.flow_completed[0] = True
                    st.success(f"✅ {product_data['name']} selected!")
                    st.balloons()
                    st.rerun()
    
    # Option 2: Custom Product
    st.markdown("### ✏️ Or Define Custom Product")
    
    with st.expander("🎨 Create Custom Product", expanded=False):
        with st.form("custom_product_form"):
            st.markdown("Define your own product or concept for autonomous testing:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                product_name = st.text_input("Product Name*", placeholder="e.g., zero360 SmartFlow Pro")
                product_category = st.selectbox("Category", 
                                              ["Shower System", "Faucet/Tap", "Smart Home", "Water Management", "Accessories", "Other"])
                target_market = st.text_input("Target Market*", placeholder="e.g., Premium homeowners, Hotels")
            
            with col2:
                product_description = st.text_area("Product Description*", 
                                                 placeholder="Describe what the product does, how it works, key technologies...")
                value_proposition = st.text_area("Value Proposition*", 
                                                placeholder="What's the main benefit? Why should customers choose this?")
            
            key_features = st.text_area("Key Features (one per line)", 
                                      placeholder="Feature 1\nFeature 2\nFeature 3...")
            price_range = st.selectbox("Price Range", 
                                     ["Budget (< 500€)", "Mid-range (500-2000€)", "Premium (2000-5000€)", "Luxury (> 5000€)", "Not defined"])
            
            if st.form_submit_button("🚀 Create Product", type="primary"):
                if product_name and product_description and value_proposition and target_market:
                    features_list = [f.strip() for f in key_features.split('\n') if f.strip()] if key_features else []
                    
                    custom_product = {
                        'name': product_name,
                        'category': product_category,
                        'description': product_description,
                        'value_prop': value_proposition,
                        'target_market': target_market,
                        'key_features': features_list,
                        'price_range': price_range
                    }
                    
                    st.session_state.current_product = custom_product
                    st.session_state.flow_completed[0] = True
                    st.success(f"✅ Custom product '{product_name}' created successfully!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Please fill in all required fields marked with *")
    
    # Show current selection
    if st.session_state.current_product:
        st.markdown("### ✅ Current Product")
        product = st.session_state.current_product
        
        st.success(f"🚀 **{product.get('name', 'Unnamed Product')}**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Target Market:** {product.get('target_market', 'Not defined')}")
            st.write(f"**Category:** {product.get('category', 'Not specified')}")
        with col2:
            st.write("**Value Proposition:**")
            st.write(product.get('value_prop', 'No value proposition defined')[:150] + "...")
        
        st.write("**Description:**")
        st.write(product.get('description', 'No description provided')[:200] + "...")
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col3:
            if st.button("➡️ Continue to Step 3: Generate Interviews", type="primary", use_container_width=True):
                st.session_state.current_step = 2
                st.rerun()

def render_step2_generate_interviews():
    """Step 3: Generate Autonomous Interviews"""
    st.markdown("## Step 3: Generate Autonomous Interviews 🤖")
    st.markdown("Generate and run up to 10 autonomous interviews with AI-created personas. Each interview will test your product with different user types.")
    
    # Check prerequisites
    if not st.session_state.target_demographics:
        st.error("⚠️ Please complete Step 1 first - define target demographics.")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⬅️ Back to Step 1", use_container_width=True, type="primary"):
                st.session_state.current_step = 0
                st.rerun()
        return
    
    if not st.session_state.current_product:
        st.error("⚠️ Please complete Step 2 first - define a product to test.")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⬅️ Back to Step 2", use_container_width=True, type="primary"):
                st.session_state.current_step = 1
                st.rerun()
        return
    
    product = st.session_state.current_product
    st.info(f"🚀 **Testing Product:** {product.get('name', 'Unnamed Product')}")
    
    # Interview Context Configuration
    st.markdown("### 🎯 Interview Context & Scenario")
    st.markdown("Define the interview scenario to ensure realistic and relevant conversations.")
    
    with st.expander("📋 Interview Context Settings", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Customer Relationship**")
            customer_status = st.selectbox(
                "Customer Status",
                [
                    "Potential new customer (never used product)",
                    "Interested prospect (aware of product)",
                    "Existing customer (current user)",
                    "Former customer (used to use product)",
                    "Competitor customer (uses similar products)"
                ],
                help="What is the persona's relationship to your product?"
            )
            
            product_knowledge = st.selectbox(
                "Product Knowledge Level",
                [
                    "No prior knowledge",
                    "Basic awareness",
                    "Good understanding",
                    "Expert level knowledge"
                ],
                help="How familiar is the persona with your product category?"
            )
            
            purchase_intent = st.selectbox(
                "Purchase Intent",
                [
                    "Just browsing/researching",
                    "Considering purchase soon",
                    "Ready to buy",
                    "Needs convincing",
                    "Comparing options"
                ],
                help="What is the persona's buying intention?"
            )
        
        with col2:
            st.markdown("**Interview Scenario**")
            interview_setting = st.selectbox(
                "Interview Setting",
                [
                    "Product discovery interview",
                    "User experience feedback session",
                    "Purchase decision consultation",
                    "Post-purchase satisfaction review",
                    "Competitive analysis discussion"
                ],
                help="What type of interview scenario should this be?"
            )
            
            conversation_style = st.selectbox(
                "Conversation Style",
                [
                    "Casual and exploratory",
                    "Structured and focused",
                    "Problem-solving oriented",
                    "Consultative and advisory"
                ],
                help="What tone should the interview have?"
            )
            
            specific_context = st.text_area(
                "Specific Context (Optional)",
                placeholder="e.g., 'Persona is renovating their bathroom and looking for modern solutions' or 'Recently moved and setting up new home'",
                help="Add any specific context about the persona's current situation"
            )
    
    # Store interview context in session state
    interview_context = {
        "customer_status": customer_status,
        "product_knowledge": product_knowledge,
        "purchase_intent": purchase_intent,
        "interview_setting": interview_setting,
        "conversation_style": conversation_style,
        "specific_context": specific_context
    }
    st.session_state.interview_context = interview_context
    
    # Interview Configuration
    st.markdown("### ⚙️ Interview Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        num_interviews = st.slider(
            "Number of Interviews", 
            min_value=1, 
            max_value=10, 
            value=min(5, st.session_state.max_interviews),
            help="How many autonomous interviews to generate"
        )
    
    with col2:
        questions_per_interview = st.slider(
            "Questions per Interview", 
            min_value=5, 
            max_value=15, 
            value=8,
            help="Number of questions in each interview"
        )
    
    with col3:
        interview_focus = st.selectbox(
            "Interview Focus",
            ["Balanced", "Pain Points", "Value Proposition", "Pricing", "Features", "Competition"],
            help="What aspect should the interviews focus on?"
        )
    
    # Current Status
    st.markdown("### 📊 Current Status")
    
    completed_interviews = len([i for i in st.session_state.autonomous_interviews if i['status'] == 'completed'])
    running_interviews = len([i for i in st.session_state.autonomous_interviews if i['status'] == 'running'])
    
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        st.metric("Completed", completed_interviews)
    with status_col2:
        st.metric("Running", running_interviews)
    with status_col3:
        st.metric("Remaining", max(0, num_interviews - len(st.session_state.autonomous_interviews)))
    
    # Generation Controls
    st.markdown("### 🎬 Interview Generation")
    
    # Check if we can generate more interviews
    can_generate = len(st.session_state.autonomous_interviews) < num_interviews and not st.session_state.research_active
    
    if can_generate:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Generate Single Interview", use_container_width=True):
                generate_single_interview(product, questions_per_interview, interview_focus, st.session_state.get('interview_context'))
        
        with col2:
            if st.button("🤖 Generate All Interviews", use_container_width=True, type="primary"):
                generate_all_interviews(product, num_interviews, questions_per_interview, interview_focus, st.session_state.get('interview_context'))
    else:
        if st.session_state.research_active:
            st.warning("🔄 Research is currently running...")
            if st.button("⏹️ Stop Research", use_container_width=True):
                st.session_state.research_active = False
                st.rerun()
        else:
            st.info("✅ Maximum number of interviews reached or research completed.")
    
    # Interview Results Preview
    if st.session_state.autonomous_interviews:
        st.markdown("### 📋 Interview Results Preview")
        
        for i, interview in enumerate(st.session_state.autonomous_interviews[-3:]):  # Show last 3
            with st.expander(f"Interview {interview['id']} - {interview['persona']['name']} ({interview['status']})", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Persona:** {interview['persona']['name']}")
                    st.write(f"**Job:** {interview['persona']['job']}")
                    st.write(f"**Age:** {interview['persona']['age']}")
                
                with col2:
                    if interview['status'] == 'completed':
                        metrics = interview['metrics']
                        st.write(f"**Sentiment:** {metrics['sentiment_score']:.1%}")
                        st.write(f"**Conviction:** {metrics['conviction_level']:.1%}")
                        st.write(f"**Concerns:** {len(metrics['main_concerns'])}")
                    else:
                        st.write("**Status:** In progress...")
                
                if interview['status'] == 'completed' and interview['conversation']:
                    st.write("**Sample Response:**")
                    first_response = next((msg['content'] for msg in interview['conversation'] if msg['role'] == 'assistant'), "No response yet")
                    st.write(f"_{first_response[:200]}..._")
    
    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ Back to Step 2", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
    
    with col3:
        # Only allow proceeding if we have at least one completed interview
        if completed_interviews > 0:
            if st.button("➡️ Continue to Step 4: Analyze", type="primary", use_container_width=True):
                st.session_state.current_step = 3
                st.session_state.flow_completed[1] = True
                st.rerun()
        else:
            st.button("➡️ Generate interviews first", disabled=True, use_container_width=True)

def generate_single_interview(product: Dict, num_questions: int, focus: str, interview_context: Dict = None):
    """Generate and run a single autonomous interview"""
    if not OPENAI_AVAILABLE:
        st.error("OpenAI API not available. Please check your API key configuration.")
        return
    
    st.session_state.research_active = True
    
    # Show progress
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    try:
        with status_placeholder.container():
            st.info("🤖 Generating persona...")
        
        # Use assembled persona if available, otherwise generate diverse persona
        if st.session_state.assembled_personas:
            # Select a random persona from the assembled ones
            import random
            persona = random.choice(st.session_state.assembled_personas)
        else:
            # Fallback to generating diverse persona
            persona = generate_diverse_persona()
        
        with status_placeholder.container():
            st.info(f"👤 Created persona: {persona.get('name', 'Unknown')}")
            st.info("❓ Generating interview questions...")
        
        # Generate questions with context
        questions = generate_interview_questions(persona, product, num_questions, interview_context)
        
        with status_placeholder.container():
            st.info(f"💬 Conducting interview with {len(questions)} questions...")
        
        # Set up progress tracking
        st.session_state.progress_placeholder = progress_placeholder
        
        # Conduct interview
        interview_data = conduct_autonomous_interview(persona, product, questions)
        
        # Add to session state
        st.session_state.autonomous_interviews.append(interview_data)
        st.session_state.interviews_completed += 1
        
        with status_placeholder.container():
            st.success(f"✅ Interview completed with {persona.get('name', 'Unknown')}!")
            st.balloons()
        
    except Exception as e:
        with status_placeholder.container():
            st.error(f"❌ Error generating interview: {str(e)}")
    
    finally:
        st.session_state.research_active = False
        progress_placeholder.empty()
        # Keep status for a moment, then clear
        import time
        time.sleep(2)
        status_placeholder.empty()
        st.rerun()

def generate_all_interviews(product: Dict, num_interviews: int, questions_per_interview: int, focus: str, interview_context: Dict = None):
    """Generate all remaining interviews"""
    if not OPENAI_AVAILABLE:
        st.error("OpenAI API not available. Please check your API key configuration.")
        return
    
    st.session_state.research_active = True
    
    # Calculate how many we need to generate
    current_count = len(st.session_state.autonomous_interviews)
    remaining = num_interviews - current_count
    
    # Show overall progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        for i in range(remaining):
            current_progress = i / remaining
            progress_bar.progress(current_progress, f"Generating interview {i+1}/{remaining}")
            
            with status_text.container():
                st.info(f"🤖 Generating interview {current_count + i + 1}...")
            
            # Use assembled persona if available, otherwise generate diverse persona
            if st.session_state.assembled_personas and i < len(st.session_state.assembled_personas):
                # Use specific persona from assembled list
                persona = st.session_state.assembled_personas[i]
            elif st.session_state.assembled_personas:
                # If we have more interviews than personas, cycle through them
                import random
                persona = random.choice(st.session_state.assembled_personas)
            else:
                # Fallback to generating diverse persona
                persona = generate_diverse_persona()
            
            with status_text.container():
                st.info(f"👤 Interview {current_count + i + 1}: {persona.get('name', 'Unknown')}")
            
            # Generate questions with context
            questions = generate_interview_questions(persona, product, questions_per_interview, interview_context)
            
            # Conduct interview
            interview_data = conduct_autonomous_interview(persona, product, questions)
            
            # Add to session state
            st.session_state.autonomous_interviews.append(interview_data)
            st.session_state.interviews_completed += 1
        
        # Final progress
        progress_bar.progress(1.0, f"✅ Generated {remaining} interviews successfully!")
        
        with status_text.container():
            st.success(f"🎉 All {remaining} interviews completed!")
            st.balloons()
        
    except Exception as e:
        with status_text.container():
            st.error(f"❌ Error during batch generation: {str(e)}")
    
    finally:
        st.session_state.research_active = False
        # Clean up UI elements
        import time
        time.sleep(3)
        progress_bar.empty()
        status_text.empty()
        st.rerun()

def render_step3_analyze_results():
    """Step 4: Analyze Autonomous Interview Results"""
    st.markdown("## Step 4: Analyze Interview Results 📊")
    st.markdown("Analyze and compare results from your autonomous interviews to gain comprehensive insights about your product.")
    
    # Check if we have any interviews
    if not st.session_state.autonomous_interviews:
        st.error("⚠️ No interviews found. Please complete Step 3 first.")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⬅️ Back to Step 3", use_container_width=True, type="primary"):
                st.session_state.current_step = 2
                st.rerun()
        return
    
    # Filter completed interviews
    completed_interviews = [i for i in st.session_state.autonomous_interviews if i['status'] == 'completed']
    
    if not completed_interviews:
        st.warning("⚠️ No completed interviews yet. Please wait for interviews to finish or go back to Step 3.")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⬅️ Back to Step 3", use_container_width=True, type="primary"):
                st.session_state.current_step = 2
                st.rerun()
        return
    
    # Overall Summary
    st.markdown("### 📋 Research Summary")
    
    product = st.session_state.current_product
    st.info(f"🚀 **Product Tested:** {product.get('name', 'Unnamed Product')}")
    
    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    
    with summary_col1:
        st.metric("Total Interviews", len(completed_interviews))
    with summary_col2:
        avg_sentiment = sum(i['metrics']['sentiment_score'] for i in completed_interviews) / len(completed_interviews)
        st.metric("Avg Sentiment", f"{avg_sentiment:.1%}")
    with summary_col3:
        avg_conviction = sum(i['metrics']['conviction_level'] for i in completed_interviews) / len(completed_interviews)
        st.metric("Avg Purchase Intent", f"{avg_conviction:.1%}")
    with summary_col4:
        all_concerns = []
        for i in completed_interviews:
            all_concerns.extend(i['metrics']['main_concerns'])
        unique_concerns = len(set(all_concerns))
        st.metric("Unique Concerns", unique_concerns)
    
    # Detailed Analytics
    st.markdown("### 📈 Detailed Analytics")
    
    # Create tabs for different analysis views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "👥 Personas", "💬 Conversations", "🗨️ Live Chat", "📄 Export"])
    
    with tab1:
        render_overview_analysis(completed_interviews)
    
    with tab2:
        render_persona_analysis(completed_interviews)
    
    with tab3:
        render_conversation_analysis(completed_interviews)
    
    with tab4:
        render_live_chat(completed_interviews, product)
    
    with tab5:
        render_export_analysis(completed_interviews, product)
    
    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ Back to Step 3", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()
    
    with col2:
        if st.button("🔄 Start New Research", use_container_width=True, type="primary"):
            # Reset for new research
            st.session_state.autonomous_interviews = []
            st.session_state.current_product = {}
            st.session_state.target_demographics = {}
            st.session_state.assembled_personas = []
            st.session_state.research_active = False
            st.session_state.interviews_completed = 0
            st.session_state.current_step = 0
            st.session_state.flow_completed = [False, False, False, False]
            st.rerun()
    
    with col3:
        st.session_state.flow_completed[3] = True  # Mark step 3 as completed

# Analysis Helper Functions
def render_overview_analysis(completed_interviews):
    """Render enhanced overview analysis tab with NLU insights"""
    st.markdown("#### 🎯 Key Insights")
    
    # Calculate basic insights
    sentiments = [i['metrics']['sentiment_score'] for i in completed_interviews]
    convictions = [i['metrics']['conviction_level'] for i in completed_interviews]
    
    avg_sentiment = sum(sentiments) / len(sentiments)
    avg_conviction = sum(convictions) / len(convictions)
    
    # Sentiment distribution
    positive_count = len([s for s in sentiments if s > 0.6])
    neutral_count = len([s for s in sentiments if 0.4 <= s <= 0.6])
    negative_count = len([s for s in sentiments if s < 0.4])
    
    # Collect emotions and keywords from all interviews
    all_emotions = {}
    all_keywords = []
    dominant_emotions = []
    
    for interview in completed_interviews:
        metrics = interview['metrics']
        
        # Aggregate emotions
        if 'emotions' in metrics and metrics['emotions']:
            for emotion, score in metrics['emotions'].items():
                all_emotions[emotion] = all_emotions.get(emotion, 0) + score
        
        # Collect keywords
        if 'keywords' in metrics and metrics['keywords']:
            all_keywords.extend(metrics['keywords'])
        
        # Collect dominant emotions
        if 'dominant_emotion' in metrics:
            dominant_emotions.append(metrics['dominant_emotion'])
    
    # Display basic insights
    insights = []
    if avg_sentiment > 0.7:
        insights.append("✅ **Very Positive Reception** - Strong overall sentiment across interviews")
    elif avg_sentiment < 0.3:
        insights.append("⚠️ **Negative Reception** - Significant concerns raised across interviews")
    else:
        insights.append("🤔 **Mixed Reception** - Varied opinions across different personas")
    
    if avg_conviction > 0.8:
        insights.append("🎯 **High Purchase Intent** - Strong buying signals from most personas")
    elif avg_conviction < 0.3:
        insights.append("📈 **Low Purchase Intent** - Need to strengthen value proposition")
    
    if positive_count > len(completed_interviews) * 0.7:
        insights.append("🌟 **Broad Appeal** - Product resonates with diverse audience")
    
    # Add emotion-based insights
    if all_emotions:
        top_emotion = max(all_emotions.keys(), key=lambda k: all_emotions[k])
        emotion_icons = {
            'joy': '😊', 'trust': '🤝', 'fear': '😰', 'surprise': '😮', 
            'anger': '😠', 'sadness': '😢', 'anticipation': '🎯', 'disgust': '😒'
        }
        icon = emotion_icons.get(top_emotion, '💭')
        insights.append(f"{icon} **Dominant Emotion: {top_emotion.title()}** - This emotion appears most frequently in responses")
    
    for insight in insights:
        st.markdown(f"- {insight}")
    
    # Enhanced visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 😊 Sentiment Distribution")
        sentiment_data = pd.DataFrame({
            'Sentiment': ['Positive', 'Neutral', 'Negative'],
            'Count': [positive_count, neutral_count, negative_count]
        })
        
        if not sentiment_data.empty:
            fig = px.pie(sentiment_data, values='Count', names='Sentiment', 
                        color_discrete_map={'Positive': '#22c55e', 'Neutral': '#64748b', 'Negative': '#ef4444'})
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=300, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if all_emotions:
            st.markdown("#### 💭 Emotion Analysis")
            emotion_df = pd.DataFrame(list(all_emotions.items()), columns=['Emotion', 'Score'])
            emotion_df = emotion_df.sort_values('Score', ascending=True)
            
            fig = px.bar(emotion_df, x='Score', y='Emotion', orientation='h',
                        title="Emotional Response Distribution")
            fig.update_layout(height=300, margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("#### 💭 Emotion Analysis")
            st.info("No emotion data available with current analysis")
    
    # Keywords section
    if all_keywords:
        st.markdown("#### 🔑 Key Topics & Terms")
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        top_keywords = keyword_counts.most_common(10)
        
        # Create keyword frequency chart
        if top_keywords:
            keyword_df = pd.DataFrame(top_keywords, columns=['Keyword', 'Frequency'])
            fig = px.bar(keyword_df, x='Frequency', y='Keyword', orientation='h',
                        title="Most Mentioned Keywords")
            fig.update_layout(height=400, margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
        
        # Display as tags
        st.markdown("**Top Keywords:**")
        keyword_tags = " ".join([f"`{word} ({count})`" for word, count in top_keywords[:8]])
        st.markdown(keyword_tags)
    

def render_persona_analysis(completed_interviews):
    """Render enhanced persona analysis tab with NLU insights"""
    st.markdown("#### 👥 Persona Breakdown")
    
    # Group by job/persona type
    persona_groups = {}
    for interview in completed_interviews:
        job = interview['persona']['job']
        if job not in persona_groups:
            persona_groups[job] = []
        persona_groups[job].append(interview)
    
    # Display each persona group
    for job, interviews in persona_groups.items():
        with st.expander(f"{job} ({len(interviews)} interview{'s' if len(interviews) > 1 else ''})", expanded=True):
            for interview in interviews:
                persona = interview['persona']
                metrics = interview['metrics']
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**{persona['name']}**")
                    st.write(f"Age: {persona['age']}")
                    st.write(f"Company: {persona.get('company', 'N/A')}")
                
                with col2:
                    st.write(f"**Sentiment:** {metrics['sentiment_score']:.1%}")
                    st.write(f"**Conviction:** {metrics['conviction_level']:.1%}")
                    st.write(f"**Concerns:** {len(metrics['main_concerns'])}")
                
                with col3:
                    if metrics['main_concerns']:
                        st.write("**Key Concerns:**")
                        for concern in metrics['main_concerns'][:3]:
                            st.write(f"• {concern}")
                    else:
                        st.write("**No major concerns**")
                
                # Sample quote
                if interview['conversation']:
                    first_response = next((msg['content'] for msg in interview['conversation'] if msg['role'] == 'assistant'), "")
                    if first_response:
                        st.write(f"💬 *\"{first_response[:150]}...\"*")
                
                st.markdown("---")

def render_conversation_analysis(completed_interviews):
    """Render conversation analysis tab"""
    st.markdown("#### 💬 Conversation Insights")
    
    # Select interview to view
    interview_options = [f"{i['persona']['name']} - {i['persona']['job']}" for i in completed_interviews]
    selected_idx = st.selectbox("Select Interview to View:", range(len(interview_options)), 
                               format_func=lambda x: interview_options[x])
    
    selected_interview = completed_interviews[selected_idx]
    
    # Display interview details
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 👤 Persona Details")
        persona = selected_interview['persona']
        st.write(f"**Name:** {persona['name']}")
        st.write(f"**Age:** {persona['age']}")
        st.write(f"**Job:** {persona['job']}")
        st.write(f"**Company:** {persona.get('company', 'N/A')}")
    
    with col2:
        st.markdown("##### 📊 Interview Metrics")
        metrics = selected_interview['metrics']
        st.write(f"**Sentiment:** {metrics['sentiment_score']:.1%}")
        st.write(f"**Conviction:** {metrics['conviction_level']:.1%}")
        st.write(f"**Concerns:** {len(metrics['main_concerns'])}")
    
    # Display conversation with streamlit-chat
    st.markdown("##### 💬 Full Conversation")
    
    conversation = selected_interview['conversation']
    for i, msg in enumerate(conversation):
        if msg['role'] == 'user':
            message(f"**Researcher:** {msg['content']}", is_user=True, key=f"user_{i}")
        else:
            avatar_url = get_persona_avatar_url(persona['name'], persona)
            message(f"**{persona['name']}:** {msg['content']}", is_user=False, key=f"assistant_{i}", avatar_style="no-avatar", logo=avatar_url)

def render_live_chat(completed_interviews, product):
    """Render interactive live chat with personas"""
    st.markdown("#### 🗨️ Live Chat with Personas")
    st.markdown("Have a real-time conversation with any of your generated personas to explore deeper insights.")
    
    if not completed_interviews:
        st.info("Complete some interviews first to enable live chat with personas.")
        return
    
    # Persona selection
    personas = [interview['persona'] for interview in completed_interviews]
    persona_names = [p['name'] for p in personas]
    
    selected_persona_name = st.selectbox("Choose a persona to chat with:", persona_names)
    selected_persona = next(p for p in personas if p['name'] == selected_persona_name)
    
    st.markdown(f"**Chatting with:** {selected_persona['name']}")
    st.markdown(f"*{selected_persona.get('background', 'AI-generated persona')}*")
    
    # Initialize chat history in session state
    chat_key = f"live_chat_{selected_persona['name']}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for i, msg in enumerate(st.session_state[chat_key]):
            timestamp = msg.get('timestamp', '')
            if msg['role'] == 'user':
                display_text = f"**You:** {msg['content']}"
                if timestamp:
                    display_text += f"\n*{timestamp}*"
                message(display_text, is_user=True, key=f"live_user_{i}_{chat_key}")
            else:
                display_text = f"**{selected_persona['name']}:** {msg['content']}"
                if timestamp:
                    display_text += f"\n*{timestamp}*"
                avatar_url = get_persona_avatar_url(selected_persona['name'], selected_persona)
                message(display_text, is_user=False, key=f"live_assistant_{i}_{chat_key}", 
                       avatar_style="no-avatar", logo=avatar_url)
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message to chat history with timestamp
        current_time = datetime.now().strftime('%H:%M')
        st.session_state[chat_key].append({
            'role': 'user', 
            'content': user_input,
            'timestamp': current_time
        })
        
        # Generate AI response
        try:
            response = get_openai_response(user_input, selected_persona, product)
            st.session_state[chat_key].append({
                'role': 'assistant', 
                'content': response,
                'timestamp': datetime.now().strftime('%H:%M')
            })
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            st.session_state[chat_key].append({
                'role': 'assistant', 
                'content': "I'm sorry, I'm having trouble responding right now. Please try again.",
                'timestamp': datetime.now().strftime('%H:%M')
            })
        
        # Rerun to update the chat display
        st.rerun()
    
    # Chat controls
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state[chat_key] = []
            st.rerun()
    
    with col2:
        if st.button("💾 Save Chat", use_container_width=True):
            if st.session_state[chat_key]:
                # Create a downloadable chat log
                chat_log = {
                    'persona': selected_persona,
                    'product': product,
                    'conversation': st.session_state[chat_key],
                    'timestamp': datetime.now().isoformat()
                }
                
                chat_json = json.dumps(chat_log, indent=2)
                st.download_button(
                    label="📥 Download Chat Log",
                    data=chat_json,
                    file_name=f"chat_log_{selected_persona['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )

def render_export_analysis(completed_interviews, product):
    """Render export analysis tab"""
    st.markdown("#### 📄 Export Research Results")
    st.markdown("Download your autonomous research results in various formats:")
    
    # Prepare comprehensive export data
    export_data = {
        'research_session': {
            'timestamp': datetime.now().isoformat(),
            'product': product,
            'total_interviews': len(completed_interviews)
        },
        'summary_metrics': {
            'avg_sentiment': sum(i['metrics']['sentiment_score'] for i in completed_interviews) / len(completed_interviews),
            'avg_conviction': sum(i['metrics']['conviction_level'] for i in completed_interviews) / len(completed_interviews),
            'sentiment_distribution': {
                'positive': len([i for i in completed_interviews if i['metrics']['sentiment_score'] > 0.6]),
                'neutral': len([i for i in completed_interviews if 0.4 <= i['metrics']['sentiment_score'] <= 0.6]),
                'negative': len([i for i in completed_interviews if i['metrics']['sentiment_score'] < 0.4])
            }
        },
        'interviews': [
            {
                'id': interview['id'],
                'persona': interview['persona'],
                'metrics': interview['metrics'],
                'conversation': [
                    {
                        'role': msg['role'],
                        'content': msg['content'],
                        'timestamp': msg['timestamp'].isoformat()
                    } for msg in interview['conversation']
                ]
            } for interview in completed_interviews
        ]
    }
    
    export_col1, export_col2, export_col3 = st.columns(3)
    
    with export_col1:
        # JSON Export
        json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
        st.download_button(
            label="📄 Export Full Data (JSON)",
            data=json_data,
            file_name=f"autonomous_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with export_col2:
        # CSV Export (Summary)
        summary_data = []
        for interview in completed_interviews:
            summary_data.append({
                'Interview_ID': interview['id'],
                'Persona_Name': interview['persona']['name'],
                'Persona_Job': interview['persona']['job'],
                'Persona_Age': interview['persona']['age'],
                'Sentiment_Score': interview['metrics']['sentiment_score'],
                'Conviction_Level': interview['metrics']['conviction_level'],
                'Concerns_Count': len(interview['metrics']['main_concerns']),
                'Main_Concerns': '; '.join(interview['metrics']['main_concerns'])
            })
        
        df = pd.DataFrame(summary_data)
        csv_string = df.to_csv(index=False)
        
        st.download_button(
            label="📊 Export Summary (CSV)",
            data=csv_string,
            file_name=f"research_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with export_col3:
        # Report Export
        avg_sentiment = export_data['summary_metrics']['avg_sentiment']
        avg_conviction = export_data['summary_metrics']['avg_conviction']
        
        report = f"""
# Autonomous User Research Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Product Tested
**Name:** {product.get('name', 'Unknown')}
**Description:** {product.get('description', 'No description')}
**Target Market:** {product.get('target_market', 'Not specified')}

## Research Summary
- **Total Interviews:** {len(completed_interviews)}
- **Average Sentiment:** {avg_sentiment:.1%}
- **Average Purchase Intent:** {avg_conviction:.1%}

## Key Findings
### Sentiment Distribution
- Positive: {export_data['summary_metrics']['sentiment_distribution']['positive']} interviews
- Neutral: {export_data['summary_metrics']['sentiment_distribution']['neutral']} interviews  
- Negative: {export_data['summary_metrics']['sentiment_distribution']['negative']} interviews

### Recommendations
{"1. Leverage positive sentiment in marketing materials" if avg_sentiment > 0.6 else "1. Address negative feedback before market launch"}
{"2. Focus on conversion optimization" if avg_conviction > 0.7 else "2. Strengthen value proposition"}
3. Consider feedback from diverse persona types

## Interview Details
"""
        
        for interview in completed_interviews:
            report += f"""
### {interview['persona']['name']} - {interview['persona']['job']}
- **Sentiment:** {interview['metrics']['sentiment_score']:.1%}
- **Purchase Intent:** {interview['metrics']['conviction_level']:.1%}
- **Key Concerns:** {', '.join(interview['metrics']['main_concerns']) if interview['metrics']['main_concerns'] else 'None'}
"""
        
        st.download_button(
            label="📋 Export Report (MD)",
            data=report,
            file_name=f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )

# Removed old step 4 function and analytics column - now using autonomous research analysis

# Main Application with Step-based Flow
def main():
    # Initialize session state
    initialize_session_state()
    
    # Render navigation bar
    render_nav_bar()
    
    # Render sidebar stats
    render_sidebar_stats()
    
    # Main content area - full width for step-based flow
    st.markdown('<div class="main-content-area">', unsafe_allow_html=True)
    render_main_content()
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
import streamlit as st
import base64
from PIL import Image
import io
import os

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(page_title="AI Scalp Trader", layout="wide")

st.title("📈 AI Scalp Trading Assistant")
st.markdown("Upload a chart screenshot to get instant analysis, Stop Loss, and Take Profit suggestions.")

# Sidebar for settings
with st.sidebar:
    st.header("Settings")
    api_provider = st.selectbox("Select AI Provider", ["OpenAI", "Anthropic", "Google Gemini"])
    
    # Auto-fill key if present in env
    default_key = ""
    if api_provider == "OpenAI":
        default_key = os.getenv("OPENAI_API_KEY", "")
    elif api_provider == "Anthropic":
        default_key = os.getenv("ANTHROPIC_API_KEY", "")
    elif api_provider == "Google Gemini":
        default_key = os.getenv("GOOGLE_API_KEY", "")
    
    api_key = st.text_input(f"Enter {api_provider} API Key", value=default_key, type="password")
    
    st.divider()
    st.markdown("### How to get a key?")
    if api_provider == "OpenAI":
        st.markdown("[Get OpenAI Key](https://platform.openai.com/api-keys)")
    elif api_provider == "Anthropic":
        st.markdown("[Get Claude Key](https://console.anthropic.com/)")
    elif api_provider == "Google Gemini":
        st.markdown("[Get Gemini Key](https://aistudio.google.com/app/apikey)")

# Main content
col1, col2 = st.columns([1, 1])

uploaded_file = None

with col1:
    st.subheader("1. Upload Chart")
    uploaded_file = st.file_uploader("Choose an image...", type=['png', 'jpg', 'jpeg'])
    
    timeframe = st.selectbox("Select Timeframe", ["1m", "5m", "15m", "1h", "4h", "Daily"])
    
    user_context = st.text_area("Additional Context (Optional)", 
                                placeholder="E.g., 'Looking for a LONG on the 5m timeframe, price just tapped a demand zone.'")

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Chart', use_column_width=True)

with col2:
    st.subheader("2. AI Analysis")
    
    analyze_btn = st.button("Analyze Chart", type="primary", disabled=(not uploaded_file or not api_key))
    
    if not api_key:
        st.warning("Please enter your API Key in the sidebar to proceed.")
    
    if analyze_btn and uploaded_file and api_key:
        with st.spinner("Analyzing market structure..."):
            try:
                from utils import analyze_chart_openai, analyze_chart_anthropic, analyze_chart_gemini
                image = Image.open(uploaded_file)
                
                analysis_result = ""
                
                if api_provider == "OpenAI":
                    analysis_result = analyze_chart_openai(api_key, image, f"Timeframe: {timeframe}. {user_context}")
                elif api_provider == "Anthropic":
                    analysis_result = analyze_chart_anthropic(api_key, image, f"Timeframe: {timeframe}. {user_context}")
                elif api_provider == "Google Gemini":
                    analysis_result = analyze_chart_gemini(api_key, image, f"Timeframe: {timeframe}. {user_context}")
                
                st.success("Analysis Complete!")
                st.markdown(analysis_result)
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

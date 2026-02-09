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
    
    st.markdown("### 🧠 Personalization")
    my_rules = st.text_area("My Trading Rules / Edge", 
                           placeholder="- Only take trades with 2:1 RR\n- Avoid trading during news\n- I prefer break and retest setups",
                           height=100)
    
    st.divider()
    st.markdown("### 💰 Risk Management")
    risk_pct = st.slider("Risk per Trade (%)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    account_size = st.number_input("Account Size ($)", min_value=10, value=100, step=10)
    
    st.divider()
    st.markdown("### How to get a key?")
    if api_provider == "OpenAI":
        st.markdown("[Get OpenAI Key](https://platform.openai.com/api-keys)")
    elif api_provider == "Anthropic":
        st.markdown("[Get Claude Key](https://console.anthropic.com/)")
    elif api_provider == "Google Gemini":
        st.markdown("[Get Gemini Key](https://aistudio.google.com/app/apikey)")

# Main content
tab1, tab2 = st.tabs(["🚀 Analyze Market", "🧠 Review Trade (Self-Learning)"])

with tab1:
    col1, col2 = st.columns([1, 1])

    uploaded_file = None

    with col1:
        st.subheader("1. Upload Chart")
        uploaded_file = st.file_uploader("Choose an image...", type=['png', 'jpg', 'jpeg'], key="analyze_upload")
        
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
                    
                    # Load knowledge base
                    knowledge_base = ""
                    if os.path.exists("knowledge.txt"):
                        with open("knowledge.txt", "r") as f:
                            knowledge_base = f.read()
                    
                    # Combine context
                    risk_context = f"Account Size: ${account_size}. Risk Per Trade: {risk_pct}%. STRICT RULE: Minimum Risk:Reward Ratio of 1:2."
                    full_system_context = f"Timeframe: {timeframe}. Risk Params: {risk_context}. User Rules: {my_rules}. Past Lessons (Knowledge Base): {knowledge_base}. Context: {user_context}"
                    
                    analysis_result = ""
                    
                    if api_provider == "OpenAI":
                        analysis_result = analyze_chart_openai(api_key, image, full_system_context)
                    elif api_provider == "Anthropic":
                        analysis_result = analyze_chart_anthropic(api_key, image, full_system_context)
                    elif api_provider == "Google Gemini":
                        analysis_result = analyze_chart_gemini(api_key, image, full_system_context)
                    
                    st.success("Analysis Complete!")
                    st.markdown(analysis_result)
                    
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

with tab2:
    st.header("Trade Post-Mortem 💀")
    st.markdown("Upload a screenshot of a **finished trade** (Win or Loss). The AI will analyze it and suggest a new rule to learn.")
    
    review_file = st.file_uploader("Upload Completed Trade", type=['png', 'jpg', 'jpeg'], key="review_upload")
    outcome = st.radio("What was the outcome?", ["WIN", "LOSS"], horizontal=True)
    notes = st.text_area("What happened? (Optional)", placeholder="e.g., I entered late and got stopped out.")
    
    if st.button("Analyze Outcome"):
        if review_file and api_key:
             with st.spinner("AI is reviewing your trade..."):
                from utils import analyze_trade_outcome
                review_image = Image.open(review_file)
                review_result = analyze_trade_outcome(api_key, review_image, outcome, notes)
                
                st.markdown(review_result)
                
                # Rule extraction logic (simplified for now, allow user to save manually)
                st.info("💡 Copy the 'New Rule' above and paste it into your 'knowledge.txt' file or formatted sidebar rules to make it permanent.")
                
                # Option to append directly to file
                new_rule = st.text_input("Refine the rule to save:", placeholder="Paste the suggested rule here")
                if st.button("Save Rule to Knowledge Base"):
                    with open("knowledge.txt", "a") as f:
                        f.write(f"\n- {new_rule}")
                    st.success("Rule Saved! The AI will remember this next time.")

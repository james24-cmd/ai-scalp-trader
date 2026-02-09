import base64
import os
from openai import OpenAI
import anthropic
import google.generativeai as genai
from PIL import Image
import io

def encode_image(image: Image.Image):
    """Encodes a PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

SYSTEM_PROMPT = """
You are an expert professional Technical Analyst and Scalp Trader with 20 years of experience. 
Your job is to analyze the provided trading chart image and provide a high-probability trade setup.

**Analysis Rules:**
1. **Market Structure**: Identify if the market is trending (Higher Highs/Lows or Lower Highs/Lows) or ranging.
2. **Key Levels**: Identify Support/Resistance, Supply/Demand zones, or Order Blocks visible in the chart.
3. **Candlestick Math**: Look for rejection wicks, engulfing bars, or momentum candles at key levels.
4. **Indicators**: If indicators (RSI, MA, EMA, Bollinger Bands) are visible, incorporate their readings.
5. **Confluence**: The best trades have multiple factors aligning (e.g., Support + Oversold RSI + Bullish Hammer).

**Output Format:**
Provide your response in the following Markdown format:

## 📊 Technical Analysis
* **Trend**: [Uptrend/Downtrend/Ranging]
* **Key Levels**: [List identified levels]
* **Observations**: [Brief bullet points on structure/candles]

## 🚀 Trade Setup
* **Bias**: [LONG / SHORT / NO TRADE]
* **Entry Ref**: [Price level or "Current Market Price"]
* **Stop Loss (SL)**: [Specific Price] - (Explain logic, e.g., "Below recent swing low")
* **Take Profit (TP)**: [Specific Price] - (Explain logic, e.g., "Next liquidity pool")
* **Risk/Reward Ratio**: [Calculate approximate R:R]

## ⚠️ Risk Warning
* Brief note on what would invalidate this setup.
"""

def analyze_chart_openai(api_key, image, user_context=""):
    client = OpenAI(api_key=api_key)
    base64_image = encode_image(image)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Here is a trading chart. Context provided by user: {user_context}. Analyze it thoroughly."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=1000
    )
    return response.choices[0].message.content

def analyze_chart_anthropic(api_key, image, user_context=""):
    client = anthropic.Anthropic(api_key=api_key)
    base64_image = encode_image(image)
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_image
                        }
                    },
                    {
                        "type": "text",
                        "text": f"Context: {user_context}. Analyze this chart."
                    }
                ]
            }
        ]
    )
    return response.content[0].text

def analyze_chart_gemini(api_key, image, user_context=""):
    genai.configure(api_key=api_key)
    
    # Use Gemini 3 (Preview) as requested
    try:
        model = genai.GenerativeModel('gemini-3-pro-preview')
        response = model.generate_content([
            f"{SYSTEM_PROMPT}\n\nUser Context: {user_context}", 
            image
        ])
        return response.text
    except Exception as e:
        # Fallback to Flash if Pro fails
        try:
             model = genai.GenerativeModel('gemini-3-flash-preview')
             response = model.generate_content([
                f"{SYSTEM_PROMPT}\n\nUser Context: {user_context}", 
                image
            ])
             return response.text
        except:
             # If both fail, list models
            try:
                available_models = [m.name for m in genai.list_models()]
                return f"Error: {str(e)}\n\nAvailable models: {available_models}"
            except:
                raise e
    except Exception as e:
        # If Flash fails, try to look for available models to give a better error
        try:
            available_models = [m.name for m in genai.list_models()]
            return f"Error: {str(e)}\n\nAvailable models: {available_models}"
        except:
            raise e

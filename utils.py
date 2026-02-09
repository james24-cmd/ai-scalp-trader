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
You are an expert professional Technical Analyst and Scalp Trader specializing in **Smart Money Concepts (SMC)** and Price Action.
Your job is to analyze the provided trading chart image and provide a high-probability trade setup based on institutional trading behavior.

**Analysis Rules (SMC Focus):**
1.  **Market Structure**: Identify **Break of Structure (BOS)** and **Change of Character (CHoCH)**. determining the current trend direction.
2.  **Liquidity**: Identify **Liquidity Sweeps** (Buy-side/Sell-side Liquidity) where stop losses might be hunting.
3.  **Inefficiencies**: Spot **Fair Value Gaps (FVG)** or Imbalances that price is likely to fill.
4.  **Order Blocks (OB)**: Identify valid Order Blocks or POI (Points of Interest) where institutional orders are pending.
5.  **Entry Trigger**: Look for lower timeframe confirmations (e.g., CHoCH inside a higher timeframe OB).

**Output Format (Concise & Actionable):**
Provide the analysis in this exact summary format:

## 🚨 TRADE SIGNAL: [LONG / SHORT / NO TRADE]

### 📉 Trade Setup (Immediate)
*   **Entry**: [Price]
*   **Stop Loss**: [Price] ❌
*   **Take Profit**: [Price] ✅

### ⏳ Limit Order Setup (Best Price)
*   **Entry Type**: [Buy Limit / Sell Limit] at [Price] (e.g., "Wait for retest of OB")
*   **Stop Loss**: [Price]
*   **Take Profit**: [Price]
*   **Reason**: [Why wait? e.g., "Better R:R at the 15m FVG"]

### 💰 Risk Management (Strict)
*   **Stop Loss Distance**: [Pips/Points]
*   **Risk Amount**: [Calculate $ amount based on user's Account Size & Risk %]
*   **Recommended Lot Size**: [Calculate exact lots] (Formula: Risk Amount / (SL Distance * Pip Value))
*   **Risk:Reward**: [Must be > 1:2. If not, mark as NO TRADE]

### 🧠 SMC Reasoning (Brief)
*   [One sentence on why: e.g., "Retest of 15m Order Block + Liquidity Sweep"]
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

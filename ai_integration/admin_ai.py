# backend/ai_integration/admin_ai.py
import os
import google.generativeai as genai
import json
import dotenv
dotenv.load_dotenv()

def get_admin_recommendations(financial_data: dict) -> str:
    """
    Analyzes financial and business data for strategic recommendations.
    
    Parameters:
      - financial_data: A dictionary containing revenue metrics, costs, profit trends, etc.
    
    Returns:
      - A text output from Gemini offering revenue insights, growth opportunities, and suggestions for succession planning.
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise Exception("GEMINI_API_KEY environment variable not set.")
    
    # Convert the financial data dict to a nicely formatted JSON string.
    data_str = json.dumps(financial_data, indent=2)
    prompt = (
        "Analyze the following financial and business data and provide actionable insights regarding revenue growth, "
        "profit optimization, and succession planning strategies:\n\n" + data_str
    )
    
    system_instruction = (
        "You are an AI financial advisor with deep knowledge of business analytics. "
        "Offer clear insights and recommendations based on the provided data."
    )
    
    # Configure the Gemini API
    genai.configure(api_key=gemini_api_key)
    
    # Set up the model with generation configuration
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config={
            "max_output_tokens": 600,
            "temperature": 0.2,
        },
        system_instruction=system_instruction
    )
    
    # Generate the response
    response = model.generate_content(prompt)
    return response.text

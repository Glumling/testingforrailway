# backend/ai_integration/customer_support.py
import os
import google.generativeai as genai
from google.generativeai import types
import dotenv
from typing import List  # <-- Add this import
dotenv.load_dotenv()

def get_support_response(conversation_history: List[str]) -> str:  # <-- Change here
    """
    Generates a multi-turn, context-rich support response from Gemini.
    
    Parameters:
      - conversation_history: A list of message strings (alternating between customer and support).
    
    Returns:
      - A generated response that addresses the customer's issue comprehensively.
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise Exception("GEMINI_API_KEY environment variable not set.")
    
    # Concatenate the conversation history.
    prompt = "\n".join(conversation_history) + "\nAssistant:"
    
    system_instruction = (
        "You are an experienced customer support agent handling complex queries. "
        "Provide a helpful, context-aware response that addresses the customer's situation."
    )
    
    client = genai.Client(api_key=gemini_api_key)
    config = types.GenerateContentConfig(
        max_output_tokens=600,
        temperature=0.2,
        system_instruction=system_instruction
    )
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt],
        config=config
    )
    return response.text

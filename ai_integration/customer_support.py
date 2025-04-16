# backend/ai_integration/customer_support.py
import os
import google.generativeai as genai
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

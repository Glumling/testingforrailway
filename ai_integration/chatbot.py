# backend/ai_integration/chatbot.py
import os
import google.generativeai as genai
import dotenv
from typing import List, Optional
dotenv.load_dotenv()

def get_chat_response(message: str, conversation_history: List[str] = None) -> str:
    """
    Generates a text response using the Gemini API.
    
    Parameters:
      - message: The text prompt to send to Gemini.
      - conversation_history: (Optional) A list of previous messages to provide context.
    
    Returns:
      - A text response from the AI.
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise Exception("GEMINI_API_KEY environment variable not set.")
    
    # Build the conversation context (if any)
    context = ""
    if conversation_history:
        context = "\n".join(conversation_history) + "\n"
    
    # Combine context and current message
    prompt_message = context + "User: " + message + "\nAI:"
    
    # Configure the Gemini API
    genai.configure(api_key=gemini_api_key)
    
    # Set up the model with generation configuration
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config={
            "max_output_tokens": 600,
            "temperature": 0.2,
        }
    )
    
    # Generate the response
    response = model.generate_content(prompt_message)
    return response.text

def get_streaming_response(message: str, conversation_history: Optional[List[str]] = None):
    """
    Generates a streaming response using the Gemini API.
    
    Parameters:
      - message: The text prompt to send to Gemini.
      - conversation_history: (Optional) A list of previous messages to provide context.
    
    Returns:
      - A generator that yields parts of the response as they become available.
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise Exception("GEMINI_API_KEY environment variable not set.")
    
    # Build the conversation context (if any)
    context = ""
    if conversation_history:
        context = "\n".join(conversation_history) + "\n"
    
    # Combine context and current message
    prompt_message = context + "User: " + message + "\nAI:"
    
    # Configure the Gemini API
    genai.configure(api_key=gemini_api_key)
    
    # Set up the model with generation configuration
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config={
            "max_output_tokens": 600,
            "temperature": 0.2,
        }
    )
    
    # Generate the streaming response
    response = model.generate_content(prompt_message, stream=True)
    for chunk in response:
        if chunk.text:
            yield chunk.text

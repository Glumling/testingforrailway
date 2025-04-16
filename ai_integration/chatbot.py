# backend/ai_integration/chatbot.py
import os
import google.generativeai as genai
from google.generativeai import types
import dotenv
dotenv.load_dotenv()

def get_chat_response(message: str, system_instruction: str = None) -> str:
    """
    Uses the Gemini API to generate a text response for a given message.
    
    Make sure you have set the GEMINI_API_KEY environment variable to your Gemini API key.
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise Exception("GEMINI_API_KEY environment variable not set.")

    client = genai.Client(api_key=gemini_api_key)
    
    # Configure generation parameters; adjust values as needed.
    config = types.GenerateContentConfig(
        max_output_tokens=500,
        temperature=0.1,
        system_instruction=system_instruction  # Optional: System instructions to steer behavior.
    )
    
    # Generate text output from the Gemini API.
    response = client.models.generate_content(
        model="gemini-2.0-flash",  # You can change this to whichever Gemini model is appropriate.
        contents=[message],
        config=config
    )
    
    return response.text

# Optional: If you want to support streaming responses, you can add a similar function:
def get_chat_response_stream(message: str, system_instruction: str = None) -> str:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise Exception("GEMINI_API_KEY environment variable not set.")

    client = genai.Client(api_key=gemini_api_key)
    config = types.GenerateContentConfig(
        max_output_tokens=500,
        temperature=0.1,
        system_instruction=system_instruction
    )
    
    response_stream = client.models.generate_content_stream(
        model="gemini-2.0-flash",
        contents=[message],
        config=config
    )
    
    # Concatenate all streamed chunks.
    result_text = ""
    for chunk in response_stream:
        result_text += chunk.text
    return result_text

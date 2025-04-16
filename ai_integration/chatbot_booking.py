# backend/ai_integration/chatbot_booking.py
import os
import google.generativeai as genai
import dotenv
from typing import List  # <-- Already present, just ensure it's there
dotenv.load_dotenv()

def booking_chat_response(message: str, conversation_history: List[str] = None) -> str:  # <-- Already correct
    """
    Uses Gemini to generate a booking-directed response.
    
    Parameters:
      - message: The latest user query.
      - conversation_history: (Optional) A list of previous messages to provide context.
    
    Returns:
      - A text response which guides the customer toward booking a mechanic.
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise Exception("GEMINI_API_KEY environment variable not set.")
    
    # Build the conversation context (if any)
    context = ""
    if conversation_history:
        context = "\n".join(conversation_history) + "\n"
    
    # Set up a system instruction that steers the conversation toward booking.
    system_instruction = (
        "You are an assistant specialized in helping customers book a mechanic. "
        "Answer the customer's question concisely and then ask if they would like to schedule an appointment. "
        "If additional booking details (like time, location, specialty) are needed, prompt accordingly."
    )
    
    # Combine context and current message.
    prompt_message = context + "Customer: " + message + "\nAssistant:"
    
    # Configure the Gemini API
    genai.configure(api_key=gemini_api_key)
    
    # Set up the model with generation configuration
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config={
            "max_output_tokens": 500,
            "temperature": 0.15,
        },
        system_instruction=system_instruction
    )
    
    # Generate the response
    response = model.generate_content(prompt_message)
    return response.text

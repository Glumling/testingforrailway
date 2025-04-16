# backend/ai_integration/repair_assistant.py
import os
import google.generativeai as genai
from google.generativeai import types
import base64
from io import BytesIO
import PIL.Image
import dotenv
dotenv.load_dotenv()

def get_repair_advice(mechanic_id: str, query: str, image_data: str = None) -> str:
    """
    Generates technical advice for vehicle repairs using Gemini.
    
    Parameters:
      - mechanic_id: The ID of the mechanic requesting advice
      - query: The repair question or issue description
      - image_data: Optional base64-encoded image data showing the part or issue
    
    Returns:
      - A string containing the technical advice
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise Exception("GEMINI_API_KEY environment variable not set.")
    
    client = genai.Client(api_key=gemini_api_key)
    
    # Set a specialized system instruction for automotive repair assistance
    system_instruction = """
    You are an expert automotive technician with decades of experience diagnosing and repairing all types of vehicles.
    Provide detailed, step-by-step technical advice for mechanics facing issues with vehicles.
    
    Your responses should be:
    1. Accurate - based on industry best practices and technical service procedures
    2. Practical - include specific diagnostic steps, tools needed, and repair procedures
    3. Safety-focused - always mention safety precautions when relevant
    4. Educational - explain why problems occur and how repairs resolve the root issue
    
    Use automotive terminology appropriate for professional mechanics. If the information provided is
    insufficient for a definitive diagnosis, ask for specific symptoms, codes, or test results.
    """
    
    # Check if an image was provided
    if image_data:
        try:
            # Decode the base64 image
            image_bytes = base64.b64decode(image_data.split(',')[1] if ',' in image_data else image_data)
            image = PIL.Image.open(BytesIO(image_bytes))
            
            # For multimodal input (text + image), use a model that supports it
            prompt = f"I need help with this automotive repair issue: {query}"
            
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",  # Using a model with multimodal capabilities
                contents=[prompt, image],
                generation_config=types.GenerateContentConfig(
                    max_output_tokens=800,
                    temperature=0.2,
                    system_instruction=system_instruction
                )
            )
        except Exception as e:
            print(f"Error processing image: {e}")
            # Fall back to text-only if image processing fails
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[f"I need help with this automotive repair issue: {query}"],
                generation_config=types.GenerateContentConfig(
                    max_output_tokens=800,
                    temperature=0.2,
                    system_instruction=system_instruction
                )
            )
    else:
        # Text-only query
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[f"I need help with this automotive repair issue: {query}"],
            generation_config=types.GenerateContentConfig(
                max_output_tokens=800,
                temperature=0.2,
                system_instruction=system_instruction
            )
        )
    
    return response.text 
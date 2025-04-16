# backend/ai_integration/google_ai.py
import os
from io import BytesIO
import PIL.Image
import google.generativeai as genai
from google.generativeai import types
import dotenv
dotenv.load_dotenv()

def analyze_image(file_content: bytes, action: str = "caption") -> str:
    """
    Uses the Gemini API to analyze the image.
    
    Parameters:
      - file_content: Image file bytes uploaded by the client.
      - action: Type of analysis. Supported values:
          "caption" - Returns a caption and description of the image.
          "bbox"    - Returns bounding box coordinates for detected objects.
          
    Returns:
      - The text output from the Gemini API.
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise Exception("GEMINI_API_KEY environment variable is not set.")

    client = genai.Client(api_key=gemini_api_key)
    
    # Use the file content to open an image using Pillow.
    image = PIL.Image.open(BytesIO(file_content))
    
    # Set the prompt and the model based on the action.
    if action == "caption":
        prompt = "Provide a caption and a detailed description of this image."
        # Use a model that supports multimodal input (e.g., gemini-2.0-flash-exp)
        model_name = "gemini-2.0-flash-exp"
    elif action == "bbox":
        prompt = ("Return a bounding box for each of the objects in this image "
                  "in [ymin, xmin, ymax, xmax] format with values normalized to a 1000x1000 scale.")
        # Use a model known for object localization. You may adjust this to your needs.
        model_name = "gemini-1.5-pro"
    else:
        # Default to caption if an unsupported action is provided.
        prompt = "Provide a caption and a detailed description of this image."
        model_name = "gemini-2.0-flash-exp"

    response = client.models.generate_content(
        model=model_name,
        contents=[image, prompt]
    )
    
    return response.text

# backend/ai_integration/mechanic_ai.py
import os
from supabase import create_client, Client
import json
import google.generativeai as genai
from google.generativeai import types
import dotenv
dotenv.load_dotenv()

# Initialize Supabase client (ensure these env variables are set)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase credentials not set.")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_mechanic_data(mechanic_id: str) -> dict:
    """
    Retrieves mechanic data from the Supabase database.
    """
    try:
        # First try mechanic_profiles table
        response = supabase.table("mechanic_profiles").select("*").eq("user_id", mechanic_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        
        # If not found, try mechanics table as fallback
        response = supabase.table("mechanics").select("*").eq("id", mechanic_id).execute()
        if not response.data or len(response.data) == 0:
            # Return a default profile for demo purposes
            return {
                "id": mechanic_id,
                "years_experience": 5,
                "hourly_rate": 75,
                "specialties": ["Engine Repair", "Brake Service"],
                "bio": "Experienced mechanic",
                "current_latitude": 37.7749,
                "current_longitude": -122.4194,
                "performance_metrics": {
                    "avg_rating": 4.7,
                    "completed_jobs": 124,
                    "response_time_min": 28
                }
            }
        return response.data[0]
    except Exception as e:
        print(f"Error retrieving mechanic data: {e}")
        # Return default data for testing
        return {
            "id": mechanic_id,
            "years_experience": 5,
            "hourly_rate": 75,
            "specialties": ["Engine Repair", "Brake Service"],
            "bio": "Experienced mechanic",
            "performance_metrics": {
                "avg_rating": 4.7,
                "completed_jobs": 124,
                "response_time_min": 28
            }
        }

def get_mechanic_recommendations(mechanic_id: str, message: str = "") -> str:
    """
    Generates personalized job recommendations and performance improvement ideas for a given mechanic.
    
    Parameters:
      - mechanic_id: The ID of the mechanic to generate recommendations for
      - message: Optional question or topic from the mechanic to focus the recommendations
    
    Returns:
      - A string containing the AI-generated recommendations
    """
    # Get mechanic data from database
    mechanic = get_mechanic_data(mechanic_id)
    
    # Extract relevant information
    specialties = mechanic.get("specialties", ["General Repair"])
    if isinstance(specialties, list):
        specialties_text = ", ".join(specialties)
    else:
        specialties_text = str(specialties)
        
    experience = mechanic.get("years_experience", 1)
    hourly_rate = mechanic.get("hourly_rate", 50)
    bio = mechanic.get("bio", "")
    
    # Get performance metrics if available
    performance = mechanic.get("performance_metrics", {})
    if not performance:
        performance = {
            "avg_rating": 4.5,
            "completed_jobs": 100,
            "response_time_min": 30
        }
    
    # Get location if available
    lat = mechanic.get("current_latitude")
    lng = mechanic.get("current_longitude")
    location_text = f"Location coordinates: {lat}, {lng}" if lat and lng else "Location not provided"
    
    # Format mechanic data for the prompt
    mechanic_data = f"""
Mechanic Profile:
- Experience: {experience} years
- Hourly Rate: ${hourly_rate}
- Specialties: {specialties_text}
- Bio: {bio}
- Average Rating: {performance.get('avg_rating', 4.5)}
- Completed Jobs: {performance.get('completed_jobs', 100)}
- Average Response Time: {performance.get('response_time_min', 30)} minutes
- {location_text}
"""

    # Determine if this is a general recommendation or a specific question
    if not message or message.strip() == "":
        prompt = f"""
{mechanic_data}

Based on this mechanic's profile, provide personalized business growth recommendations. 
Include advice on:
1. Pricing strategy (should they adjust their hourly rate?)
2. Skills to develop based on market demand
3. Service expansion opportunities
4. Customer acquisition strategies

Keep your response concise, practical and data-driven.
"""
    else:
        prompt = f"""
{mechanic_data}

The mechanic has asked: "{message}"

Based on their profile data and this question, provide a helpful, personalized response.
Focus on practical, actionable advice that addresses their specific question.
If the question isn't related to their business, gently redirect to business topics.

Keep your response concise, practical and data-driven.
"""
    
    # System instruction to guide the AI
    system_instruction = """
You are an AI business advisor for automotive mechanics. Your job is to help mechanics grow their business,
increase revenue, and improve customer satisfaction. Provide thoughtful, data-driven recommendations
based on the mechanic's profile, specialties, experience, and location.

Keep your responses concise, practical, and actionable. Use a friendly, professional tone.
"""
    
    # Call Gemini API
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise Exception("GEMINI_API_KEY environment variable not set.")
    
    client = genai.Client(api_key=gemini_api_key)
    config = types.GenerateContentConfig(
        max_output_tokens=600,
        temperature=0.2,
        system_instruction=system_instruction
    )
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt],
            config=config
        )
        return response.text
    except Exception as e:
        print(f"Error generating AI response: {e}")
        return "I'm sorry, I encountered an issue generating recommendations. Please try again later."

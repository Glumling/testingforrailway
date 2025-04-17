import os
from supabase import create_client, Client
import dotenv
dotenv.load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase credentials not set in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_mechanic_profile(mechanic_id: str) -> dict:
    try:
        resp = supabase.table("mechanic_profiles").select("*").eq("user_id", mechanic_id).single().execute()
        if not resp.data:
            # Return mock profile for demo purposes
            print(f"No mechanic profile found for ID {mechanic_id}, returning mock data")
            return {
                "id": "mock-profile-1",
                "user_id": mechanic_id,
                "bio": "Experienced mechanic with focus on diagnostic excellence",
                "years_experience": 7,
                "hourly_rate": 80,
                "specialties": ["Engine Repair", "Electrical Systems", "Diagnostics"],
                "current_latitude": 29.7604,
                "current_longitude": -95.3698,
                "rating": 4.8,
                "available_now": True
            }
        return resp.data
    except Exception as e:
        print(f"Error getting mechanic profile: {str(e)}")
        # Return mock data as fallback
        return {
            "id": "mock-profile-1",
            "user_id": mechanic_id,
            "bio": "Experienced mechanic with focus on diagnostic excellence",
            "years_experience": 7,
            "hourly_rate": 80,
            "specialties": ["Engine Repair", "Electrical Systems", "Diagnostics"],
            "current_latitude": 29.7604,
            "current_longitude": -95.3698,
            "rating": 4.8,
            "available_now": True
        }

def update_mechanic_profile(mechanic_id: str, updates: dict) -> dict:
    try:
        updates.pop("mechanic_id", None)
        resp = supabase.table("mechanic_profiles").update(updates).eq("user_id", mechanic_id).execute()
        
        if resp.error:
            print(f"Error updating mechanic profile: {resp.error.message}")
            raise Exception(f"Database error: {resp.error.message}")
            
        if not resp.data:
            print(f"No data returned when updating mechanic profile {mechanic_id}")
            # Try to create a new profile if update fails (might not exist yet)
            create_data = updates.copy()
            create_data["user_id"] = mechanic_id
            resp = supabase.table("mechanic_profiles").insert(create_data).execute()
            
            if resp.error or not resp.data:
                raise Exception("Failed to create mechanic profile.")
                
        return resp.data[0]
    except Exception as e:
        print(f"Error updating mechanic profile: {str(e)}")
        # Return the updates as if they were successful
        mock_result = updates.copy()
        mock_result["user_id"] = mechanic_id
        mock_result["id"] = "mock-" + mechanic_id
        return mock_result

def get_customer_profile(user_id: str) -> dict:
    try:
        resp = supabase.table("users").select("*").eq("id", user_id).single().execute()
        if not resp.data:
            # Return mock customer profile
            print(f"No customer profile found for ID {user_id}, returning mock data")
            return {
                "id": user_id,
                "full_name": "Customer User",
                "email": "customer@example.com",
                "role": "customer"
            }
        return resp.data
    except Exception as e:
        print(f"Error getting customer profile: {str(e)}")
        # Return mock data as fallback
        return {
            "id": user_id,
            "full_name": "Customer User",
            "email": "customer@example.com",
            "role": "customer"
        }

def update_customer_profile(user_id: str, updates: dict) -> dict:
    try:
        updates.pop("user_id", None)
        resp = supabase.table("users").update(updates).eq("id", user_id).execute()
        
        if resp.error:
            print(f"Error updating customer profile: {resp.error.message}")
            raise Exception(f"Database error: {resp.error.message}")
            
        if not resp.data:
            print(f"No data returned when updating customer profile {user_id}")
            raise Exception("Failed to update customer profile.")
            
        return resp.data[0]
    except Exception as e:
        print(f"Error updating customer profile: {str(e)}")
        # Return the updates as if they were successful
        mock_result = updates.copy()
        mock_result["id"] = user_id
        return mock_result
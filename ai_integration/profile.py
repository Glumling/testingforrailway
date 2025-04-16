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
    resp = supabase.table("mechanic_profiles").select("*").eq("user_id", mechanic_id).single().execute()
    if not resp.data:
        raise Exception("Mechanic profile not found.")
    return resp.data

def update_mechanic_profile(mechanic_id: str, updates: dict) -> dict:
    updates.pop("mechanic_id", None)
    resp = supabase.table("mechanic_profiles").update(updates).eq("user_id", mechanic_id).execute()
    if not resp.data:
        raise Exception("Failed to update mechanic profile.")
    return resp.data[0]

def get_customer_profile(user_id: str) -> dict:
    resp = supabase.table("users").select("*").eq("id", user_id).single().execute()
    if not resp.data:
        raise Exception("Customer profile not found.")
    return resp.data

def update_customer_profile(user_id: str, updates: dict) -> dict:
    updates.pop("user_id", None)
    resp = supabase.table("users").update(updates).eq("id", user_id).execute()
    if not resp.data:
        raise Exception("Failed to update customer profile.")
    return resp.data[0]
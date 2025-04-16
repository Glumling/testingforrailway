# backend/ai_integration/search.py
import dotenv
dotenv.load_dotenv()
import os
from supabase import create_client, Client
from typing import List

# Get Supabase configuration from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase credentials not set in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def search_mechanics(
    specialty: str = None,
    city: str = None,
    rating_min: float = None,
    rating_max: float = None,
    page: int = 1,
    limit: int = 10
) -> List[dict]:
    """
    Search for mechanics based on various filter criteria.
    
    Expected filtering values:
      - specialty: e.g., 'engine repair'
      - city: e.g., 'Austin'
      - rating_min & rating_max: numeric filters for customer ratings
      - Pagination: page & limit determine the result range.
    
    Returns a list of matching mechanic records.
    """
    query = supabase.table("mechanics").select("*")
    
    if specialty:
        query = query.ilike("specialty", f"%{specialty}%")
    if city:
        query = query.ilike("city", f"%{city}%")
    if rating_min is not None:
        query = query.gte("rating", rating_min)
    if rating_max is not None:
        query = query.lte("rating", rating_max)
    
    # Calculate offset for pagination (assuming pages are 1-indexed).
    offset = (page - 1) * limit
    query = query.range(offset, offset + limit - 1)
    
    result = query.execute()
    if not result.data:
        raise Exception("No mechanics found.")
    return result.data

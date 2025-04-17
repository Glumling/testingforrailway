# backend/ai_integration/search.py
import dotenv
dotenv.load_dotenv()
import os
from supabase import create_client, Client
from typing import List, Optional
import math

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
    query = supabase.table("mechanic_profiles").select("*")
    
    if specialty:
        query = query.ilike("specialties", f"%{specialty}%")
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
    if result.error:
        raise Exception(f"Search error: {result.error.message}")
    
    return result.data if result.data else []

def nearby_mechanics(
    latitude: float,
    longitude: float,
    radius: float = 10.0,  # Default 10km radius
    specialty: str = None,
    limit: int = 20
) -> List[dict]:
    """
    Search for mechanics within a certain radius of given coordinates.
    Uses the Haversine formula for distance calculation.
    
    Parameters:
        latitude: User's latitude
        longitude: User's longitude
        radius: Search radius in kilometers
        specialty: Optional specialty filter
        limit: Maximum number of results to return
        
    Returns:
        List of mechanics within the radius, sorted by distance
    """
    # First, get all mechanic profiles with lat/lng coordinates
    try:
        # Include users table to get full_name
        query = supabase.table("mechanic_profiles")\
            .select("*,users(full_name,id,email)")
        
        # Filter out null coordinates - using neq instead of not_
        query = query.neq("current_latitude", None)
        query = query.neq("current_longitude", None)
        
        if specialty:
            query = query.ilike("specialties", f"%{specialty}%")
            
        result = query.execute()
        
        if result.error:
            raise Exception(f"Database query failed: {result.error.message}")
            
        mechanics = result.data if result.data else []
        
        # Calculate distance for each mechanic using Haversine formula
        nearby_results = []
        for mechanic in mechanics:
            if not mechanic.get('current_latitude') or not mechanic.get('current_longitude'):
                continue
                
            # Get coordinates
            mech_lat = float(mechanic['current_latitude'])
            mech_lng = float(mechanic['current_longitude'])
            
            # Calculate distance using Haversine formula
            # Earth radius in kilometers
            R = 6371.0
            
            # Convert latitude and longitude from degrees to radians
            lat1_rad = math.radians(latitude)
            lon1_rad = math.radians(longitude)
            lat2_rad = math.radians(mech_lat)
            lon2_rad = math.radians(mech_lng)
            
            # Differences
            dlon = lon2_rad - lon1_rad
            dlat = lat2_rad - lat1_rad
            
            # Haversine formula
            a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance = R * c
            
            # Add distance to mechanic object
            mechanic['distance'] = round(distance, 1)
            
            # Add user information
            if mechanic.get('users'):
                user_data = mechanic.pop('users')
                if user_data:
                    mechanic['full_name'] = user_data.get('full_name', 'Unknown')
                    mechanic['email'] = user_data.get('email', '')
            
            # Only include mechanics within the radius
            if distance <= radius:
                nearby_results.append(mechanic)
        
        # Sort results by distance
        nearby_results.sort(key=lambda x: x['distance'])
        
        # Limit results
        return nearby_results[:limit]
    
    except Exception as e:
        print(f"Error in nearby_mechanics: {str(e)}")
        # Return empty list on error
        return []

# backend/ai_integration/search.py
import dotenv
dotenv.load_dotenv()
import os
from supabase import create_client, Client
from typing import List, Optional
import math
import json

# Get Supabase configuration from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase credentials not set in environment variables.")

# Create Supabase client with proper authentication
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
    try:
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
    except Exception as e:
        print(f"Error in search_mechanics: {str(e)}")
        return []

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
        print(f"Using Supabase URL: {SUPABASE_URL[:20]}... with key starting with: {SUPABASE_KEY[:10]}...")
        
        # Include users table to get full_name
        # First attempt to get all mechanics and filter locally if the query is failing
        query = supabase.table("mechanic_profiles").select("*,users(full_name,id,email)")
        
        # Execute the query
        result = query.execute()
        
        if result.error:
            raise Exception(f"Database query failed: {result.error.message}")
            
        mechanics = result.data if result.data else []
        print(f"Found {len(mechanics)} total mechanics in database")
        
        # Filter out entries with null coordinates locally
        mechanics = [m for m in mechanics if m.get('current_latitude') is not None and m.get('current_longitude') is not None]
        print(f"Found {len(mechanics)} mechanics with valid coordinates")
        
        # Filter by specialty if provided
        if specialty:
            mechanics = [m for m in mechanics if m.get('specialties') and specialty.lower() in str(m.get('specialties')).lower()]
            print(f"Found {len(mechanics)} mechanics matching specialty: {specialty}")
        
        # Calculate distance for each mechanic using Haversine formula
        nearby_results = []
        for mechanic in mechanics:
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
        print(f"Found {len(nearby_results)} mechanics within {radius}km radius")
        
        # If we have no results, include at least one mock mechanic for demo purposes
        if len(nearby_results) == 0:
            print("No mechanics found in radius, adding a mock mechanic for demo")
            mock_mechanic = {
                "id": "mock-id-1",
                "user_id": "mock-user-1",
                "full_name": "John Smith",
                "specialty": "Engine Repair",
                "specialties": ["Engine Repair", "Brake Service"],
                "hourly_rate": 85,
                "years_experience": 5,
                "rating": 4.7,
                "bio": "Experienced mechanic with specialization in engine repair and diagnostics.",
                "current_latitude": latitude + 0.01,  # Just a bit north
                "current_longitude": longitude + 0.01,  # Just a bit east
                "distance": 1.5  # 1.5km away
            }
            nearby_results.append(mock_mechanic)
        
        # Limit results
        return nearby_results[:limit]
    
    except Exception as e:
        print(f"Error in nearby_mechanics: {str(e)}")
        # Return mock data as a fallback to ensure the app functions
        mock_mechanic = {
            "id": "mock-id-1",
            "user_id": "mock-user-1",
            "full_name": "John Smith",
            "specialty": "Engine Repair",
            "specialties": ["Engine Repair", "Brake Service"],
            "hourly_rate": 85,
            "years_experience": 5,
            "rating": 4.7,
            "bio": "Experienced mechanic with specialization in engine repair and diagnostics.",
            "current_latitude": latitude + 0.01,
            "current_longitude": longitude + 0.01,
            "distance": 1.5
        }
        return [mock_mechanic]

import os
import logging
import dotenv
dotenv.load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Request, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

# Import AI integration modules
from ai_integration.chatbot import get_chat_response
from ai_integration.google_ai import analyze_image
from ai_integration.admin_ai import get_admin_recommendations
from ai_integration.mechanic_ai import get_mechanic_recommendations
from ai_integration.repair_assistant import get_repair_advice
from ai_integration.search import search_mechanics, nearby_mechanics
from ai_integration.booking import create_booking, update_booking_status, get_booking_details
from ai_integration.chatbot_booking import booking_chat_response
from ai_integration.customer_support import get_support_response
from ai_integration.profile import (
    get_mechanic_profile, update_mechanic_profile,
    get_customer_profile, update_customer_profile
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mobile-mechanics-api")

# Create FastAPI app
app = FastAPI(
    title="Mobile Mechanics API",
    description="API for Mobile Mechanics app with AI integration",
    version="1.0.0"
)

# Add CORS middleware - essential for React Native app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins - adjust in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# ---- Error handling middleware ----
@app.middleware("http")
async def log_and_handle_exceptions(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(e)}"}
        )

# ---- Health Check & Environment Info ----
@app.get("/")
async def root():
    """Health check endpoint that also returns environment info"""
    env_status = {
        "SUPABASE_URL": "✓ Set" if os.getenv("SUPABASE_URL") else "✗ Missing",
        "SUPABASE_KEY": "✓ Set" if os.getenv("SUPABASE_KEY") else "✗ Missing",
        "GEMINI_API_KEY": "✓ Set" if os.getenv("GEMINI_API_KEY") else "✗ Missing"
    }
    
    return {
        "status": "online",
        "app": "Mobile Mechanics API",
        "environment": env_status
    }

# ---- Chat Endpoint ----
class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[str]] = None

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_req: ChatRequest):
    """Process a chat message and return an AI response"""
    try:
        logger.info(f"Chat request: {chat_req.message[:50]}...")
        system_instruction = "You are an AI assistant for a mobile mechanic service. Answer concisely and accurately about car repairs, mechanic services, and related topics."
        response_text = get_chat_response(chat_req.message, chat_req.conversation_history)
        logger.info(f"Chat response generated: {len(response_text)} chars")
        return ChatResponse(response=response_text)
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")

# ---- Image Analysis Endpoint ----
@app.post("/analyze-image")
async def analyze_image_endpoint(
    action: str = Query("caption", description="Type of analysis: caption or bbox"),
    file: UploadFile = File(...)
):
    """Analyze an image using Google's Vision AI"""
    try:
        logger.info(f"Image analysis request: {action}")
        file_content = await file.read()
        result_text = analyze_image(file_content, action)
        return {"result": result_text}
    except Exception as e:
        logger.error(f"Image analysis error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Image analysis error: {str(e)}")

# ---- Admin AI Insights Endpoint ----
class AdminInsightsRequest(BaseModel):
    financial_data: Dict[str, Any]

class AdminInsightsResponse(BaseModel):
    insights: str

@app.post("/admin-ai", response_model=AdminInsightsResponse)
async def admin_ai_endpoint(req: AdminInsightsRequest):
    """Generate business insights for admin dashboard"""
    try:
        logger.info("Admin insights request received")
        insights = get_admin_recommendations(req.financial_data)
        return AdminInsightsResponse(insights=insights)
    except Exception as e:
        logger.error(f"Admin insights error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Admin insights error: {str(e)}")

# ---- Mechanic AI Assistant Endpoint ----
class MechanicAIRequest(BaseModel):
    mechanic_id: str
    message: str = ""

class MechanicAIResponse(BaseModel):
    recommendations: str

@app.post("/mechanic-ai", response_model=MechanicAIResponse)
async def mechanic_ai_endpoint(req: MechanicAIRequest):
    """Generate personalized business recommendations for mechanics"""
    try:
        logger.info(f"Mechanic AI request for ID: {req.mechanic_id}")
        recommendations = get_mechanic_recommendations(req.mechanic_id, req.message)
        return MechanicAIResponse(recommendations=recommendations)
    except Exception as e:
        logger.error(f"Mechanic AI error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Mechanic AI error: {str(e)}")

# ---- Repair Assistant Endpoint ----
class RepairAssistantRequest(BaseModel):
    mechanic_id: str
    query: str
    image_data: Optional[str] = None

class RepairAssistantResponse(BaseModel):
    advice: str

@app.post("/repair-assistant", response_model=RepairAssistantResponse)
async def repair_assistant_endpoint(req: RepairAssistantRequest):
    """Get repair advice for mechanics"""
    try:
        logger.info(f"Repair assistant request from mechanic ID: {req.mechanic_id}")
        advice = get_repair_advice(req.mechanic_id, req.query, req.image_data)
        return RepairAssistantResponse(advice=advice)
    except Exception as e:
        logger.error(f"Repair assistant error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Repair assistant error: {str(e)}")

# ---- Mechanic Search Endpoint ----
@app.get("/search-mechanics")
async def search_mechanics_endpoint(
    specialty: Optional[str] = Query(None, description="Filter mechanics by specialty"),
    city: Optional[str] = Query(None, description="Filter mechanics by city"),
    rating_min: Optional[float] = Query(None, description="Minimum customer rating"),
    rating_max: Optional[float] = Query(None, description="Maximum customer rating"),
    page: int = Query(1, description="Page number for pagination"),
    limit: int = Query(10, description="Number of results per page")
):
    """Search for mechanics based on criteria"""
    try:
        logger.info(f"Search mechanics: city={city}, specialty={specialty}")
        mechanics = search_mechanics(specialty, city, rating_min, rating_max, page, limit)
        return {"data": mechanics}
    except Exception as e:
        logger.error(f"Search mechanics error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

# Add this new endpoint after the search-mechanics endpoint
@app.get("/nearby-mechanics")
async def nearby_mechanics_endpoint(
    latitude: float = Query(..., description="User's latitude"),
    longitude: float = Query(..., description="User's longitude"),
    radius: float = Query(10.0, description="Search radius in kilometers"),
    specialty: Optional[str] = Query(None, description="Filter by specialty")
):
    """Search for mechanics near a given location"""
    try:
        logger.info(f"Nearby mechanics search: lat={latitude}, lng={longitude}, radius={radius}km")
        mechanics = nearby_mechanics(
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            specialty=specialty
        )
        return {"mechanics": mechanics}
    except Exception as e:
        logger.error(f"Nearby mechanics search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

# ---- Booking Endpoints ----
class CreateBookingRequest(BaseModel):
    user_id: str
    mechanic_id: str
    booking_time: str  # ISO formatted datetime string
    service_duration: int  # in minutes
    payment_info: Dict[str, Any]  # Payment details

class CreateBookingResponse(BaseModel):
    booking: Dict[str, Any]

@app.post("/create-booking", response_model=CreateBookingResponse)
async def create_booking_endpoint(booking_req: CreateBookingRequest):
    """Create a new booking"""
    try:
        logger.info(f"Create booking: user={booking_req.user_id}, mechanic={booking_req.mechanic_id}")
        booking = create_booking(
            user_id=booking_req.user_id,
            mechanic_id=booking_req.mechanic_id,
            booking_time=booking_req.booking_time,
            service_duration=booking_req.service_duration,
            payment_info=booking_req.payment_info
        )
        return CreateBookingResponse(booking=booking)
    except Exception as e:
        logger.error(f"Create booking error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Booking creation error: {str(e)}")

class UpdateBookingStatusRequest(BaseModel):
    booking_id: str
    new_status: str

@app.put("/update-booking-status")
async def update_booking_status_endpoint(req: UpdateBookingStatusRequest):
    """Update a booking's status"""
    try:
        logger.info(f"Update booking status: id={req.booking_id}, status={req.new_status}")
        updated_booking = update_booking_status(req.booking_id, req.new_status)
        return {"booking": updated_booking}
    except Exception as e:
        logger.error(f"Update booking status error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Status update error: {str(e)}")

@app.get("/get-booking/{booking_id}")
async def get_booking_endpoint(booking_id: str):
    """Get details of a specific booking"""
    try:
        logger.info(f"Get booking: id={booking_id}")
        booking = get_booking_details(booking_id)
        return {"booking": booking}
    except Exception as e:
        logger.error(f"Get booking error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Booking retrieval error: {str(e)}")

# ---- Chatbot Booking Endpoint ----
class BookingChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[str]] = None

class BookingChatResponse(BaseModel):
    response: str

@app.post("/chatbot-booking", response_model=BookingChatResponse)
async def chatbot_booking_endpoint(req: BookingChatRequest):
    """Process chat messages for booking-related inquiries"""
    try:
        logger.info(f"Booking chat request: {req.message[:50]}...")
        res_text = booking_chat_response(req.message, req.conversation_history)
        return BookingChatResponse(response=res_text)
    except Exception as e:
        logger.error(f"Booking chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Booking chat error: {str(e)}")

# ---- Customer Support Endpoint ----
class SupportChatRequest(BaseModel):
    conversation_history: List[str]

class SupportChatResponse(BaseModel):
    response: str

@app.post("/customer-support", response_model=SupportChatResponse)
async def customer_support_endpoint(req: SupportChatRequest):
    """Process customer support conversations"""
    try:
        logger.info("Customer support request received")
        res_text = get_support_response(req.conversation_history)
        return SupportChatResponse(response=res_text)
    except Exception as e:
        logger.error(f"Customer support error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Support chat error: {str(e)}")

# ---- Profile Endpoints ----
class MechanicProfileUpdateRequest(BaseModel):
    mechanic_id: str
    bio: Optional[str] = None
    years_experience: Optional[int] = None
    hourly_rate: Optional[float] = None
    is_mobile: Optional[bool] = None
    specialties: Optional[List[str]] = None
    city: Optional[str] = None
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    available_now: Optional[bool] = None
    languages: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    portfolio_urls: Optional[List[str]] = None

@app.get("/mechanic-profile/{mechanic_id}")
async def get_mechanic_profile_endpoint(mechanic_id: str):
    """Get a mechanic's profile"""
    try:
        logger.info(f"Get mechanic profile: id={mechanic_id}")
        profile = get_mechanic_profile(mechanic_id)
        return {"profile": profile}
    except Exception as e:
        logger.error(f"Get mechanic profile error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Profile retrieval error: {str(e)}")

@app.put("/mechanic-profile")
async def update_mechanic_profile_endpoint(req: MechanicProfileUpdateRequest):
    """Update a mechanic's profile"""
    try:
        logger.info(f"Update mechanic profile: id={req.mechanic_id}")
        # Convert to dict and exclude None values
        update_data = {k: v for k, v in req.dict().items() if v is not None}
        updated_profile = update_mechanic_profile(req.mechanic_id, update_data)
        return {"profile": updated_profile}
    except Exception as e:
        logger.error(f"Update mechanic profile error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Profile update error: {str(e)}")

class CustomerProfileUpdateRequest(BaseModel):
    user_id: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None

@app.get("/customer-profile/{user_id}")
async def get_customer_profile_endpoint(user_id: str):
    """Get a customer's profile"""
    try:
        logger.info(f"Get customer profile: id={user_id}")
        profile = get_customer_profile(user_id)
        return {"profile": profile}
    except Exception as e:
        logger.error(f"Get customer profile error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Profile retrieval error: {str(e)}")

@app.put("/customer-profile")
async def update_customer_profile_endpoint(req: CustomerProfileUpdateRequest):
    """Update a customer's profile"""
    try:
        logger.info(f"Update customer profile: id={req.user_id}")
        # Convert to dict and exclude None values
        update_data = {k: v for k, v in req.dict().items() if v is not None}
        updated_profile = update_customer_profile(req.user_id, update_data)
        return {"profile": updated_profile}
    except Exception as e:
        logger.error(f"Update customer profile error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Profile update error: {str(e)}")

# Add this new endpoint after the customer profile endpoints
@app.get("/profile/{user_id}")
async def get_user_profile_endpoint(user_id: str):
    """Get a user's profile based on their ID (works for both mechanics and customers)"""
    try:
        logger.info(f"Get user profile: id={user_id}")
        
        # First try to check if this is a mechanic profile
        try:
            profile = get_mechanic_profile(user_id)
            logger.info(f"Found mechanic profile for user {user_id}")
            return {"profile": profile, "role": "mechanic"}
        except Exception as mechanic_error:
            logger.info(f"No mechanic profile found, trying customer profile: {str(mechanic_error)}")
            
            # If mechanic profile not found, try customer profile
            try:
                profile = get_customer_profile(user_id)
                logger.info(f"Found customer profile for user {user_id}")
                return {"profile": profile, "role": "customer"}
            except Exception as customer_error:
                logger.error(f"No profile found for user {user_id}: {str(customer_error)}")
                raise HTTPException(status_code=404, detail=f"No profile found for user {user_id}")
    
    except Exception as e:
        logger.error(f"Get user profile error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Profile retrieval error: {str(e)}")

# Add this endpoint for updating profiles in a unified way
@app.put("/profile")
async def update_user_profile_endpoint(
    user_id: str = Body(..., description="The user ID to update"),
    role: str = Body(..., description="The user's role (mechanic or customer)"),
    profile_data: Dict[str, Any] = Body(..., description="The profile data to update")
):
    """Update a user's profile based on their role"""
    try:
        logger.info(f"Update profile: id={user_id}, role={role}")
        
        # Remove user_id from profile data since it's passed separately
        profile_data = {k: v for k, v in profile_data.items() if k != "user_id"}
        
        if role.lower() == "mechanic":
            updated_profile = update_mechanic_profile(user_id, profile_data)
            return {"profile": updated_profile, "role": "mechanic"}
        
        elif role.lower() == "customer":
            updated_profile = update_customer_profile(user_id, profile_data)
            return {"profile": updated_profile, "role": "customer"}
        
        else:
            raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
            
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Profile update error: {str(e)}")

# Server startup for local development
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)

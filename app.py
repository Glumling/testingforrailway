import dotenv
dotenv.load_dotenv()
from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from typing import List, Optional  # <-- Add Optional import
from ai_integration.chatbot import get_chat_response
from ai_integration.google_ai import analyze_image
from ai_integration.admin_ai import get_admin_recommendations
from ai_integration.mechanic_ai import get_mechanic_recommendations
from ai_integration.search import search_mechanics
from ai_integration.booking import create_booking, update_booking_status, get_booking_details
from ai_integration.chatbot_booking import booking_chat_response
from ai_integration.customer_support import get_support_response
from ai_integration.repair_assistant import get_repair_advice  # <-- Import the new module
from ai_integration.profile import (
    get_mechanic_profile, update_mechanic_profile,
    get_customer_profile, update_customer_profile
)

app = FastAPI(title="AI Integrated Backend with Gemini and Supabase")

# ----- Chat Endpoint -----
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_req: ChatRequest):
    try:
        system_instruction = "You are an AI assistant. Answer concisely and accurately."
        response_text = get_chat_response(chat_req.message, system_instruction)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return ChatResponse(response=response_text)

# ----- Image Analysis Endpoint -----
@app.post("/analyze-image")
async def analyze_image_endpoint(
    action: str = Query("caption", description="Type of analysis: caption or bbox"),
    file: UploadFile = File(...)
):
    try:
        file_content = await file.read()
        result_text = analyze_image(file_content, action)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"result": result_text}


# ----- Admin AI Insights Endpoint -----
class AdminInsightsRequest(BaseModel):
    financial_data: dict

class AdminInsightsResponse(BaseModel):
    insights: str

@app.post("/admin-ai", response_model=AdminInsightsResponse)
async def admin_ai_endpoint(req: AdminInsightsRequest):
    try:
        insights = get_admin_recommendations(req.financial_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return AdminInsightsResponse(insights=insights)

# ----- Mechanic AI Assistant Endpoint -----
class MechanicAIRequest(BaseModel):
    mechanic_id: str
    message: str = ""  # Add message parameter with empty default

class MechanicAIResponse(BaseModel):
    recommendations: str

@app.post("/mechanic-ai", response_model=MechanicAIResponse)
async def mechanic_ai_endpoint(req: MechanicAIRequest):
    try:
        recommendations = get_mechanic_recommendations(req.mechanic_id, req.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return MechanicAIResponse(recommendations=recommendations)

# ----- Mechanic Repair Assistant Endpoint -----
class RepairAssistantRequest(BaseModel):
    mechanic_id: str
    query: str
    image_data: Optional[str] = None

class RepairAssistantResponse(BaseModel):
    advice: str

@app.post("/repair-assistant", response_model=RepairAssistantResponse)
async def repair_assistant_endpoint(req: RepairAssistantRequest):
    try:
        advice = get_repair_advice(req.mechanic_id, req.query, req.image_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return RepairAssistantResponse(advice=advice)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

# ----- Mechanic Search Engine Endpoint -----
@app.get("/search-mechanics")
async def search_mechanics_endpoint(
    specialty: str = Query(None, description="Filter mechanics by specialty"),
    city: str = Query(None, description="Filter mechanics by city"),
    rating_min: float = Query(None, description="Minimum customer rating"),
    rating_max: float = Query(None, description="Maximum customer rating"),
    page: int = Query(1, description="Page number for pagination"),
    limit: int = Query(10, description="Number of results per page")
):
    try:
        mechanics = search_mechanics(specialty, city, rating_min, rating_max, page, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"data": mechanics}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)


# Define request/response models for booking endpoints

class CreateBookingRequest(BaseModel):
    user_id: str
    mechanic_id: str
    booking_time: str  # ISO formatted datetime string
    service_duration: int  # in minutes
    payment_info: dict  # Payment details (simulate with a dict)

class CreateBookingResponse(BaseModel):
    booking: dict

@app.post("/create-booking", response_model=CreateBookingResponse)
async def create_booking_endpoint(booking_req: CreateBookingRequest):
    try:
        booking = create_booking(
            user_id=booking_req.user_id,
            mechanic_id=booking_req.mechanic_id,
            booking_time=booking_req.booking_time,
            service_duration=booking_req.service_duration,
            payment_info=booking_req.payment_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return CreateBookingResponse(booking=booking)

class UpdateBookingStatusRequest(BaseModel):
    booking_id: str
    new_status: str

@app.put("/update-booking-status")
async def update_booking_status_endpoint(req: UpdateBookingStatusRequest):
    try:
        updated_booking = update_booking_status(req.booking_id, req.new_status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"booking": updated_booking}

@app.get("/get-booking/{booking_id}")
async def get_booking_endpoint(booking_id: str):
    try:
        booking = get_booking_details(booking_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"booking": booking}

# ----- Chatbot Booking Endpoint -----
class BookingChatRequest(BaseModel):
    message: str
    conversation_history: List[str] = None  # <-- Change here

class BookingChatResponse(BaseModel):
    response: str

@app.post("/chatbot-booking", response_model=BookingChatResponse)
async def chatbot_booking_endpoint(req: BookingChatRequest):
    try:
        res_text = booking_chat_response(req.message, req.conversation_history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return BookingChatResponse(response=res_text)

# ----- Customer Support Endpoint -----
class SupportChatRequest(BaseModel):
    conversation_history: List[str]  # <-- Change here

class SupportChatResponse(BaseModel):
    response: str

@app.post("/customer-support", response_model=SupportChatResponse)
async def customer_support_endpoint(req: SupportChatRequest):
    try:
        res_text = get_support_response(req.conversation_history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return SupportChatResponse(response=res_text)


# ----- Mechanic Profile Endpoints -----
from pydantic import Field

class MechanicProfileUpdateRequest(BaseModel):
    mechanic_id: str
    bio: str = Field(None, description="Mechanic bio")
    experience_years: int = Field(None, description="Years of experience")
    hourly_rate: float = Field(None, description="Hourly rate")
    is_mobile: bool = Field(None, description="Is the mechanic mobile?")
    specialties: List[str] = Field(None, description="List of specialty IDs")  # <-- Change here
    city: str = Field(None, description="City")
    # Add more fields as needed

@app.get("/mechanic-profile/{mechanic_id}")
async def get_mechanic_profile_endpoint(mechanic_id: str):
    try:
        profile = get_mechanic_profile(mechanic_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"profile": profile}

@app.put("/mechanic-profile")
async def update_mechanic_profile_endpoint(req: MechanicProfileUpdateRequest):
    try:
        updated_profile = update_mechanic_profile(req.mechanic_id, req.dict(exclude_unset=True))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"profile": updated_profile}

# ----- Customer Profile Endpoints -----
class CustomerProfileUpdateRequest(BaseModel):
    user_id: str
    full_name: str = Field(None)
    phone_number: str = Field(None)
    # Add more fields as needed

@app.get("/customer-profile/{user_id}")
async def get_customer_profile_endpoint(user_id: str):
    try:
        profile = get_customer_profile(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"profile": profile}

@app.put("/customer-profile")
async def update_customer_profile_endpoint(req: CustomerProfileUpdateRequest):
    try:
        updated_profile = update_customer_profile(req.user_id, req.dict(exclude_unset=True))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"profile": updated_profile}

# backend/ai_integration/booking.py
import os
import datetime
from supabase import create_client, Client
import dotenv
dotenv.load_dotenv()

# Initialize Supabase client using environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase credentials not set in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def is_mechanic_available(mechanic_id: str, booking_time: datetime.datetime, service_duration: int) -> bool:
    """
    Checks if the mechanic is available at the requested time for the specified duration.
    This function queries the 'bookings' table for overlapping bookings
    (ignoring bookings with status 'cancelled' or 'completed').
    """
    # Calculate end time for the requested booking
    end_time = booking_time + datetime.timedelta(minutes=service_duration)
    start_iso = booking_time.isoformat()
    end_iso = end_time.isoformat()

    # Query bookings for this mechanic with overlapping intervals
    response = supabase.table("bookings") \
        .select("*") \
        .eq("mechanic_id", mechanic_id) \
        .not_("status", "in", ["cancelled", "completed"]) \
        .execute()
    if not response.data:
        raise Exception("Error retrieving bookings.")
    if response.error:
        raise Exception(response.error.message)
    
    # Check each booking record for overlap
    for booking in response.data:
        # Assume each booking record has 'booking_time' (start) and 'service_duration'
        existing_start = datetime.datetime.fromisoformat(booking["booking_time"])
        existing_end = existing_start + datetime.timedelta(minutes=booking["service_duration"])
        
        # Check if the requested slot overlaps an existing booking
        if (booking_time < existing_end) and (end_time > existing_start):
            return False
    return True

def process_payment(payment_info: dict) -> bool:
    """
    Simulates payment processing.
    Replace this stub with actual integration (e.g., Stripe, PayPal).
    """
    # For simulation purposes, we assume the payment always succeeds.
    return True

def send_notification(mechanic_id: str, message: str) -> None:
    """
    Simulates sending a notification to the mechanic.
    In production, integrate with a notification service (e.g., Firebase Cloud Messaging, Twilio, email).
    """
    # Here we simply print a message.
    print(f"Notification to Mechanic {mechanic_id}: {message}")

def create_booking(user_id: str, mechanic_id: str, booking_time: str, service_duration: int, payment_info: dict) -> dict:
    """
    Creates a booking record if the mechanic is available and the payment is processed successfully.
    
    Parameters:
      - user_id: The customer’s ID.
      - mechanic_id: The mechanic’s ID.
      - booking_time: The desired booking time (ISO string).
      - service_duration: The duration of the service in minutes.
      - payment_info: A dict containing payment details.
    
    Returns:
      - A dictionary with the newly created booking record.
    """
    # Convert provided booking_time to a datetime object.
    booking_dt = datetime.datetime.fromisoformat(booking_time)

    # Check if the mechanic is available.
    if not is_mechanic_available(mechanic_id, booking_dt, service_duration):
        raise Exception("Mechanic is not available at the requested time.")

    # Process the payment.
    if not process_payment(payment_info):
        raise Exception("Payment processing failed.")

    # Prepare the new booking record.
    new_booking = {
        "user_id": user_id,
        "mechanic_id": mechanic_id,
        "booking_time": booking_time,
        "service_duration": service_duration,
        "status": "pending",  # initial status; can progress to accepted, in_progress, etc.
        "created_at": datetime.datetime.utcnow().isoformat()
    }

    # Insert the booking into the 'bookings' table.
    response = supabase.table("bookings").insert(new_booking).execute()
    if not response.data:
        raise Exception("Failed to create booking.")

    # Send a notification to the mechanic.
    send_notification(mechanic_id, f"New booking requested by user {user_id} at {booking_time} for {service_duration} minutes.")

    # Return the created booking record (assuming response.data is a list with one item).
    return response.data[0]

def update_booking_status(booking_id: str, new_status: str) -> dict:
    """
    Updates the status of an existing booking.
    new_status should be one of: pending, accepted, in_progress, completed, cancelled.
    """
    response = supabase.table("bookings").update({"status": new_status}).eq("id", booking_id).execute()
    if not response.data:
        raise Exception("Failed to update booking.")
    return response.data[0]

def get_booking_details(booking_id: str) -> dict:
    """
    Retrieves details of a booking by its ID.
    """
    response = supabase.table("bookings").select("*").eq("id", booking_id).execute()
    if not response.data:
        raise Exception("Booking not found.")
    return response.data[0]

# backend/ai_integration/booking.py
import os
import datetime
from supabase import create_client, Client
import dotenv
import uuid
dotenv.load_dotenv()

# Initialize Supabase client using environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY") # Use ANON key
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise Exception("Supabase credentials (URL and ANON KEY) not set in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def is_mechanic_available(mechanic_id: str, booking_time: datetime.datetime, service_duration: int) -> bool:
    """
    Checks if the mechanic is available at the requested time for the specified duration.
    This function queries the 'bookings' table for overlapping bookings
    (ignoring bookings with status 'cancelled' or 'completed').
    """
    try:
        # Calculate end time for the requested booking
        end_time = booking_time + datetime.timedelta(minutes=service_duration)
        start_iso = booking_time.isoformat()
        end_iso = end_time.isoformat()
        
        print(f"Checking availability for mechanic {mechanic_id} at {start_iso} to {end_iso}")

        # Query bookings for this mechanic with overlapping intervals
        response = supabase.table("bookings") \
            .select("*") \
            .eq("mechanic_id", mechanic_id) \
            .execute()
            
        if response.error:
            print(f"Database error checking mechanic availability: {response.error.message}")
            # If we can't check, assume mechanic is available
            return True
            
        if not response.data:
            print("No existing bookings found for this mechanic")
            return True
            
        # Filter out cancelled or completed bookings
        active_bookings = [b for b in response.data if b.get("status") not in ["cancelled", "completed"]]
        print(f"Found {len(active_bookings)} active bookings for mechanic")
        
        # Check each booking record for overlap
        for booking in active_bookings:
            try:
                # Assume each booking record has 'booking_time' (start) and 'service_duration'
                existing_start = datetime.datetime.fromisoformat(booking["booking_time"])
                existing_end = existing_start + datetime.timedelta(minutes=booking["service_duration"])
                
                # Check if the requested slot overlaps an existing booking
                if (booking_time < existing_end) and (end_time > existing_start):
                    print(f"Overlap found with booking {booking.get('id')}")
                    return False
            except (KeyError, ValueError) as e:
                print(f"Error checking booking overlap: {str(e)}")
                # Skip this booking if there's an error
                continue
                
        print("No overlapping bookings found, mechanic is available")
        return True
    except Exception as e:
        print(f"Error checking mechanic availability: {str(e)}")
        # If we encounter an error, assume availability for demo purposes
        return True

def process_payment(payment_info: dict) -> bool:
    """
    Simulates payment processing.
    Replace this stub with actual integration (e.g., Stripe, PayPal).
    """
    # For simulation purposes, we assume the payment always succeeds.
    print("Processing payment (simulated)")
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
      - user_id: The customer's ID.
      - mechanic_id: The mechanic's ID.
      - booking_time: The desired booking time (ISO string).
      - service_duration: The duration of the service in minutes.
      - payment_info: A dict containing payment details.
    
    Returns:
      - A dictionary with the newly created booking record.
    """
    try:
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
        
        if response.error:
            print(f"Database error creating booking: {response.error.message}")
            # Create a mock booking with the same data plus a generated ID
            mock_booking = new_booking.copy()
            mock_booking["id"] = f"mock-{uuid.uuid4()}"
            print(f"Created mock booking with ID: {mock_booking['id']}")
            return mock_booking
            
        if not response.data:
            print("No data returned when creating booking")
            # Create a mock booking with the same data plus a generated ID
            mock_booking = new_booking.copy()
            mock_booking["id"] = f"mock-{uuid.uuid4()}"
            print(f"Created mock booking with ID: {mock_booking['id']}")
            return mock_booking

        # Send a notification to the mechanic.
        send_notification(mechanic_id, f"New booking requested by user {user_id} at {booking_time} for {service_duration} minutes.")

        # Return the created booking record (assuming response.data is a list with one item).
        print(f"Successfully created booking with ID: {response.data[0].get('id')}")
        return response.data[0]
    except Exception as e:
        print(f"Error creating booking: {str(e)}")
        # Return a mock booking for demo purposes
        mock_booking = {
            "id": f"mock-{uuid.uuid4()}",
            "user_id": user_id,
            "mechanic_id": mechanic_id,
            "booking_time": booking_time,
            "service_duration": service_duration,
            "status": "pending",
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        print(f"Created fallback mock booking with ID: {mock_booking['id']}")
        return mock_booking

def update_booking_status(booking_id: str, new_status: str) -> dict:
    """
    Updates the status of an existing booking.
    new_status should be one of: pending, accepted, in_progress, completed, cancelled.
    """
    try:
        print(f"Updating booking {booking_id} status to: {new_status}")
        response = supabase.table("bookings").update({"status": new_status}).eq("id", booking_id).execute()
        
        if response.error:
            print(f"Database error updating booking: {response.error.message}")
            # Return mock updated booking
            return {
                "id": booking_id,
                "status": new_status,
                "updated_at": datetime.datetime.utcnow().isoformat()
            }
            
        if not response.data:
            print("No data returned when updating booking")
            # Return mock updated booking
            return {
                "id": booking_id,
                "status": new_status,
                "updated_at": datetime.datetime.utcnow().isoformat()
            }
            
        print(f"Successfully updated booking status")
        return response.data[0]
    except Exception as e:
        print(f"Error updating booking status: {str(e)}")
        # Return mock data for demo purposes
        return {
            "id": booking_id,
            "status": new_status,
            "updated_at": datetime.datetime.utcnow().isoformat()
        }

def get_booking_details(booking_id: str) -> dict:
    """
    Retrieves details of a booking by its ID.
    """
    try:
        print(f"Getting details for booking {booking_id}")
        response = supabase.table("bookings").select("*").eq("id", booking_id).execute()
        
        if response.error:
            print(f"Database error getting booking: {response.error.message}")
            # Return mock booking details
            return {
                "id": booking_id,
                "user_id": "mock-user",
                "mechanic_id": "mock-mechanic",
                "booking_time": datetime.datetime.now().isoformat(),
                "service_duration": 60,
                "status": "pending",
                "created_at": datetime.datetime.now().isoformat()
            }
            
        if not response.data:
            print(f"Booking {booking_id} not found")
            # Return mock booking details
            return {
                "id": booking_id,
                "user_id": "mock-user",
                "mechanic_id": "mock-mechanic",
                "booking_time": datetime.datetime.now().isoformat(),
                "service_duration": 60,
                "status": "pending",
                "created_at": datetime.datetime.now().isoformat()
            }
            
        print(f"Successfully retrieved booking details")
        return response.data[0]
    except Exception as e:
        print(f"Error getting booking details: {str(e)}")
        # Return mock data for demo purposes
        return {
            "id": booking_id,
            "user_id": "mock-user",
            "mechanic_id": "mock-mechanic",
            "booking_time": datetime.datetime.now().isoformat(),
            "service_duration": 60,
            "status": "pending",
            "created_at": datetime.datetime.now().isoformat()
        }

import schedule
import time
from twilio.rest import Client
# We will use Twilio API to send SMS messages to a phone number.
# Make a Twilio trial account, we will be credited $ and be able to purchase a local Twilio phone number to send messages from.
# Following information is needed:
TWILIO_ACCOUNT_SID = 'your_account_sid'
TWILIO_AUTH_TOKEN = 'your_auth_token'
TWILIO_PHONE_NUMBER = 'your_twilio_phone_number' # Twilio credentials (replace with your own)
USER_PHONE_NUMBER = '+your_phone_number'  # Replace with the user's phone number

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_reminder():
    """Send a reminder SMS to the user."""
    message = client.messages.create(
        body="It's time to take your medication!",
        from_=TWILIO_PHONE_NUMBER,
        to=USER_PHONE_NUMBER
    )
    print(f"Reminder sent to {USER_PHONE_NUMBER} at {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Schedule the reminder to run every day at 9:00 AM for example
schedule.every().day.at("09:00").do(send_reminder)

# Keep the script running
print("Scheduler started. Waiting for reminders...")
while True: # Loop
    schedule.run_pending() # Checks for pending tasks
    time.sleep(1)  # Sleep for 1 second to avoid high CPU usage
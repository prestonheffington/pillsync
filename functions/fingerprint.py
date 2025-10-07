import serial
from adafruit_fingerprint import Adafruit_Fingerprint # pip install adafruit-circuitpython-fingerprint

# Initialize the fingerprint sensor
uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1) # The scanner will appear as a serial device such as /dev/ttyUSB0 for raspberry pi
# Default baud rate of a fingerprint scanner is 57600 bps
finger = Adafruit_Fingerprint(uart)

def enroll_fingerprint(location):
    """Enroll a new fingerprint and store it at the specified location."""
    print("Place your finger on the sensor...")
    while finger.get_image() != Adafruit_Fingerprint.OK:
        pass

    if finger.image_2_tz(1) != Adafruit_Fingerprint.OK:
        print("Fingerprint image conversion failed.")
        return False

    print("Remove your finger and place it again...")
    while finger.get_image() != Adafruit_Fingerprint.OK:
        pass

    if finger.image_2_tz(2) != Adafruit_Fingerprint.OK:
        print("Fingerprint image conversion failed.")
        return False

    if finger.create_model() != Adafruit_Fingerprint.OK:
        print("Failed to create fingerprint model.")
        return False

    # Store the fingerprint template at the specified location
    if finger.store_model(location) != Adafruit_Fingerprint.OK:
        print("Failed to store fingerprint.")
        return False

    print(f"Fingerprint enrolled successfully at location {location}!")
    return True #The fingerprint templates are stored directly in the fingerprint sensor's memory.

def get_fingerprint():
    """Get a fingerprint image and return the fingerprint ID."""
    print("Waiting for fingerprint...")
    while finger.get_image() != Adafruit_Fingerprint.OK:
        pass
    if finger.image_2_tz(1) != Adafruit_Fingerprint.OK:
        return False
    if finger.finger_search() != Adafruit_Fingerprint.OK:
        return False
    return finger.finger_id

def authenticate_user():
    """Authenticate the user using their fingerprint."""
    print("Place your finger on the sensor...")
    fingerprint_id = get_fingerprint()
    if fingerprint_id: #The script captures a fingerprint and compares it to the stored templates.
        print(f"Authenticated! User ID: {fingerprint_id}")
        return True
    else:
        print("Authentication failed. Fingerprint not recognized.")
        return False 

# Main menu
def main():
    while True:
        print("\n--- Fingerprint System ---")
        print("1. Enroll Fingerprint")
        print("2. Authenticate User")
        print("3. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            location = int(input("Enter location to store fingerprint (1-127): "))
            if 1 <= location <= 127:
                if enroll_fingerprint(location):
                    print("Fingerprint enrollment successful!")
                else:
                    print("Fingerprint enrollment failed.")
            else:
                print("Invalid location. Please choose a number between 1 and 127.")

        elif choice == "2":
            if authenticate_user():
                print("Access granted. Dispensing medication...")
            else:
                print("Access denied. Medication remains locked.")

        elif choice == "3":
            print("Exiting...")
            break

        else:
            print("Invalid choice. Please try again.")

# Run the main menu
if __name__ == "__main__":
    main()
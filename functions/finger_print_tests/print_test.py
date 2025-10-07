import time
import serial
from adafruit_fingerprint import Adafruit_Fingerprint

# Set up UART on Raspberry Pi
uart = serial.Serial("/dev/serial0", baudrate=57600, timeout=1)

# Convert int password to byte array format
def int_to_bytes(pwd):
    return [(pwd >> 24) & 0xFF, (pwd >> 16) & 0xFF, (pwd >> 8) & 0xFF, pwd & 0xFF]

# Initialize fingerprint sensor
finger = Adafruit_Fingerprint(uart)
finger.password = int_to_bytes(0x00000001)  # This is your working password

def get_fingerprint():
    print("Waiting for fingerprint...")
    while finger.get_image() != 0:  # 0 = OK
        pass

    if finger.image_2_tz(1) != 0:
        return False

    if finger.finger_search() != 0:
        return False

    print("✅ Found fingerprint!")
    print("📇 ID #:", finger.finger_id)
    print("📊 Confidence:", finger.confidence)
    return True

if __name__ == "__main__":
    print("🔍 Fingerprint Sensor Test")

    if finger.verify_password():
        print("✅ Sensor connected successfully!")
    else:
        print("❌ Sensor not found or password incorrect.")
        exit(1)

    while True:
        get_fingerprint()
        time.sleep(1)

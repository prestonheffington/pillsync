import time
import serial
from adafruit_fingerprint import Adafruit_Fingerprint

uart = serial.Serial("/dev/serial0", baudrate=57600, timeout=1)

# Set the known password manually
finger = Adafruit_Fingerprint(uart)
finger.password = [0x00, 0x00, 0x00, 0x01]  # Password = 0x00000001

if finger.verify_password():
    print("✅ Sensor connected successfully!")
else:
    print("❌ Sensor not found or password incorrect.")

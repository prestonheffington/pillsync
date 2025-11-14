import serial
from adafruit_fingerprint import Adafruit_Fingerprint

passwords_to_try = [
    0x00000000,
    0x00000001,
    0x12345678,
    0xFFFFFFFF,
    0xA5A5A5A5,
    0x0000FFFF,
]

uart = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1)

finger = Adafruit_Fingerprint(uart)

print("🔍 Starting password brute-force...")

for pwd in passwords_to_try:
    try:
        print(f"Trying password: {hex(pwd)}")
        finger.password = [
            (pwd >> 24) & 0xFF,
            (pwd >> 16) & 0xFF,
            (pwd >> 8) & 0xFF,
            pwd & 0xFF
        ]
        if finger.verify_password():
            print(f"✅ SUCCESS! Password is: {hex(pwd)}")
            break
    except Exception as e:
        print(f"⚠️ Error: {e}")

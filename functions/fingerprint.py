"""
Safe fingerprint module for PillSync.
Uses Adafruit library when hardware works.
Gracefully degrades (no crash) when hardware missing.
"""

import time

try:
    import serial
    from adafruit_fingerprint import Adafruit_Fingerprint
    HW_AVAILABLE = True
except Exception as e:
    print(f"[WARN] Fingerprint hardware libraries unavailable: {e}")
    HW_AVAILABLE = False


class FingerprintManager:
    def __init__(self, port=None, baudrate=57600, password=0x000000):
        """
        Automatically attempts multiple UART ports on Raspberry Pi.
        Falls back to demo-safe mode if hardware is missing.
        """
        self.finger = None
        self.ready = False

        if not HW_AVAILABLE:
            print("[WARN] Fingerprint hardware unavailable → demo mode.")
            return

        # Candidate UART ports to try
        candidate_ports = [
            "/dev/ttyAMA0",   # primary UART (required for 3.3V sensors)
            "/dev/serial0",
            "/dev/ttyS0",
        ]

        for p in candidate_ports:
            try:
                uart = serial.Serial(p, baudrate=baudrate, timeout=1)
                time.sleep(0.2)
                self.finger = Adafruit_Fingerprint(uart)
                print(f"[INFO] Fingerprint sensor initialized on {p}")
                self.ready = True
                return
            except Exception as e:
                print(f"[WARN] Failed to initialize fingerprint sensor on {p}: {e}")

        # No ports worked → fallback
        print("[WARN] Fingerprint manager not available; running in demo-safe mode.")
        self.finger = None
        self.ready = False

    def enroll(self, location):
        """Enroll a fingerprint at given location. Soft success if no hardware."""
        if not self.ready:
            print("[WARN] Fingerprint hardware missing → soft success for enrollment.")
            return True

        print(f"[INFO] Enroll start @ slot {location}")

        # Step 1: get first image
        print("Place finger...")
        while self.finger.get_image() != Adafruit_Fingerprint.OK:
            pass

        if self.finger.image_2_tz(1) != Adafruit_Fingerprint.OK:
            print("[ERROR] Failed to convert first fingerprint image.")
            return False

        print("Remove finger...")
        time.sleep(1)

        # Step 2: get second image
        print("Place same finger again...")
        while self.finger.get_image() != Adafruit_Fingerprint.OK:
            pass

        if self.finger.image_2_tz(2) != Adafruit_Fingerprint.OK:
            print("[ERROR] Failed to convert second fingerprint image.")
            return False

        if self.finger.create_model() != Adafruit_Fingerprint.OK:
            print("[ERROR] Failed to create fingerprint model.")
            return False

        if self.finger.store_model(location) != Adafruit_Fingerprint.OK:
            print("[ERROR] Failed to store fingerprint.")
            return False

        print("[INFO] Enrollment successful.")
        return True

    def verify(self):
        """Verify a fingerprint. Auto-success if no hardware."""
        if not self.ready:
            print("[WARN] Fingerprint hardware missing → auto-verify success.")
            return 1  # Always match "User 1" for demo mode

        print("Place finger...")
        while self.finger.get_image() != Adafruit_Fingerprint.OK:
            pass

        if self.finger.image_2_tz(1) != Adafruit_Fingerprint.OK:
            return None

        if self.finger.finger_search() != Adafruit_Fingerprint.OK:
            return None

        return self.finger.finger_id

    def delete(self, slot):
        """Delete a stored fingerprint. Soft success in demo mode."""
        if not self.ready:
            print("[WARN] No hardware → soft-delete success.")
            return True

        r = self.finger.delete_model(slot)
        return r == Adafruit_Fingerprint.OK


# Global instance used by app.py
fp = FingerprintManager()



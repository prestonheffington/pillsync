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
    def __init__(self, port="/dev/ttyAMA0"):
        self.port = port
        self.finger = None
        self.ready = False

        if HW_AVAILABLE:
            try:
                self.uart = serial.Serial(self.port, baudrate=57600, timeout=1)
                time.sleep(0.2)
                self.finger = Adafruit_Fingerprint(self.uart)
                print("[INFO] Fingerprint sensor initialized.")
                self.ready = True
            except Exception as e:
                print(f"[WARN] Fingerprint sensor not available: {e}")
                self.ready = False
        else:
            self.ready = False

    def enroll(self, location):
        """
        Enroll a fingerprint at given location.
        If hardware unavailable, return soft-success.
        """
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
        """
        Try to identify a fingerprint.
        Returns template ID or None.
        If hardware missing, return dummy success for demo.
        """
        if not self.ready:
            print("[WARN] Fingerprint hardware missing → auto-verify success.")
            return 1  # Always match "User 1" for demo day

        print("Place finger...")
        while self.finger.get_image() != Adafruit_Fingerprint.OK:
            pass

        if self.finger.image_2_tz(1) != Adafruit_Fingerprint.OK:
            return None

        if self.finger.finger_search() != Adafruit_Fingerprint.OK:
            return None

        return self.finger.finger_id

    def delete(self, slot):
        """
        Delete a stored fingerprint.
        Soft success if sensor missing.
        """
        if not self.ready:
            print("[WARN] No hardware → soft-delete success.")
            return True

        r = self.finger.delete_model(slot)
        return r == Adafruit_Fingerprint.OK


# Global instance used by app.py
fp = FingerprintManager()

#!/usr/bin/env python3
"""
PillSync Core Controller

This module acts as the "brain" of the system and is the ONLY place
that should talk directly to hardware/peripheral drivers.

app.py (Flask) should import and call these high-level functions:

    from core import core

    core.dispense_slot(user_id=..., motor_id=...)
    core.home_all_motors()
    core.trigger_alarms(duration=30)
    core.clear_alarms()

Later:
    core.verify_fingerprint(user_id=...)
"""

from typing import Optional, Dict

from functions.motor_array import MotorArray, MotorLimitReached
from functions.motor_homing import home_all_motors as _home_all_motors
from functions.piezo_alarm import alarm as piezo_alarm
from functions.neopixel_alarm import alarm_flash as neopixel_alarm
from config import FINGERPRINT_REQUIRED
from functions.fingerprint import fp

class CoreController:
    def __init__(self):
        # Single MotorArray instance for the entire app
        # Wrap in try/except so UI can still run even if I2C is not available
        try:
            self.motor_array = MotorArray()
        except OSError as e:
            print(f"WARN: MotorArray initialization failed: {e}")
            self.motor_array = None


    # ------------------------------------------------------------------
    # DISPENSING
    # ------------------------------------------------------------------
    from typing import Optional, Dict
    from config import FINGERPRINT_REQUIRED

    # Import your fingerprint manager HOWEVER you expose it.
    # Adjust this path to match your project structure.
    try:
        from functions.fingerprint import fingerprint_manager
    except Exception:
        fingerprint_manager = None
        print("[WARN] Fingerprint manager not available; running in demo-safe mode.")


    def secure_dispense(
            self,
            user_id: Optional[int],
            motor_id: int,
            direction: int = 1,
        ) -> Dict[str, object]:
        """
        SECURITY WRAPPER for dispensing.
        - If fingerprint enforcement is ON, user must verify before dispensing.
        - If OFF (demo day), dispense proceeds immediately.

        Returns a unified status dict identical to dispense_slot().
        """

        # ---------------------------------------------------------
        # 1. Fingerprint check (skipped on demo day)
        # ---------------------------------------------------------
        if FINGERPRINT_REQUIRED:

            if fingerprint_manager is None:
                return {
                    "success": False,
                    "error": "Fingerprint system unavailable.",
                    "motor_id": motor_id,
                    "user_id": user_id,
                }

            ok = fingerprint_manager.verify_for_dispense(user_id=user_id)

            if not ok:
                return {
                    "success": False,
                    "error": "Fingerprint verification failed.",
                    "motor_id": motor_id,
                    "user_id": user_id,
                 }

        # ---------------------------------------------------------
        # 2. Call actual dispense logic
        # ---------------------------------------------------------
        return self.dispense_slot(
            user_id=user_id,
            motor_id=motor_id,
            direction=direction,
        )



    ###############################################################
    #  ORIGINAL DISPENSE FUNCTION (unchanged)
    ###############################################################
    def dispense_slot(
            self,
            user_id: Optional[int],
            motor_id: int,
            direction: int = 1,
        ) -> Dict[str, object]:
            """
            Dispense a single dose from the given motor/slot.

            :param user_id: ID of the user this dispense is for (can be None for demo mode)
            :param motor_id: motor number 1–6
            :param direction: +1 or -1 (normally +1 for forward dispense)
            :return: dict with status info (for logging / UI feedback)
            """

            result = {
                "success": False,
                "error": None,
                "motor_id": motor_id,
                "user_id": user_id,
            }

            if self.motor_array is None:
                result["error"] = "MotorArray not initialized (I2C unavailable)."
                return result

            try:
                self.motor_array.step_motor(
                    motor_id=motor_id,
                    direction=direction,
                    # use defaults in MotorArray: whole_steps=WHOLESTEPS_PER_CALL
                    enforce_limits=True,
                )
                result["success"] = True

            except MotorLimitReached as e:
                result["error"] = str(e)

            except Exception as e:  # catch-all for hardware errors
                result["error"] = f"Unexpected motor error: {e}"

            return result


    # ------------------------------------------------------------------
    # HOMING
    # ------------------------------------------------------------------
    def home_all_motors(self, direction: int = -1) -> Dict[int, bool]:
        """
        Home all motors (one at a time), resetting their internal call counts.
        """
        if self.motor_array is None:
            print("WARN: home_all_motors called but MotorArray is not initialized.")
            # Return False for all motors to indicate failure
            return {mid: False for mid in range(1, 7)}

        return _home_all_motors(
            motor_array=self.motor_array,
            direction=direction,
        )



    # ------------------------------------------------------------------
    # ALARMS (BUZZER + NEOPIXEL)
    # ------------------------------------------------------------------
    def trigger_alarms(self, duration: float = 30.0):
        """
        Trigger both piezo and neopixel alarms.

        NOTE: This is a blocking call. If you don't want to block Flask,
        call this from a background thread in app.py.
        """
        # Run them in sequence here; app.py can also start them in separate threads
        piezo_alarm(duration=duration)
        neopixel_alarm(duration=duration)

    def trigger_piezo_only(self, duration: float = 30.0):
        """Convenience helper for just the buzzer."""
        piezo_alarm(duration=duration)

    def trigger_neopixel_only(self, duration: float = 30.0):
        """Convenience helper for just the Neopixel."""
        neopixel_alarm(duration=duration)

    def clear_alarms(self):
        """
        Placeholder in case we later add non-blocking alarms
        that can be cancelled mid-way.
        For now, alarms run to completion.
        """
        # In future: track threads or async tasks and signal them to stop.
        pass

    # ------------------------------------------------------------------
    # FINGERPRINT (FUTURE HOOKS)
    # ------------------------------------------------------------------
    def verify_fingerprint_for_user(self, user_id: int, timeout: float = 10.0) -> bool:
        """
        Placeholder for fingerprint verification.

        app.py should call this before dispensing for real users.
        For demo mode, app.py can skip this and call dispense_slot() directly.
        """
        # TODO: integrate real fingerprint library later
        # For now, always "pass" in non-demo environments if you want to stub it.
        return True

    # ------------------------------------------------------------------
    # SHUTDOWN / CLEANUP
    # ------------------------------------------------------------------
    def shutdown(self):
        """
        Cleanly shut down hardware resources.
        Call this on app exit if needed.
        """
        try:
            self.motor_array.close()
        except Exception:
            pass


# Global singleton-style instance that app.py can import
core = CoreController()


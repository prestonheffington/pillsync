# core.py
import subprocess

def perform_dispense_simple():
    """
    Calls the existing motor script as a subprocess.
    Safe, no changes to functions/servermotor_sim.py required.
    """
    try:
        result = subprocess.run(
            ["python3", "functions/servermotor_sim.py"],
            check=True,
            capture_output=True,
            text=True
        )
        print("DEBUG[CORE]: dispense stdout ->", result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print("ERROR[CORE]: dispense stderr ->", e.stderr.strip())
        return False


def alert_due_simple(message: str | None = None):
    """
    If your LED/buzzer are also standalone scripts right now,
    call them the same safe way.
    """
    try:
        subprocess.run(["python3", "functions/LEDalert_sim.py"], check=True)
        subprocess.run(["python3", "functions/buzzer_sim.py"], check=True)
        if message:
            print("DEBUG[CORE]:", message)
    except subprocess.CalledProcessError as e:
        print("ERROR[CORE]: alert failed ->", e)

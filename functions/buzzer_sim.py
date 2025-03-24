# Import necessary libraries
import RPi.GPIO as GPIO
import time

# Set up
LED_PIN = 4  # Define GPIO pin

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(LED_PIN, GPIO.OUT)

# Callable function
def flash_led():
    GPIO.output(LED_PIN, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(LED_PIN, GPIO.LOW)  # ✅ FIXED: Now uses LED_PIN variable
    return "LED flashed"

if __name__ == "__main__":
    flash_led()
    GPIO.cleanup()  # Ensure GPIO cleanup

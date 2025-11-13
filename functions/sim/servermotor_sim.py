# Import necessary libraries
import RPi.GPIO as GPIO
import time

# Set up
LED_PIN = 5  # Ensure this matches your wiring

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(LED_PIN, GPIO.OUT)

# Callable function
def flash_led():
    try:
        GPIO.output(LED_PIN, GPIO.HIGH)  # Turn LED ON
        time.sleep(1)  # Keep it ON for 1 second
        GPIO.output(LED_PIN, GPIO.LOW)  # Turn LED OFF
        return "LED flashed successfully"
    except Exception as e:
        return f"Error: {e}"
    finally:
        GPIO.cleanup()  # Ensure proper cleanup

# Run the function if script is executed directly
if __name__ == "__main__":
    result = flash_led()
    print(result)
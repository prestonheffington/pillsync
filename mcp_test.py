import board
import busio
from adafruit_mcp230xx.mcp23017 import MCP23017

print("Starting test...")

i2c = busio.I2C(board.SCL, board.SDA)

# Wait until bus is ready
while not i2c.try_lock():
    pass

print("I2C Locked.")

try:
    expander = MCP23017(i2c, address=0x20)
    print("MCP23017 initialized successfully!")

finally:
    i2c.unlock()

#!/usr/bin/env python3
import time, argparse
from smbus2 import SMBus

# BANK=0 map
IODIRA, IODIRB = 0x00, 0x01
GPIOA,  GPIOB  = 0x12, 0x13

def scan_addrs(busnum=1):
    found=[]
    with SMBus(busnum) as bus:
        for a in range(0x20,0x28):
            try:
                bus.read_byte_data(a, IODIRA)
                found.append(a)
            except Exception:
                pass
    return found

def poke(bus, addr, reg, val):
    bus.write_i2c_block_data(addr, reg, [val & 0xFF])

def run(addr, port, hold, busnum=1):
    with SMBus(busnum) as bus:
        if port in ("A","both"):
            poke(bus, addr, IODIRA, 0x00)   # A outputs
            print(f"[0x{addr:02X}] Port A GPIOA sweep")
            for i in range(4):
                poke(bus, addr, GPIOA, 1<<i); time.sleep(hold)
            poke(bus, addr, GPIOA, 0x00)
        if port in ("B","both"):
            poke(bus, addr, IODIRB, 0x00)   # B outputs
            print(f"[0x{addr:02X}] Port B GPIOB sweep")
            for i in range(4):
                poke(bus, addr, GPIOB, 1<<i); time.sleep(hold)
            poke(bus, addr, GPIOB, 0x00)

if __name__ == "__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--addr", type=lambda x:int(x,0), help="I2C addr (0x20..0x27)")
    ap.add_argument("--port", choices=["A","B","both"], default="both")
    ap.add_argument("--hold", type=float, default=0.5)
    args=ap.parse_args()

    addrs = [args.addr] if args.addr is not None else scan_addrs()
    if not addrs:
        print("No MCP23017 found (0x20..0x27)."); exit(1)
    for a in addrs:
        run(a, args.port, args.hold)
    print("Done. If no LEDs lit, check ULN2003 5V and GND / signal column.")


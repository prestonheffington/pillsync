#!/usr/bin/env python3
import time, argparse
from smbus2 import SMBus

# MCP23017 regs (BANK=0)
IODIRA, IODIRB = 0x00, 0x01
GPIOA,  GPIOB  = 0x12, 0x13

HALFSTEP_BASE = [
    0b0001, 0b0011, 0b0010, 0b0110,
    0b0100, 0b1100, 0b1000, 0b1001,
]

def poke(bus, addr, reg, val): bus.write_i2c_block_data(addr, reg, [val & 0x0F])

def drive(bus, addr, reg, seq, steps, delay, direction=1):
    idx = 0 if direction > 0 else len(seq) - 1
    for _ in range(steps):
        poke(bus, addr, reg, seq[idx]); time.sleep(delay)
        idx = (idx + 1) % len(seq) if direction > 0 else (idx - 1) % len(seq)
    poke(bus, addr, reg, 0x00)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--addr", type=lambda x:int(x,0), default=0x20)
    ap.add_argument("--port", choices=["A","B"], default="A")
    ap.add_argument("--delay", type=float, default=0.008)
    ap.add_argument("--steps", type=int, default=256)  # small move per try
    args = ap.parse_args()

    reg = GPIOA if args.port == "A" else GPIOB
    dir_reg = IODIRA if args.port == "A" else IODIRB

    with SMBus(1) as bus:
        # outputs
        bus.write_i2c_block_data(args.addr, dir_reg, [0x00])
        seq = HALFSTEP_BASE[:]
        print(f"[addr 0x{args.addr:02X} port {args.port}] delay={args.delay}s steps={args.steps}")
        for rot in range(8):
            # rotate sequence by 'rot'
            rotated = seq[rot:]+seq[:rot]
            print(f"Try rot={rot} CW…")
            drive(bus, args.addr, reg, rotated, args.steps, args.delay, direction=1)
            time.sleep(0.5)
            print(f"Try rot={rot} CCW…")
            drive(bus, args.addr, reg, rotated, args.steps, args.delay, direction=-1)
            time.sleep(1.0)
        poke(bus, args.addr, reg, 0x00)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        with SMBus(1) as bus:
            for a in (0x20,0x21,0x22,0x23):
                for r in (GPIOA,GPIOB):
                    try: poke(bus,a,r,0x00)
                    except: pass
        print("\nInterrupted; coils off.")

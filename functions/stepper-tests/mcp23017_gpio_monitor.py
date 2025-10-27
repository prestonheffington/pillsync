
#!/usr/bin/env python3
import time, argparse, csv
from smbus2 import SMBus
GPIOA, GPIOB = 0x12, 0x13
def r(bus, a, reg): return bus.read_byte_data(a, reg) & 0xFF
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--addr", type=lambda x:int(x,0), default=0x20)
    ap.add_argument("--rate", type=float, default=0.1)
    ap.add_argument("--out", default="/tmp/mcp_gpio_log.csv")
    args = ap.parse_args()
    with SMBus(1) as bus, open(args.out,"w",newline="") as f:
        w=csv.writer(f); w.writerow(["ts","A_hex","B_hex"])
        print(f"[monitor] addr=0x{args.addr:02X} rate={args.rate}s log={args.out}")
        try:
            while True:
                t=time.time(); A=r(bus,args.addr,GPIOA); B=r(bus,args.addr,GPIOB)
                iso=time.strftime("%H:%M:%S", time.localtime(t))
                print(f"{iso} | A={A:#04x} B={B:#04x}")
                w.writerow([f"{t:.6f}", f"0x{A:02X}", f"0x{B:02X}"]); f.flush()
                time.sleep(args.rate)
        except KeyboardInterrupt:
            pass


#!/usr/bin/env python3
"""Very small load test harness (no extra deps).

This is not a full benchmark suite; it is a smoke harness to catch obvious perf regressions.
"""

import os
import time
import random
import requests

BASE = os.environ.get("LINKS_BASE_URL", "http://127.0.0.1:8000")
VILLAGE = os.environ.get("LINKS_VILLAGE_ID", "demo")

def main():
    n = int(os.environ.get("N", "200"))
    t0 = time.time()
    ok = 0
    for i in range(n):
        r = requests.get(f"{BASE}/villages/{VILLAGE}/policy/latest", timeout=5)
        if r.status_code == 200:
            ok += 1
        time.sleep(0.01 + random.random()*0.02)
    dt = time.time()-t0
    print(f"requests={n} ok={ok} seconds={dt:.2f} rps={n/dt:.1f}")

if __name__ == "__main__":
    main()

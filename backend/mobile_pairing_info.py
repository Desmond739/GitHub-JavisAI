from __future__ import annotations

import socket

from app.core.config import MOBILE_ACCESS_ENABLED, NAYA_DEVICE_TOKEN


if not MOBILE_ACCESS_ENABLED or not NAYA_DEVICE_TOKEN:
    raise SystemExit("Run Configure_Early_Access.bat first.")

address = socket.gethostbyname(socket.gethostname())
print("Open this once inside the Naya Android app:")
print(f"http://{address}:8001/app/?pair={NAYA_DEVICE_TOKEN}")
print("Keep this pairing link private.")

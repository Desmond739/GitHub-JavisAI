"""Interactive local configuration. Secrets stay on the owner's computer."""

from __future__ import annotations

import base64
import os
import secrets
from getpass import getpass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"


def current_values() -> dict[str, str]:
    values: dict[str, str] = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    return values


def ask(label: str, existing: str = "", *, secret: bool = False) -> str:
    suffix = " [already set]" if existing and secret else f" [{existing}]" if existing else ""
    value = (getpass if secret else input)(f"{label}{suffix}: ").strip()
    return value or existing


def main() -> None:
    values = current_values()
    print("Naya early-access configuration")
    print("Values are stored only in backend\\.env on this computer.\n")
    values["MOMO_MANUAL_PAYMENT_NUMBER"] = ask("Temporary MTN MoMo payment number", values.get("MOMO_MANUAL_PAYMENT_NUMBER", ""))
    values["MOMO_MANUAL_ACCOUNT_NAME"] = ask("MoMo account name", values.get("MOMO_MANUAL_ACCOUNT_NAME", ""))
    values.setdefault("PAYMENT_ADMIN_TOKEN", secrets.token_urlsafe(32))
    values["R2_ACCOUNT_ID"] = ask("Cloudflare account ID", values.get("R2_ACCOUNT_ID", ""), secret=True)
    values["R2_ACCESS_KEY_ID"] = ask("R2 access key ID", values.get("R2_ACCESS_KEY_ID", ""), secret=True)
    values["R2_SECRET_ACCESS_KEY"] = ask("R2 secret access key", values.get("R2_SECRET_ACCESS_KEY", ""), secret=True)
    values["R2_BUCKET_NAME"] = ask("R2 bucket name", values.get("R2_BUCKET_NAME", "naya-private"))
    values.setdefault("R2_ENCRYPTION_KEY", base64.urlsafe_b64encode(os.urandom(32)).decode("ascii"))
    values["MOBILE_ACCESS_ENABLED"] = "true"
    values.setdefault("NAYA_DEVICE_TOKEN", secrets.token_urlsafe(32))
    base = []
    if (ROOT / ".env.example").exists():
        base = (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
    known = set()
    output = []
    for line in base:
        if "=" in line and not line.lstrip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            known.add(key)
            output.append(f"{key}={values.get(key, line.split('=',1)[1])}")
        else:
            output.append(line)
    for key, value in values.items():
        if key not in known:
            output.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(output) + "\n", encoding="utf-8")
    try:
        os.chmod(ENV_PATH, 0o600)
    except OSError:
        pass
    print("\nEARLY ACCESS CONFIGURATION: SAVED")
    print("Do not share backend\\.env with anyone.")


if __name__ == "__main__":
    main()

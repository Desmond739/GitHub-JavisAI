"""Approve or reject a manually verified private-beta MoMo payment."""

from __future__ import annotations

import argparse
import getpass

from app.product.manual_payments import manual_payment_service


def main() -> None:
    parser = argparse.ArgumentParser(description="Review a Naya manual MoMo payment.")
    parser.add_argument("payment_id")
    parser.add_argument("decision", choices=("approve", "reject"))
    args = parser.parse_args()
    token = getpass.getpass("Payment administrator token: ")
    result = manual_payment_service.verify(args.payment_id, args.decision == "approve", token)
    print(f"PAYMENT {result['status'].upper()}: {result['payment_id']}")


if __name__ == "__main__":
    main()

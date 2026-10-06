"""Explicit Google OAuth setup for the user-assisted validation step."""

from __future__ import annotations

import argparse

from app.personal_data.google_calendar_connector import (
    google_calendar_connector,
)
from app.personal_data.google_workspace_connector import google_workspace_connector


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Authorize Naya for read-only Google Calendar, Gmail, and Drive access."
        )
    )
    parser.add_argument(
        "--authorize-read-only",
        action="store_true",
        help=(
            "Acknowledge that browser-based Google OAuth will open."
        ),
    )
    arguments = parser.parse_args()

    if not arguments.authorize_read_only:

        parser.error(
            "No authorization was started. Re-run with "
            "--authorize-read-only only after the user approves."
        )

    connectors = (("Calendar", google_calendar_connector),)

    for name, connector in connectors:

        print(f"Authorizing Google {name} read-only access...")
        connector.authenticate(
            allow_interactive=True
        )
        print(f"Google {name} read-only access authorized.")

    for service in ("gmail", "drive"):
        print(f"Authorizing Google {service.title()} read-only access...")
        google_workspace_connector.authenticate(service, allow_interactive=True)
        print(f"Google {service.title()} read-only access authorized.")

    print("Google read-only authorization is complete.")


if __name__ == "__main__":
    main()

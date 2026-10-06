from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app.personal_data.secure_file_writer import atomic_write_private_text


class GoogleWorkspaceConnector:
    """Granular Google Calendar, Gmail and Drive read-only access."""

    SCOPES = {
        "calendar": "https://www.googleapis.com/auth/calendar.readonly",
        "gmail": "https://www.googleapis.com/auth/gmail.metadata",
        "drive": "https://www.googleapis.com/auth/drive.metadata.readonly",
    }
    APIS = {"calendar": ("calendar", "v3"), "gmail": ("gmail", "v1"), "drive": ("drive", "v3")}

    def __init__(self, root: Path = Path("data/personal_data/google")) -> None:
        self.root = root
        self.credentials_path = root / "credentials.json"

    def token_path(self, service: str) -> Path:
        self._scope(service)
        return self.root / f"{service}_token.json"

    def _scope(self, service: str) -> str:
        try:
            return self.SCOPES[service]
        except KeyError as error:
            raise ValueError("Unsupported Google service.") from error

    def status(self) -> dict[str, object]:
        return {
            name: {"credentials_available": self.credentials_path.exists(),
                   "token_available": self.token_path(name).exists(), "scope": scope}
            for name, scope in self.SCOPES.items()
        }

    def authenticate(self, service: str, *, allow_interactive: bool = False) -> Credentials:
        scope = self._scope(service)
        if not self.credentials_path.exists():
            raise FileNotFoundError("Google OAuth credentials.json was not found.")
        path = self.token_path(service)
        credentials = None
        if path.exists():
            try:
                credentials = Credentials.from_authorized_user_file(str(path), [scope])
            except Exception:
                credentials = None
        if credentials and credentials.valid:
            return credentials
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            atomic_write_private_text(path, credentials.to_json(), error_label="Google OAuth token")
            return credentials
        if not allow_interactive:
            raise PermissionError("Interactive Google authorization is disabled during normal startup.")
        flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_path), [scope])
        credentials = flow.run_local_server(port=0)
        atomic_write_private_text(path, credentials.to_json(), error_label="Google OAuth token")
        return credentials

    def service(self, name: str):
        api, version = self.APIS[name]
        return build(api, version, credentials=self.authenticate(name), cache_discovery=False)

    def gmail_summary(self, limit: int = 20) -> list[dict[str, Any]]:
        api = self.service("gmail")
        listing = api.users().messages().list(userId="me", maxResults=min(max(limit, 1), 100)).execute()
        results = []
        for item in listing.get("messages", []):
            message = api.users().messages().get(
                userId="me", id=item["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            ).execute()
            headers = {h["name"].casefold(): h["value"] for h in message.get("payload", {}).get("headers", [])}
            results.append({"id": item["id"], "thread_id": message.get("threadId"),
                            "from": headers.get("from", ""), "subject": headers.get("subject", ""),
                            "date": headers.get("date", "")})
        return results

    def drive_files(self, limit: int = 50) -> list[dict[str, Any]]:
        result = self.service("drive").files().list(
            pageSize=min(max(limit, 1), 100), spaces="drive",
            fields="files(id,name,mimeType,modifiedTime,size,webViewLink)",
            orderBy="modifiedTime desc", q="trashed = false",
        ).execute()
        return list(result.get("files", []))


google_workspace_connector = GoogleWorkspaceConnector()

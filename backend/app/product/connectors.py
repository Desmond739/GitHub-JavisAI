from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ConnectorManifest:
    id: str
    name: str
    access_mode: str
    capabilities: tuple[str, ...]
    minimum_plan: str

    def public(self) -> dict[str, object]:
        result = asdict(self)
        result["capabilities"] = list(self.capabilities)
        return result


class ConnectorRegistry:
    """Allow-listed extension point; arbitrary downloaded code is never executed."""

    def __init__(self) -> None:
        self._manifests: dict[str, ConnectorManifest] = {}

    def register(self, manifest: ConnectorManifest) -> None:
        if manifest.id in self._manifests:
            raise ValueError("Connector is already registered.")
        if manifest.access_mode not in {"read_only", "confirmed_write"}:
            raise ValueError("Connector access mode is invalid.")
        self._manifests[manifest.id] = manifest

    def list(self) -> list[dict[str, object]]:
        return [manifest.public() for manifest in self._manifests.values()]


connector_registry = ConnectorRegistry()
connector_registry.register(ConnectorManifest(
    "google_calendar", "Google Calendar", "read_only", ("events", "calendars"), "plus"
))
connector_registry.register(ConnectorManifest(
    "gmail", "Gmail", "read_only", ("message_metadata",), "plus"
))
connector_registry.register(ConnectorManifest(
    "google_drive", "Google Drive", "read_only", ("file_metadata",), "plus"
))

from enum import Enum


class PermissionLevel(str, Enum):
    ALLOW = "allow"
    CONFIRM = "confirm"
    DENY = "deny"
    MANUAL = "manual"


class PermissionManager:

    def __init__(self):

        self.permissions = {
            "read_notes": PermissionLevel.ALLOW,
            "read_projects": PermissionLevel.ALLOW,
            "search_internet": PermissionLevel.ALLOW,
            "create_document": PermissionLevel.ALLOW,

            "check_calendar": PermissionLevel.ALLOW,
            "check_tasks": PermissionLevel.ALLOW,
            "review_goals": PermissionLevel.ALLOW,
            "generate_daily_briefing": PermissionLevel.ALLOW,
            "speak_daily_briefing": PermissionLevel.ALLOW,

            "send_email": PermissionLevel.CONFIRM,
            "create_calendar_event": PermissionLevel.CONFIRM,
            "edit_calendar_event": PermissionLevel.CONFIRM,
            "upload_drive_file": PermissionLevel.CONFIRM,
            "run_local_app_action": PermissionLevel.CONFIRM,
            "delete_file": PermissionLevel.CONFIRM,

            "transfer_money": PermissionLevel.MANUAL,
            "purchase_subscription": PermissionLevel.MANUAL,
            "change_password": PermissionLevel.DENY,
            "execute_unknown_program": PermissionLevel.DENY,
        }

    def get_permission(self, action: str) -> PermissionLevel:

        return self.permissions.get(
            action,
            PermissionLevel.DENY
        )

    def is_allowed(self, action: str) -> bool:

        return self.get_permission(action) == PermissionLevel.ALLOW

    def requires_confirmation(self, action: str) -> bool:

        return self.get_permission(action) == PermissionLevel.CONFIRM

    def is_denied(self, action: str) -> bool:

        return self.get_permission(action) == PermissionLevel.DENY

    def requires_manual_action(self, action: str) -> bool:

        return self.get_permission(action) == PermissionLevel.MANUAL

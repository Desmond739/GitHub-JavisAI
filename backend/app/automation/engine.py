from app.automation.models import Workflow
from app.security.permission_manager import PermissionManager
from app.automation.action_registry import action_registry
from app.core.logging_config import log_event


class AutomationEngine:

    def __init__(self):

        self.workflows: dict[str, Workflow] = {}

        self.permission_manager = PermissionManager()

    def register_workflow(
        self,
        workflow: Workflow
    ) -> None:

        self.workflows[workflow.name] = workflow

    def get_workflow(
        self,
        name: str
    ) -> Workflow | None:

        return self.workflows.get(name)

    def list_workflows(self) -> list[str]:

        return list(self.workflows.keys())

    def execute_action(
        self,
        action_name: str
    ) -> str:

        permission = (
            self.permission_manager
            .get_permission(action_name)
        )

        if self.permission_manager.is_denied(
            action_name
        ):

            return (
                f"DENIED: {action_name}"
            )

        if self.permission_manager.requires_confirmation(
            action_name
        ):

            return (
                f"CONFIRMATION REQUIRED: {action_name}"
            )

        if self.permission_manager.requires_manual_action(
            action_name
        ):

            return (
                f"MANUAL ACTION REQUIRED: {action_name}"
            )

        action = action_registry.get(
            action_name
        )

        if action is None:

            return (
                f"UNAVAILABLE: "
                f"{action_name}"
            )

        try:

            result = action()

            return str(result)

        except Exception as error:

            error_type = type(error).__name__
            log_event(
                "automation_action_failed",
                level=40,
                component="automation",
                error_type=error_type,
                status="failed",
            )

            return (
                f"Action failed: {action_name} "
                f"({error_type})"
            )

    def run_workflow(
        self,
        name: str
    ) -> list[str]:

        workflow = self.get_workflow(name)

        if workflow is None:

            raise ValueError(
                f"Workflow '{name}' does not exist."
            )

        results = []

        for action in workflow.actions:

            results.append(
                self.execute_action(
                    action.name
                )
            )

        return results


automation_engine = AutomationEngine()

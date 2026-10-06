from __future__ import annotations

import re

from datetime import (
    date,
    datetime,
    timedelta,
)

from typing import Callable

from app.personal_data.personal_data_model import (
    PersonalDataRecord,
)

from app.personal_data.task_service import (
    TaskService,
    task_service,
)


WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


class TaskQueryEngine:

    def __init__(
        self,
        service: TaskService | None = None,
        now_provider:
        Callable[[], datetime] | None = None,
    ) -> None:

        self.service = (
            service
            if service is not None
            else task_service
        )

        self._now_provider = (
            now_provider
            if now_provider is not None
            else lambda: datetime.now().astimezone()
        )

    # ============================================================
    # TIME
    # ============================================================

    def _now(
        self,
    ) -> datetime:

        value = self._now_provider()

        if not isinstance(
            value,
            datetime,
        ):

            raise TypeError(
                "now_provider must return "
                "a datetime."
            )

        if value.tzinfo is None:

            local_timezone = (
                datetime.now()
                .astimezone()
                .tzinfo
            )

            value = value.replace(
                tzinfo=local_timezone
            )

        return value

    def _parse_datetime(
        self,
        value: str | None,
    ) -> datetime | None:

        if not value:

            return None

        cleaned = (
            str(value)
            .strip()
        )

        if not cleaned:

            return None

        try:

            parsed = datetime.fromisoformat(
                cleaned.replace(
                    "Z",
                    "+00:00",
                )
            )

        except ValueError:

            return None

        now = self._now()

        if parsed.tzinfo is None:

            parsed = parsed.replace(
                tzinfo=now.tzinfo
            )

        return parsed.astimezone(
            now.tzinfo
        )

    # ============================================================
    # SOURCE
    # ============================================================

    def has_active_source(
        self,
    ) -> bool:

        sources = (
            self.service.manager
            .list_sources()
        )

        for source in sources:

            if (
                source.source_type
                in {
                    "task",
                    "reminder",
                }
                and source.status
                == "active"
            ):

                return True

        return False

    # ============================================================
    # TASK COLLECTIONS
    # ============================================================

    def open_tasks(
        self,
    ) -> list[PersonalDataRecord]:

        records = self.service.list_tasks(
            record_type="task",
            active_only=True,
        )

        return [
            record
            for record in records
            if (
                record.attributes.get(
                    "task_status"
                )
                in {
                    "pending",
                    "in_progress",
                }
            )
        ]

    def completed_tasks(
        self,
    ) -> list[PersonalDataRecord]:

        return self.service.list_tasks(
            record_type="task",
            active_only=True,
            task_status="completed",
        )

    def reminders(
        self,
    ) -> list[PersonalDataRecord]:

        records = self.service.list_tasks(
            record_type="reminder",
            active_only=True,
        )

        return [
            record
            for record in records
            if (
                record.attributes.get(
                    "task_status"
                )
                not in {
                    "completed",
                    "cancelled",
                }
            )
        ]

    def urgent_tasks(
        self,
    ) -> list[PersonalDataRecord]:

        return [
            record
            for record in self.open_tasks()
            if (
                record.attributes.get(
                    "priority"
                )
                == "urgent"
            )
        ]

    # ============================================================
    # DATE FILTERING
    # ============================================================

    def due_on(
        self,
        target_date: date,
    ) -> list[PersonalDataRecord]:

        results = []

        for task in self.open_tasks():

            due = self._parse_datetime(
                task.attributes.get(
                    "due_at"
                )
            )

            if (
                due is not None
                and due.date()
                == target_date
            ):

                results.append(
                    task
                )

        return self._sort_by_due(
            results
        )

    def reminders_on(
        self,
        target_date: date,
    ) -> list[PersonalDataRecord]:

        results = []

        for reminder in self.reminders():

            reminder_at = (
                self._parse_datetime(
                    reminder.attributes.get(
                        "reminder_at"
                    )
                )
            )

            if (
                reminder_at is not None
                and reminder_at.date()
                == target_date
            ):

                results.append(
                    reminder
                )

        return self._sort_by_reminder(
            results
        )

    def overdue_tasks(
        self,
    ) -> list[PersonalDataRecord]:

        now = self._now()

        results = []

        for task in self.open_tasks():

            due = self._parse_datetime(
                task.attributes.get(
                    "due_at"
                )
            )

            if (
                due is not None
                and due < now
            ):

                results.append(
                    task
                )

        return self._sort_by_due(
            results
        )

    def due_between(
        self,
        start_date: date,
        end_date: date,
    ) -> list[PersonalDataRecord]:

        results = []

        for task in self.open_tasks():

            due = self._parse_datetime(
                task.attributes.get(
                    "due_at"
                )
            )

            if due is None:

                continue

            if (
                start_date
                <= due.date()
                <= end_date
            ):

                results.append(
                    task
                )

        return self._sort_by_due(
            results
        )

    # ============================================================
    # SORTING
    # ============================================================

    def _sort_by_due(
        self,
        records:
        list[PersonalDataRecord],
    ) -> list[PersonalDataRecord]:

        maximum = datetime.max.replace(
            tzinfo=self._now().tzinfo
        )

        return sorted(
            records,
            key=lambda record: (
                self._parse_datetime(
                    record.attributes.get(
                        "due_at"
                    )
                )
                or maximum
            ),
        )

    def _sort_by_reminder(
        self,
        records:
        list[PersonalDataRecord],
    ) -> list[PersonalDataRecord]:

        maximum = datetime.max.replace(
            tzinfo=self._now().tzinfo
        )

        return sorted(
            records,
            key=lambda record: (
                self._parse_datetime(
                    record.attributes.get(
                        "reminder_at"
                    )
                )
                or maximum
            ),
        )

    # ============================================================
    # NATURAL-LANGUAGE DATE
    # ============================================================

    def resolve_date(
        self,
        request: str,
    ) -> date | None:

        normalized = (
            request.strip()
            .casefold()
        )

        today = self._now().date()

        if "tomorrow" in normalized:

            return (
                today
                + timedelta(
                    days=1
                )
            )

        if "today" in normalized:

            return today

        iso_match = re.search(
            r"\b"
            r"(\d{4}-\d{2}-\d{2})"
            r"\b",
            normalized,
        )

        if iso_match:

            try:

                return date.fromisoformat(
                    iso_match.group(1)
                )

            except ValueError:

                return None

        for name, weekday in (
            WEEKDAYS.items()
        ):

            if name not in normalized:

                continue

            days_ahead = (
                weekday
                - today.weekday()
            ) % 7

            if (
                f"next {name}"
                in normalized
                and days_ahead == 0
            ):

                days_ahead = 7

            return (
                today
                + timedelta(
                    days=days_ahead
                )
            )

        return None

    # ============================================================
    # INTENT
    # ============================================================

    def can_answer(
        self,
        request: str,
    ) -> bool:

        if (
            not request
            or not request.strip()
        ):

            return False

        normalized = (
            request.strip()
            .casefold()
        )

        # Commands such as:
        #
        # "Remind me to..."
        #
        # are intentionally NOT handled here.
        # This engine is read-only.
        if normalized.startswith(
            "remind me to "
        ):

            return False

        patterns = [
            "what tasks do i have",
            "what task do i have",
            "show my tasks",
            "show me my tasks",
            "my tasks",
            "task list",
            "to-do list",
            "todo list",
            "what is due",
            "what's due",
            "what are my urgent tasks",
            "urgent tasks",
            "overdue tasks",
            "tasks are overdue",
            "what have i completed",
            "completed tasks",
            "what reminders do i have",
            "show my reminders",
            "show me my reminders",
            "my reminders",
            "any reminders",
        ]

        if any(
            pattern in normalized
            for pattern in patterns
        ):

            return True

        if (
            "task" in normalized
            and any(
                word in normalized
                for word in {
                    "today",
                    "tomorrow",
                    "due",
                    "urgent",
                    "overdue",
                    "completed",
                }
            )
        ):

            return True

        if (
            "reminder" in normalized
            and any(
                phrase in normalized
                for phrase in {
                    "what",
                    "show",
                    "today",
                    "tomorrow",
                    "have",
                }
            )
        ):

            return True

        return False

    # ============================================================
    # FORMATTING
    # ============================================================

    def _format_datetime(
        self,
        value: str | None,
    ) -> str:

        parsed = self._parse_datetime(
            value
        )

        if parsed is None:

            return ""

        return parsed.strftime(
            "%A, %d %B %Y at %H:%M"
        )

    def _format_task(
        self,
        task: PersonalDataRecord,
    ) -> str:

        details = [
            task.title
        ]

        due_text = self._format_datetime(
            task.attributes.get(
                "due_at"
            )
        )

        if due_text:

            details.append(
                f"due {due_text}"
            )

        priority = task.attributes.get(
            "priority"
        )

        if (
            priority
            and priority != "normal"
        ):

            details.append(
                f"{priority} priority"
            )

        return " — ".join(
            details
        )

    def _format_reminder(
        self,
        reminder:
        PersonalDataRecord,
    ) -> str:

        details = [
            reminder.title
        ]

        reminder_text = (
            self._format_datetime(
                reminder.attributes.get(
                    "reminder_at"
                )
            )
        )

        if reminder_text:

            details.append(
                reminder_text
            )

        return " — ".join(
            details
        )

    @staticmethod
    def _join_records(
        records:
        list[PersonalDataRecord],
        formatter,
    ) -> str:

        return "; ".join(
            formatter(record)
            for record in records
        )

    # ============================================================
    # ANSWER
    # ============================================================

    def answer(
        self,
        request: str,
    ) -> str | None:

        if not self.can_answer(
            request
        ):

            return None

        if not self.has_active_source():

            return (
                "You do not have an active "
                "task or reminder source yet."
            )

        normalized = (
            request.strip()
            .casefold()
        )

        target_date = self.resolve_date(
            request
        )

        # --------------------------------------------------------
        # REMINDERS
        # --------------------------------------------------------

        if "reminder" in normalized:

            if target_date is not None:

                records = self.reminders_on(
                    target_date
                )

                if not records:

                    return (
                        "You have no reminders "
                        f"for {target_date.strftime('%A, %d %B %Y')}."
                    )

                return (
                    f"You have {len(records)} "
                    f"reminder"
                    f"{'' if len(records) == 1 else 's'} "
                    f"for "
                    f"{target_date.strftime('%A, %d %B %Y')}: "
                    + self._join_records(
                        records,
                        self._format_reminder,
                    )
                    + "."
                )

            records = self.reminders()

            if not records:

                return (
                    "You have no active reminders."
                )

            return (
                f"You have {len(records)} active "
                f"reminder"
                f"{'' if len(records) == 1 else 's'}: "
                + self._join_records(
                    records,
                    self._format_reminder,
                )
                + "."
            )

        # --------------------------------------------------------
        # COMPLETED
        # --------------------------------------------------------

        if "completed" in normalized:

            records = self.completed_tasks()

            if not records:

                return (
                    "You have no completed tasks."
                )

            return (
                f"You have {len(records)} completed "
                f"task"
                f"{'' if len(records) == 1 else 's'}: "
                + self._join_records(
                    records,
                    self._format_task,
                )
                + "."
            )

        # --------------------------------------------------------
        # OVERDUE
        # --------------------------------------------------------

        if "overdue" in normalized:

            records = self.overdue_tasks()

            if not records:

                return (
                    "You have no overdue tasks."
                )

            return (
                f"You have {len(records)} overdue "
                f"task"
                f"{'' if len(records) == 1 else 's'}: "
                + self._join_records(
                    records,
                    self._format_task,
                )
                + "."
            )

        # --------------------------------------------------------
        # URGENT
        # --------------------------------------------------------

        if "urgent" in normalized:

            records = self.urgent_tasks()

            if not records:

                return (
                    "You have no urgent tasks."
                )

            return (
                f"You have {len(records)} urgent "
                f"task"
                f"{'' if len(records) == 1 else 's'}: "
                + self._join_records(
                    records,
                    self._format_task,
                )
                + "."
            )

        # --------------------------------------------------------
        # THIS WEEK
        # --------------------------------------------------------

        if (
            "due" in normalized
            and "this week" in normalized
        ):

            today = self._now().date()

            end = (
                today
                + timedelta(
                    days=(
                        6
                        - today.weekday()
                    )
                )
            )

            records = self.due_between(
                today,
                end,
            )

            if not records:

                return (
                    "You have no open tasks "
                    "due this week."
                )

            return (
                f"You have {len(records)} "
                f"task"
                f"{'' if len(records) == 1 else 's'} "
                f"due this week: "
                + self._join_records(
                    records,
                    self._format_task,
                )
                + "."
            )

        # --------------------------------------------------------
        # DATE-SPECIFIC DUE TASKS
        # --------------------------------------------------------

        if target_date is not None:

            records = self.due_on(
                target_date
            )

            if not records:

                return (
                    "You have no open tasks due "
                    f"{target_date.strftime('%A, %d %B %Y')}."
                )

            return (
                f"You have {len(records)} "
                f"task"
                f"{'' if len(records) == 1 else 's'} "
                f"due "
                f"{target_date.strftime('%A, %d %B %Y')}: "
                + self._join_records(
                    records,
                    self._format_task,
                )
                + "."
            )

        # --------------------------------------------------------
        # ALL OPEN TASKS
        # --------------------------------------------------------

        records = self._sort_by_due(
            self.open_tasks()
        )

        if not records:

            return (
                "You have no open tasks."
            )

        return (
            f"You have {len(records)} open "
            f"task"
            f"{'' if len(records) == 1 else 's'}: "
            + self._join_records(
                records,
                self._format_task,
            )
            + "."
        )


task_query_engine = TaskQueryEngine()
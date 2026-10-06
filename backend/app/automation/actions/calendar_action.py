from app.personal_data.calendar_query_engine import (
    CalendarQueryEngine,
    calendar_query_engine,
)


class CalendarAction:

    def __init__(
        self,
        query_engine: CalendarQueryEngine | None = None,
    ) -> None:

        self.query_engine = (
            query_engine
            if query_engine is not None
            else calendar_query_engine
        )

    def read_today(self) -> str:

        return (
            self.query_engine.answer(
                "What is my schedule today?"
            )
            or "No calendar summary is available."
        )


calendar_action = CalendarAction()

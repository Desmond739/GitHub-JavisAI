from __future__ import annotations

from datetime import datetime

from app.product.store import platform_store


class SuggestionService:
    """Conservative, explainable suggestions derived from owner-approved context."""

    def create(self, title: str, body: str, reason: str, user_id: str | None = None) -> dict[str, str]:
        suggestion_id = platform_store.insert("suggestions", {
            "title": title, "body": body, "reason": reason, "status": "new",
            "user_id": user_id,
        })
        return {"id": suggestion_id, "status": "new"}

    def daily_check_in(self) -> dict[str, str]:
        today = datetime.now().date().isoformat()
        with platform_store.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM suggestions WHERE title IN ('Plan your day','Review today''s priorities') "
                "AND substr(created_at,1,10)=? LIMIT 1", (today,),
            ).fetchone()
        if existing is not None:
            return {"id": str(existing["id"]), "status": "already_created"}
        hour = datetime.now().hour
        title = "Plan your day" if hour < 12 else "Review today's priorities"
        body = "Review your calendar and choose the three outcomes that matter most."
        return self.create(title, body, "Daily planning is enabled; no private content was inferred.")


suggestion_service = SuggestionService()

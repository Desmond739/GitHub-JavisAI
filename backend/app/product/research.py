"""Trusted research routing with topic-specific official-source preference."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

from app.core.config import BRAVE_SEARCH_API_KEY
from app.services.ai_service import generate_response


OFFICIAL_SOURCES = {
    "football": ("fifa.com", "uefa.com", "cafonline.com"),
    "anime": ("crunchyroll.com", "aniplex.co.jp", "toei-anim.co.jp", "shonenjump.com"),
    "health": ("who.int", "cdc.gov"),
    "software": ("docs.python.org", "developer.android.com", "learn.microsoft.com"),
    "finance": ("imf.org", "worldbank.org", "beac.int"),
}


def _topic(question: str) -> str:
    text = question.casefold()
    if any(word in text for word in ("football", "soccer", "fifa", "match", "league")): return "football"
    if any(word in text for word in ("anime", "manga", "episode", "season")): return "anime"
    if any(word in text for word in ("health", "medicine", "symptom", "disease")): return "health"
    if any(word in text for word in ("code", "python", "android", "windows", "software")): return "software"
    if any(word in text for word in ("money", "economy", "bank", "xaf", "finance")): return "finance"
    return "general"


class ResearchService:
    def status(self) -> dict[str, object]:
        return {"configured": bool(BRAVE_SEARCH_API_KEY), "provider": "Brave Search",
                "official_source_topics": sorted(OFFICIAL_SOURCES)}

    def answer(self, question: str) -> dict[str, object]:
        if not BRAVE_SEARCH_API_KEY:
            raise RuntimeError("Web research is not configured.")
        topic = _topic(question)
        domains = OFFICIAL_SOURCES.get(topic, ())
        domain_filter = " OR ".join(f"site:{domain}" for domain in domains)
        query = f"{question} ({domain_filter})" if domain_filter else question
        url = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode({"q": query, "count": 6})
        request = urllib.request.Request(url, headers={"Accept": "application/json", "X-Subscription-Token": BRAVE_SEARCH_API_KEY})
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read())
        results = payload.get("web", {}).get("results", [])[:6]
        sources = [{"title": item.get("title", ""), "url": item.get("url", ""),
                    "description": item.get("description", "")} for item in results]
        evidence = "\n".join(f"[{i+1}] {s['title']} — {s['description']} — {s['url']}" for i, s in enumerate(sources))
        answer = generate_response(
            "Answer using only the evidence below. If evidence is insufficient, say so. "
            "Cite source numbers in brackets and do not invent facts.\n\nQuestion: " + question + "\n\nEvidence:\n" + evidence,
            max_tokens=500,
        )
        return {"answer": answer, "topic": topic, "sources": sources,
                "source_policy": "official-first" if domains else "reputable-source"}


research_service = ResearchService()

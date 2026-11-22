"""Web search (DuckDuckGo, no key needed) with a clearly labelled sample-data fallback
that is ONLY used for the example Nepal food-delivery query."""
import re

from models import Source

SAMPLE_NOTICE = "SAMPLE DATA (illustrative only, not live research)"

SAMPLE_RESULTS = [
    Source(
        title=f"{SAMPLE_NOTICE}: market overview",
        snippet="Online food delivery in Nepal is concentrated in Kathmandu Valley and other cities. "
        "Foodmandu and Pathao Food are commonly cited players. Verify all details independently.",
    ),
    Source(
        title=f"{SAMPLE_NOTICE}: challenges",
        snippet="Typical challenges for delivery platforms include rider costs, traffic, "
        "thin margins and customer retention.",
    ),
]

MAX_TOTAL_RESULTS = 12


def _topic(query: str) -> str:
    """'Analyze the food delivery market in Nepal' -> 'food delivery market in Nepal'"""
    t = re.sub(
        r"^(please\s+)?(analy[sz]e|research|tell me about|give me)\s+(the\s+)?",
        "",
        query.strip(),
        flags=re.I,
    )
    return t.rstrip(".?! ")


def _sample_matches(query: str) -> bool:
    q = query.lower()
    return "food" in q and "deliver" in q and "nepal" in q


def web_search(query: str, max_results: int = 5) -> tuple[list[Source], str, str]:
    """Return (results, origin, error). origin is 'web', 'sample' or 'none'."""
    results: list[Source] = []
    errors: list[str] = []

    try:
        from ddgs import DDGS
    except Exception as e: 
        DDGS = None
        errors.append(f"ddgs is not installed correctly: {e}")

    topic = _topic(query)
    queries = [
        f"{topic} market size growth",
        f"best {topic} apps platforms companies",
        f"{topic} leading brands news",
    ]
    if DDGS:
        for q in queries:
            try:
                for r in DDGS().text(q, max_results=max_results):
                    url = r.get("href", "")
                    if url and all(url != s.url for s in results):
                        results.append(
                            Source(title=r.get("title", ""), url=url, snippet=r.get("body", ""))
                        )
            except Exception as e:  
                errors.append(str(e)[:200])

    if results:
        return results[:MAX_TOTAL_RESULTS], "web", ""
    if _sample_matches(query):
        return SAMPLE_RESULTS, "sample", "; ".join(errors)
    return [], "none", "; ".join(errors) or "the search returned zero results"
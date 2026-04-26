"""Workflow-level helpers for query activity and report handoff."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, MutableMapping

from modules.database import execute_query, execute_update


PINNED_INSIGHTS_KEY = "pinned_report_insights"


def pin_insight(
    state: MutableMapping,
    question: str,
    answer: str,
    source: str = "Query",
    username: str | None = None,
) -> None:
    """Store a query answer for later report drafting."""
    insights = list(state.get(PINNED_INSIGHTS_KEY, []))
    insight = {
        "question": question,
        "answer": answer,
        "source": source,
    }
    if username:
        insight["username"] = username
        insight["id"] = persist_insight(username, question, answer, source)
    insights.append(insight)
    state[PINNED_INSIGHTS_KEY] = insights[-20:]


def clear_pinned_insights(state: MutableMapping, username: str | None = None) -> None:
    """Remove all pinned report insights."""
    state.pop(PINNED_INSIGHTS_KEY, None)
    if username:
        execute_update("DELETE FROM pinned_insights WHERE username = ?", (username,))


def get_pinned_insights(state: MutableMapping) -> List[Dict[str, str]]:
    """Return pinned insights from session state."""
    return list(state.get(PINNED_INSIGHTS_KEY, []))


def persist_insight(username: str, question: str, answer: str, source: str = "Query") -> int:
    """Persist a pinned insight and return its row ID."""
    return execute_update(
        """
        INSERT INTO pinned_insights (username, question, answer, source)
        VALUES (?, ?, ?, ?)
        """,
        (username, question, answer, source),
    )


def delete_pinned_insight(insight_id: int, username: str | None = None) -> None:
    """Delete one pinned insight."""
    if username:
        execute_update(
            "DELETE FROM pinned_insights WHERE id = ? AND username = ?",
            (insight_id, username),
        )
    else:
        execute_update("DELETE FROM pinned_insights WHERE id = ?", (insight_id,))


def load_pinned_insights(username: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Load recent pinned insights for a user from SQLite."""
    rows = execute_query(
        """
        SELECT id, username, question, answer, source, created_at
        FROM pinned_insights
        WHERE username = ?
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (username, limit),
    )
    return list(reversed(rows))


def sync_session_insights(state: MutableMapping, username: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Load persistent insights into session state when none are present."""
    if not state.get(PINNED_INSIGHTS_KEY):
        state[PINNED_INSIGHTS_KEY] = load_pinned_insights(username, limit=limit)
    return get_pinned_insights(state)


def get_recent_query_logs(limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch recent RAG query logs from SQLite."""
    return execute_query(
        """
        SELECT id, question, answer, confidence, timestamp, processing_time_ms
        FROM query_logs
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (limit,),
    )


def log_query_activity(
    question: str,
    answer: str,
    confidence: float,
    citations: str = "[]",
    session_id: str | None = None,
    processing_time_ms: int = 0,
) -> int:
    """Record a query answer in the shared activity log."""
    return execute_update(
        """
        INSERT INTO query_logs (question, answer, confidence, citations, session_id, processing_time_ms)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (question, answer, confidence, citations, session_id, processing_time_ms),
    )


def query_activity_summary(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize recent query activity."""
    row_list = list(rows)
    if not row_list:
        return {
            "count": 0,
            "average_confidence": None,
            "average_processing_ms": None,
            "low_confidence_count": 0,
        }

    confidences = [row["confidence"] for row in row_list if row.get("confidence") is not None]
    timings = [row["processing_time_ms"] for row in row_list if row.get("processing_time_ms") is not None]
    return {
        "count": len(row_list),
        "average_confidence": sum(confidences) / len(confidences) if confidences else None,
        "average_processing_ms": sum(timings) / len(timings) if timings else None,
        "low_confidence_count": sum(1 for confidence in confidences if confidence < 0.35),
    }


def format_insights_for_report(insights: Iterable[Dict[str, str]]) -> str:
    """Create a markdown block from pinned insights."""
    lines = []
    for idx, insight in enumerate(insights, 1):
        lines.append(f"### Pinned Insight {idx}")
        lines.append(f"**Question:** {insight.get('question', '')}")
        lines.append("")
        lines.append(insight.get("answer", ""))
        lines.append("")
    return "\n".join(lines).strip()

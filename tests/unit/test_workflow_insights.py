from modules import workflow_insights


def test_pin_and_clear_insights():
    state = {}

    workflow_insights.pin_insight(state, "Question?", "Answer.")

    insights = workflow_insights.get_pinned_insights(state)
    assert len(insights) == 1
    assert insights[0]["question"] == "Question?"
    assert insights[0]["answer"] == "Answer."

    workflow_insights.clear_pinned_insights(state)

    assert workflow_insights.get_pinned_insights(state) == []


def test_pinned_insights_keep_recent_twenty():
    state = {}

    for idx in range(25):
        workflow_insights.pin_insight(state, f"Q{idx}", f"A{idx}")

    insights = workflow_insights.get_pinned_insights(state)
    assert len(insights) == 20
    assert insights[0]["question"] == "Q5"
    assert insights[-1]["question"] == "Q24"


def test_query_activity_summary_handles_empty_rows():
    summary = workflow_insights.query_activity_summary([])

    assert summary["count"] == 0
    assert summary["average_confidence"] is None
    assert summary["low_confidence_count"] == 0


def test_query_activity_summary_calculates_metrics():
    rows = [
        {"confidence": 0.2, "processing_time_ms": 100},
        {"confidence": 0.8, "processing_time_ms": 300},
    ]

    summary = workflow_insights.query_activity_summary(rows)

    assert summary["count"] == 2
    assert summary["average_confidence"] == 0.5
    assert summary["average_processing_ms"] == 200
    assert summary["low_confidence_count"] == 1


def test_format_insights_for_report_creates_markdown():
    text = workflow_insights.format_insights_for_report(
        [{"question": "What matters?", "answer": "Access and staffing."}]
    )

    assert "Pinned Insight 1" in text
    assert "**Question:** What matters?" in text
    assert "Access and staffing." in text


def test_pin_insight_persists_when_username_present(monkeypatch):
    calls = []

    def fake_persist(username, question, answer, source="Query"):
        calls.append((username, question, answer, source))
        return 42

    monkeypatch.setattr(workflow_insights, "persist_insight", fake_persist)
    state = {}

    workflow_insights.pin_insight(
        state,
        "What matters?",
        "Access.",
        username="admin",
    )

    assert calls == [("admin", "What matters?", "Access.", "Query")]
    assert state[workflow_insights.PINNED_INSIGHTS_KEY][0]["id"] == 42


def test_load_pinned_insights_reverses_descending_db_rows(monkeypatch):
    monkeypatch.setattr(
        workflow_insights,
        "execute_query",
        lambda query, params: [
            {"id": 2, "question": "newer"},
            {"id": 1, "question": "older"},
        ],
    )

    rows = workflow_insights.load_pinned_insights("admin")

    assert [row["question"] for row in rows] == ["older", "newer"]


def test_delete_pinned_insight_scopes_by_username(monkeypatch):
    calls = []
    monkeypatch.setattr(
        workflow_insights,
        "execute_update",
        lambda query, params: calls.append((query, params)),
    )

    workflow_insights.delete_pinned_insight(7, username="admin")

    assert "username" in calls[0][0]
    assert calls[0][1] == (7, "admin")


def test_log_query_activity_records_profile_native_answers(monkeypatch):
    calls = []
    monkeypatch.setattr(
        workflow_insights,
        "execute_update",
        lambda query, params: calls.append((query, params)) or 99,
    )

    row_id = workflow_insights.log_query_activity(
        "What data do I have?",
        "Survey data is available.",
        1.0,
        session_id="session-1",
    )

    assert row_id == 99
    assert "INSERT INTO query_logs" in calls[0][0]
    assert calls[0][1] == (
        "What data do I have?",
        "Survey data is available.",
        1.0,
        "[]",
        "session-1",
        0,
    )

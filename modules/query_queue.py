"""Small state helpers for suggested questions queued into the query page."""

from __future__ import annotations

from typing import MutableMapping, Optional


PENDING_QUERY_KEY = "pending_query_prompt"
RUN_PENDING_QUERY_KEY = "run_pending_query"


def queue_question(state: MutableMapping, question: str) -> None:
    """Queue a suggested question without executing it."""
    cleaned_question = question.strip()
    if not cleaned_question:
        clear_pending_question(state)
        return
    state[PENDING_QUERY_KEY] = cleaned_question
    state[RUN_PENDING_QUERY_KEY] = False


def update_pending_question(state: MutableMapping, question: str) -> None:
    """Edit the queued question text."""
    cleaned_question = question.strip()
    if not cleaned_question:
        clear_pending_question(state)
        return
    state[PENDING_QUERY_KEY] = cleaned_question
    state[RUN_PENDING_QUERY_KEY] = False


def mark_pending_for_run(state: MutableMapping) -> bool:
    """Mark the current pending question to run on this render."""
    if not state.get(PENDING_QUERY_KEY):
        return False
    state[RUN_PENDING_QUERY_KEY] = True
    return True


def clear_pending_question(state: MutableMapping) -> None:
    """Clear pending question state."""
    state.pop(PENDING_QUERY_KEY, None)
    state.pop(RUN_PENDING_QUERY_KEY, None)


def consume_runnable_question(state: MutableMapping) -> Optional[str]:
    """Return and clear the pending question only when the user chose Run."""
    if not state.get(RUN_PENDING_QUERY_KEY):
        return None
    question = state.get(PENDING_QUERY_KEY)
    clear_pending_question(state)
    return question

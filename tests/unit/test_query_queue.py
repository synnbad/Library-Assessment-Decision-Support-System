from modules import query_queue


def test_queue_question_does_not_mark_for_run():
    state = {}

    query_queue.queue_question(state, "What are the main themes?")

    assert state[query_queue.PENDING_QUERY_KEY] == "What are the main themes?"
    assert state[query_queue.RUN_PENDING_QUERY_KEY] is False
    assert query_queue.consume_runnable_question(state) is None


def test_mark_pending_for_run_consumes_and_clears_question():
    state = {}
    query_queue.queue_question(state, "Show representative quotes.")

    assert query_queue.mark_pending_for_run(state) is True
    assert query_queue.consume_runnable_question(state) == "Show representative quotes."
    assert query_queue.PENDING_QUERY_KEY not in state
    assert query_queue.RUN_PENDING_QUERY_KEY not in state


def test_mark_pending_for_run_without_question_returns_false():
    state = {}

    assert query_queue.mark_pending_for_run(state) is False
    assert query_queue.consume_runnable_question(state) is None


def test_update_pending_question_keeps_it_from_auto_running():
    state = {}
    query_queue.queue_question(state, "Original")
    query_queue.mark_pending_for_run(state)

    query_queue.update_pending_question(state, "Edited")

    assert state[query_queue.PENDING_QUERY_KEY] == "Edited"
    assert state[query_queue.RUN_PENDING_QUERY_KEY] is False


def test_queue_question_trims_whitespace():
    state = {}

    query_queue.queue_question(state, "  What changed?  ")

    assert state[query_queue.PENDING_QUERY_KEY] == "What changed?"


def test_blank_question_clears_pending_state():
    state = {}
    query_queue.queue_question(state, "Original")

    query_queue.update_pending_question(state, "   ")

    assert query_queue.PENDING_QUERY_KEY not in state
    assert query_queue.RUN_PENDING_QUERY_KEY not in state

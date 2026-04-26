"""Reusable Streamlit helpers for dataset-aware guidance."""

import streamlit as st

from modules import csv_handler, query_intelligence
from modules import query_queue


def build_profile(dataset, n_rows: int = 1000):
    """Build a query intelligence profile for a stored dataset."""
    preview_df = csv_handler.get_preview(dataset["id"], n_rows=n_rows)
    if preview_df.empty:
        return None
    return query_intelligence.build_profile_from_dataset_record(dataset, preview_df)


def display_profile_summary(profile, compact: bool = True):
    """Show a short dataset brief with strengths and warnings."""
    if profile is None:
        return

    st.markdown(query_intelligence.generate_dataset_brief(profile))
    if not compact and profile.strengths:
        for strength in profile.strengths:
            st.success(strength)
    if profile.warnings:
        with st.expander("Data Quality Notes", expanded=False):
            for warning in profile.warnings:
                st.warning(warning)


def queue_question_button(question: str, key: str, use_container_width: bool = True):
    """Button that stores a suggested question for the Query Interface."""
    if st.button(question, key=key, use_container_width=use_container_width):
        query_queue.queue_question(st.session_state, question)
        st.success("Queued. Open Query Interface to review, edit, and run it.")


def display_question_buttons(questions, key_prefix: str, limit: int = 5):
    """Render de-duplicated suggested question buttons."""
    for idx, question in enumerate(_dedupe(questions)[:limit]):
        queue_question_button(question, key=f"{key_prefix}_{idx}")


def qualitative_next_questions(dataset_name: str):
    """Follow-up prompts that naturally continue qualitative analysis."""
    return [
        f"Show representative quotes for the strongest themes in {dataset_name}.",
        f"Focus only on negative feedback in {dataset_name}.",
        f"Turn the qualitative findings from {dataset_name} into a report paragraph.",
        f"What recommendations follow from the feedback themes in {dataset_name}?",
    ]


def quantitative_next_questions(dataset_name: str, profile):
    """Follow-up prompts that naturally continue quantitative analysis."""
    questions = [
        f"Show the top and bottom metrics in {dataset_name}.",
        f"Find outliers or unusual values in {dataset_name}.",
        f"Explain the quantitative results from {dataset_name} for a report.",
    ]
    if profile and profile.date_columns:
        questions.insert(1, f"What trends appear over time in {dataset_name}?")
    if profile and profile.category_columns:
        questions.append(f"Compare {dataset_name} by {profile.category_columns[0]}.")
    return questions


def report_section_suggestions(profiles):
    """Suggested sections for a report based on selected datasets."""
    sections = ["Executive summary", "Dataset provenance", "Key findings", "Limitations"]
    if any(profile.is_text_ready for profile in profiles):
        sections.extend(["Sentiment overview", "Theme summary", "Representative quotes"])
    if any(profile.is_numeric_ready for profile in profiles):
        sections.extend(["Metric summary", "Top/bottom comparisons", "Outliers"])
    if any(profile.is_time_ready for profile in profiles):
        sections.append("Trend analysis")
    return _dedupe(sections)


def report_prep_questions(profiles):
    """Questions worth asking before generating a stakeholder report."""
    questions = []
    for profile in profiles[:3]:
        if profile.is_text_ready:
            questions.append(f"What are the most report-worthy themes in {profile.name}?")
        if profile.is_numeric_ready:
            questions.append(f"What are the most important metrics in {profile.name}?")
        if profile.warnings:
            questions.append(f"What limitations should the report mention for {profile.name}?")
    return questions


def _dedupe(items):
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            result.append(item)
            seen.add(item)
    return result

"""
Dataset-aware query guidance for the Library Assessment Assistant.

The helpers in this module are intentionally deterministic and local. They
profile uploaded data, suggest useful questions, classify intent, and rewrite
short or vague prompts before they reach retrieval.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd


TEXT_HINTS = (
    "response",
    "comment",
    "feedback",
    "answer",
    "question",
    "text",
    "description",
    "quote",
)
DATE_HINTS = ("date", "time", "year", "month", "period")
TEXT_EXCLUSION_HINTS = ("date", "time", "year", "month", "period", "timestamp")
NUMERIC_HINTS = ("value", "count", "total", "number", "score", "rating", "visits", "circulation")
CATEGORY_HINTS = ("type", "category", "group", "state", "branch", "language", "patron", "material")
MISSING_SENTINELS = {"", "nan", "none", "null", "-666", "-777", "-888", "-999", "n/a", "na"}


@dataclass
class DatasetProfile:
    """Small, serializable profile used to guide UI and query behavior."""

    dataset_id: Optional[int]
    name: str
    dataset_type: str
    row_count: int
    columns: List[str]
    text_columns: List[str] = field(default_factory=list)
    date_columns: List[str] = field(default_factory=list)
    numeric_columns: List[str] = field(default_factory=list)
    category_columns: List[str] = field(default_factory=list)
    missing_columns: List[str] = field(default_factory=list)
    coded_missing_columns: List[str] = field(default_factory=list)
    coded_missing_rates: Dict[str, float] = field(default_factory=dict)
    languages: List[str] = field(default_factory=list)
    sentiment_labels: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)

    @property
    def is_text_ready(self) -> bool:
        return bool(self.text_columns)

    @property
    def is_numeric_ready(self) -> bool:
        return bool(self.numeric_columns)

    @property
    def is_time_ready(self) -> bool:
        return bool(self.date_columns)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "name": self.name,
            "dataset_type": self.dataset_type,
            "row_count": self.row_count,
            "columns": self.columns,
            "text_columns": self.text_columns,
            "date_columns": self.date_columns,
            "numeric_columns": self.numeric_columns,
            "category_columns": self.category_columns,
            "missing_columns": self.missing_columns,
            "coded_missing_columns": self.coded_missing_columns,
            "coded_missing_rates": self.coded_missing_rates,
            "languages": self.languages,
            "sentiment_labels": self.sentiment_labels,
            "warnings": self.warnings,
            "strengths": self.strengths,
        }


def build_dataset_profile(
    df: pd.DataFrame,
    dataset_type: str,
    dataset_name: str = "Uploaded dataset",
    dataset_id: Optional[int] = None,
) -> DatasetProfile:
    """Inspect a DataFrame and return a compact profile for guidance."""
    columns = [str(col) for col in df.columns]
    text_columns = _detect_columns(df, TEXT_HINTS, kind="text")
    date_columns = _detect_date_columns(df)
    numeric_columns = _detect_numeric_columns(df)
    category_columns = _detect_columns(df, CATEGORY_HINTS, kind="category")
    missing_columns = [
        col for col in columns if df[col].isna().all() or _normalized_values(df[col]).isin(MISSING_SENTINELS).all()
    ]
    coded_missing_rates = _detect_coded_missing_rates(df)
    coded_missing_columns = list(coded_missing_rates.keys())

    languages = _top_values(df, ("language", "lang"), limit=8)
    sentiment_labels = _top_values(df, ("sentiment", "label"), limit=8)

    profile = DatasetProfile(
        dataset_id=dataset_id,
        name=dataset_name,
        dataset_type=dataset_type,
        row_count=len(df),
        columns=columns,
        text_columns=text_columns,
        date_columns=date_columns,
        numeric_columns=numeric_columns,
        category_columns=category_columns,
        missing_columns=missing_columns,
        coded_missing_columns=coded_missing_columns,
        coded_missing_rates=coded_missing_rates,
        languages=languages,
        sentiment_labels=sentiment_labels,
    )
    profile.strengths = _build_strengths(profile)
    profile.warnings = _build_warnings(profile)
    return profile


def build_profile_from_dataset_record(
    dataset: Dict[str, Any],
    preview_df: pd.DataFrame,
) -> DatasetProfile:
    """Build a profile from a stored dataset row and preview data."""
    return build_dataset_profile(
        preview_df,
        dataset_type=dataset.get("dataset_type", "unknown"),
        dataset_name=dataset.get("name", "Dataset"),
        dataset_id=dataset.get("id"),
    )


def combine_profiles(profiles: Iterable[DatasetProfile]) -> Dict[str, Any]:
    """Summarize a set of profiles for dashboard/query-level guidance."""
    profile_list = list(profiles)
    return {
        "dataset_count": len(profile_list),
        "total_rows": sum(profile.row_count for profile in profile_list),
        "types": sorted({profile.dataset_type for profile in profile_list}),
        "has_text": any(profile.is_text_ready for profile in profile_list),
        "has_numeric": any(profile.is_numeric_ready for profile in profile_list),
        "has_dates": any(profile.is_time_ready for profile in profile_list),
        "warnings": [warning for profile in profile_list for warning in profile.warnings],
    }


def generate_dataset_brief(profile: DatasetProfile) -> str:
    """Return a short human-readable summary of what a dataset can support."""
    parts = [
        f"{profile.name} has {profile.row_count:,} rows and {len(profile.columns)} columns.",
    ]
    if profile.text_columns:
        parts.append(f"Text analysis can use {', '.join(profile.text_columns[:3])}.")
    if profile.numeric_columns:
        parts.append(f"Numeric analysis can use {', '.join(profile.numeric_columns[:4])}.")
    if profile.date_columns:
        parts.append(f"Trend analysis can use {', '.join(profile.date_columns[:2])}.")
    if profile.languages:
        parts.append(f"Language values detected: {', '.join(profile.languages[:5])}.")
    if profile.sentiment_labels:
        parts.append(f"Sentiment/label values detected: {', '.join(profile.sentiment_labels[:5])}.")
    return " ".join(parts)


def suggest_questions(profile: DatasetProfile, limit: int = 6) -> List[str]:
    """Generate starter questions tailored to one dataset profile."""
    questions: List[str] = []
    dtype = profile.dataset_type.lower()

    if dtype == "survey" or profile.text_columns:
        questions.extend(
            [
                f"What are the main themes in {profile.name}?",
                f"What are people most dissatisfied with in {profile.name}?",
                f"Show representative quotes from negative feedback in {profile.name}.",
            ]
        )
        if profile.sentiment_labels:
            questions.append(f"Compare positive, neutral, and negative responses in {profile.name}.")
        if profile.languages:
            questions.append(f"Compare feedback themes by language in {profile.name}.")

    if dtype in {"usage", "circulation"} or profile.numeric_columns:
        questions.extend(
            [
                f"What are the highest and lowest metrics in {profile.name}?",
                f"Find unusual values or outliers in {profile.name}.",
            ]
        )
        if profile.date_columns:
            questions.append(f"What trends appear over time in {profile.name}?")
        if profile.category_columns:
            questions.append(f"Compare results by {profile.category_columns[0]} in {profile.name}.")

    questions.append(f"Summarize {profile.name} for a library assessment report.")
    if profile.warnings:
        questions.append(f"What data quality issues should I know about in {profile.name}?")
    return _dedupe(questions)[:limit]


def classify_query(query: str, profiles: Iterable[DatasetProfile]) -> Dict[str, Any]:
    """Classify user intent with lightweight keyword rules."""
    text = query.lower()
    profile_list = list(profiles)
    intent = "retrieval"
    if any(phrase in text for phrase in ("what data", "what datasets", "available data", "uploaded data")):
        intent = "data_inventory"
    elif any(word in text for word in ("theme", "sentiment", "quote", "comment", "feedback", "mad", "complain")):
        intent = "qualitative"
    elif any(word in text for word in ("average", "total", "count", "rank", "highest", "lowest", "trend", "compare", "outlier")):
        intent = "quantitative"
    elif any(word in text for word in ("report", "executive", "summary", "recommendation", "board")):
        intent = "reporting"
    elif any(word in text for word in ("missing", "quality", "duplicate", "dirty", "clean", "null", "invalid", "limitation", "caveat")):
        intent = "data_quality"

    targets = []
    for profile in profile_list:
        name_hit = profile.name.lower() in text
        type_hit = profile.dataset_type.lower() in text
        capability_hit = (
            (intent == "qualitative" and profile.is_text_ready)
            or (intent == "quantitative" and profile.is_numeric_ready)
            or intent in {"retrieval", "reporting", "data_quality", "data_inventory"}
        )
        if name_hit or type_hit or capability_hit:
            targets.append(profile.name)

    return {
        "intent": intent,
        "target_datasets": _dedupe(targets),
        "needs_evidence": intent in {"qualitative", "retrieval", "reporting"},
    }


def rewrite_query(query: str, profiles: Iterable[DatasetProfile], intent: Optional[str] = None) -> str:
    """Rewrite vague prompts into clearer retrieval instructions."""
    profile_list = list(profiles)
    resolved_intent = intent or classify_query(query, profile_list)["intent"]
    context = _profile_context(profile_list)
    stripped = query.strip()

    if resolved_intent == "qualitative":
        return (
            f"{stripped}. Focus on open-ended feedback, sentiment, recurring themes, "
            f"and representative source rows. Available context: {context}"
        )
    if resolved_intent == "quantitative":
        return (
            f"{stripped}. Use numeric metrics, dates, categories, rankings, comparisons, "
            f"and outliers where available. Available context: {context}"
        )
    if resolved_intent == "reporting":
        return (
            f"{stripped}. Write the answer as a concise library assessment report section "
            f"with evidence and caveats. Available context: {context}"
        )
    if resolved_intent == "data_quality":
        return (
            f"{stripped}. Identify missing fields, coded missing values, duplicate-looking records, "
            f"and limitations that affect analysis. Available context: {context}"
        )
    if resolved_intent == "data_inventory":
        return (
            f"{stripped}. Summarize the uploaded datasets, row counts, available analysis paths, "
            f"and important caveats. Available context: {context}"
        )
    return f"{stripped}. Use the most relevant uploaded library assessment records. Available context: {context}"


def answer_from_profiles(
    query: str,
    profiles: Iterable[DatasetProfile],
    intent: Optional[str] = None,
) -> Optional[str]:
    """Answer profile-native questions without vector retrieval."""
    profile_list = list(profiles)
    resolved_intent = intent or classify_query(query, profile_list)["intent"]
    if resolved_intent not in {"data_inventory", "data_quality"}:
        return None
    if not profile_list:
        return "No uploaded dataset profile is available yet. Upload data first, then ask again."

    if resolved_intent == "data_inventory":
        lines = ["Here is the data currently available:"]
        for profile in profile_list:
            ready = []
            if profile.is_text_ready:
                ready.append("text/theme analysis")
            if profile.is_numeric_ready:
                ready.append("numeric analysis")
            if profile.is_time_ready:
                ready.append("trend analysis")
            ready_text = ", ".join(ready) if ready else "basic review"
            lines.append(
                f"- {profile.name}: {profile.row_count:,} rows, {len(profile.columns)} columns, "
                f"type `{profile.dataset_type}`, ready for {ready_text}."
            )
        return "\n".join(lines)

    lines = ["Data quality and limitation notes:"]
    for profile in profile_list:
        if profile.warnings:
            lines.append(f"- {profile.name}: {' '.join(profile.warnings)}")
        else:
            lines.append(f"- {profile.name}: no major profile-level warnings detected.")
    lines.append("Use these notes as caveats; they do not replace a full data cleaning review.")
    return "\n".join(lines)


def assess_evidence(
    confidence: float,
    citation_count: int,
    intent: str,
    query: str,
    profiles: Iterable[DatasetProfile],
) -> Dict[str, Any]:
    """Convert raw confidence into a user-facing evidence assessment."""
    profile_list = list(profiles)
    if intent in {"data_inventory", "data_quality"}:
        return {
            "label": "High" if profile_list else "Low",
            "score": 1.0 if profile_list else 0.0,
            "reason": "Answered from dataset profiles, not vector retrieval.",
        }

    broad_terms = ("what data", "available", "summarize", "overview", "limitations")
    is_broad = any(term in query.lower() for term in broad_terms)
    if confidence >= 0.65 and citation_count >= 3:
        label = "High"
        reason = "Retrieved source rows closely matched the question."
    elif confidence >= 0.35 and citation_count >= 2:
        label = "Medium"
        reason = "Retrieved source rows were relevant but not tightly matched."
    else:
        label = "Low"
        reason = "Retrieved source rows were only loosely matched."

    if is_broad and label != "High":
        reason += " Broad or metadata-style questions often score lower with vector retrieval."
    return {
        "label": label,
        "score": confidence,
        "reason": reason,
    }


def suggest_followups(
    query: str,
    answer: str,
    profiles: Iterable[DatasetProfile],
    intent: Optional[str] = None,
    limit: int = 5,
) -> List[str]:
    """Suggest next questions after an answer."""
    profile_list = list(profiles)
    resolved_intent = intent or classify_query(query, profile_list)["intent"]
    suggestions: List[str] = []

    if resolved_intent == "qualitative":
        suggestions.extend(
            [
                "Show representative quotes for each theme.",
                "Focus only on negative or dissatisfied responses.",
                "Turn these findings into a report-ready paragraph.",
            ]
        )
        if any(profile.languages for profile in profile_list):
            suggestions.append("Compare these themes by language.")
    elif resolved_intent == "quantitative":
        suggestions.extend(
            [
                "Show the top and bottom performers.",
                "Check whether any values look like outliers.",
                "Explain the result in plain English for a report.",
            ]
        )
        if any(profile.date_columns for profile in profile_list):
            suggestions.append("Look for trends over time.")
    elif resolved_intent == "data_quality":
        suggestions.extend(
            [
                "Which issues should I fix before analysis?",
                "Create a cleaned-data checklist for this dataset.",
                "What analyses are limited by these data quality issues?",
            ]
        )
    else:
        suggestions.extend(
            [
                "Show the source rows behind this answer.",
                "Summarize this as a report finding.",
                "What should I ask next about this dataset?",
            ]
        )

    if "low" in answer.lower() or "not enough" in answer.lower():
        suggestions.append("Broaden the search and include related terms.")

    return _dedupe(suggestions)[:limit]


def recommended_next_action(profiles: Iterable[DatasetProfile], has_indexed_data: bool = False) -> str:
    """Return one practical next step for dashboard/upload guidance."""
    profile_list = list(profiles)
    if not profile_list:
        return "Upload a survey, usage, or circulation CSV to begin analysis."
    if not has_indexed_data:
        return "Index the uploaded datasets so the query interface can search them."
    if any(profile.is_text_ready for profile in profile_list):
        return "Ask about themes, sentiment, and representative quotes in your survey feedback."
    if any(profile.is_numeric_ready for profile in profile_list):
        return "Run a quantitative comparison or ask for top metrics and outliers."
    return "Review data quality warnings before running deeper analysis."


def _detect_columns(df: pd.DataFrame, hints: Iterable[str], kind: str) -> List[str]:
    columns = []
    for col in df.columns:
        col_str = str(col)
        col_lower = col_str.lower()
        if kind == "text" and any(hint in col_lower for hint in TEXT_EXCLUSION_HINTS):
            continue
        if any(hint in col_lower for hint in hints):
            columns.append(col_str)
        elif kind == "text" and df[col].dtype == "object":
            sample = df[col].dropna().astype(str).head(20)
            if not sample.empty and sample.str.len().median() >= 25:
                columns.append(col_str)
        elif kind == "category" and df[col].dtype == "object":
            sample = df[col].dropna().astype(str).head(200)
            if not sample.empty and sample.nunique() <= max(20, len(sample) * 0.25):
                columns.append(col_str)
    return _dedupe(columns)


def _detect_date_columns(df: pd.DataFrame) -> List[str]:
    columns = []
    for col in df.columns:
        col_str = str(col)
        if any(hint in col_str.lower() for hint in DATE_HINTS):
            columns.append(col_str)
            continue
        sample = df[col].dropna().astype(str).head(50)
        if not sample.empty and sample.str.contains(r"\d{1,4}[-/]\d{1,2}", regex=True).mean() >= 0.5:
            parsed = pd.to_datetime(sample, errors="coerce")
            if parsed.notna().mean() >= 0.7:
                columns.append(col_str)
    return _dedupe(columns)


def _detect_numeric_columns(df: pd.DataFrame) -> List[str]:
    columns = []
    for col in df.columns:
        col_str = str(col)
        series = df[col]
        if pd.api.types.is_numeric_dtype(series):
            columns.append(col_str)
            continue
        if any(hint in col_str.lower() for hint in NUMERIC_HINTS):
            converted = pd.to_numeric(series, errors="coerce")
            if converted.notna().sum() > 0:
                columns.append(col_str)
    return _dedupe(columns)


def _detect_coded_missing_rates(df: pd.DataFrame) -> Dict[str, float]:
    rates = {}
    coded_values = {"-666", "-777", "-888", "-999"}
    for col in df.columns:
        values = _normalized_values(df[col]).head(500)
        if values.empty:
            continue
        rate = float(values.isin(coded_values).mean())
        if rate > 0:
            rates[str(col)] = rate
    return rates


def _top_values(df: pd.DataFrame, hints: Iterable[str], limit: int) -> List[str]:
    for col in df.columns:
        if any(hint in str(col).lower() for hint in hints):
            values = [
                str(value)
                for value in df[col].dropna().astype(str).value_counts().head(limit).index.tolist()
                if str(value).lower() not in MISSING_SENTINELS
            ]
            if values:
                return values
    return []


def _normalized_values(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower()


def _build_strengths(profile: DatasetProfile) -> List[str]:
    strengths = []
    if profile.is_text_ready:
        strengths.append("Ready for qualitative themes and sentiment questions.")
    if profile.is_numeric_ready:
        strengths.append("Ready for numeric summaries and comparisons.")
    if profile.is_time_ready:
        strengths.append("Ready for time-based trend questions.")
    if profile.languages:
        strengths.append("Contains language metadata for subgroup comparisons.")
    if profile.sentiment_labels:
        strengths.append("Contains sentiment or label fields for validation/comparison.")
    return strengths


def _build_warnings(profile: DatasetProfile) -> List[str]:
    warnings = []
    if profile.dataset_type == "survey" and not profile.text_columns:
        warnings.append("No obvious text response column was detected.")
    if profile.dataset_type in {"usage", "circulation"} and not profile.numeric_columns:
        warnings.append("No obvious numeric metric column was detected.")
    if profile.missing_columns:
        warnings.append(f"Empty or fully missing columns detected: {', '.join(profile.missing_columns[:4])}.")
    if profile.coded_missing_columns:
        coded_details = []
        for column in profile.coded_missing_columns[:4]:
            rate = profile.coded_missing_rates.get(column)
            if rate is not None:
                coded_details.append(f"{column} ({rate:.0%})")
            else:
                coded_details.append(column)
        warnings.append(
            f"Coded missing values appear in: {', '.join(coded_details)}."
        )
    if profile.row_count < 10:
        warnings.append("This dataset is small, so patterns may be anecdotal.")
    return warnings


def _profile_context(profiles: List[DatasetProfile]) -> str:
    if not profiles:
        return "no uploaded dataset profile is available"
    fragments = []
    for profile in profiles[:4]:
        details = [profile.dataset_type, f"{profile.row_count:,} rows"]
        if profile.text_columns:
            details.append(f"text: {', '.join(profile.text_columns[:2])}")
        if profile.numeric_columns:
            details.append(f"numeric: {', '.join(profile.numeric_columns[:2])}")
        if profile.date_columns:
            details.append(f"dates: {', '.join(profile.date_columns[:2])}")
        fragments.append(f"{profile.name} ({'; '.join(details)})")
    return " | ".join(fragments)


def _dedupe(items: Iterable[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            result.append(item)
            seen.add(item)
    return result

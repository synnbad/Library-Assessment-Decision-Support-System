"""Assessment data import and normalization helpers.

This module turns common library assessment exports into clean DataFrames that
can continue through the existing upload, metadata, analysis, indexing, and
reporting workflow.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


SUPPORTED_EXTENSIONS = ("csv", "tsv", "txt", "xlsx", "json")

DATASET_TYPES = [
    "survey",
    "usage",
    "circulation",
    "e_resource",
    "spaces",
    "instruction",
    "reference",
    "events",
    "collection",
    "benchmark",
]

TEXT_DATASET_TYPES = {"survey", "reference"}
METRIC_DATASET_TYPES = {
    "usage",
    "circulation",
    "e_resource",
    "spaces",
    "instruction",
    "events",
    "collection",
    "benchmark",
}

DOMAIN_LABELS = {
    "survey": "Survey and feedback",
    "usage": "General usage statistics",
    "circulation": "Circulation and borrowing",
    "e_resource": "E-resource and COUNTER usage",
    "spaces": "Spaces, rooms, and gate counts",
    "instruction": "Instruction and learning assessment",
    "reference": "Reference, chat, and service interactions",
    "events": "Events and programs",
    "collection": "Collection assessment",
    "benchmark": "Peer, ACRL, ARL, or benchmark data",
}


@dataclass
class ImportResult:
    """Normalized upload result used by the Data Import Hub."""

    dataframe: pd.DataFrame
    original_extension: str
    detected_type: str
    normalized_type: str
    notes: List[str] = field(default_factory=list)
    data_dictionary: List[Dict[str, Any]] = field(default_factory=list)


def parse_assessment_file(file: Any, filename: str) -> ImportResult:
    """Parse a supported assessment file and normalize it for storage."""
    extension = Path(filename).suffix.lower().lstrip(".")
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '.{extension}'. Supported types: {', '.join(SUPPORTED_EXTENSIONS)}."
        )

    raw_df = _parse_file_to_dataframe(file, extension)
    raw_df = _clean_dataframe(raw_df)
    detected_type = detect_assessment_type(raw_df, filename)
    normalized_df, notes = normalize_assessment_dataframe(raw_df, detected_type)
    data_dictionary = build_data_dictionary(normalized_df)

    return ImportResult(
        dataframe=normalized_df,
        original_extension=extension,
        detected_type=detected_type,
        normalized_type=detected_type,
        notes=notes,
        data_dictionary=data_dictionary,
    )


def detect_assessment_type(df: pd.DataFrame, filename: str = "") -> str:
    """Infer a library assessment domain from filename and column names."""
    text = " ".join([filename, *[str(col) for col in df.columns]]).lower()

    rules = [
        ("benchmark", ("acrl", "arl", "peer", "benchmark", "ipeds", "institution")),
        ("e_resource", ("counter", "database", "platform", "title", "requests", "searches", "turnaway")),
        ("spaces", ("gate", "door", "room", "booking", "reservation", "seat", "occupancy", "libcal")),
        ("instruction", ("instruction", "class", "course", "section", "learning", "attendance")),
        ("reference", ("reference", "chat", "ticket", "question_text", "transaction", "libanswers")),
        ("events", ("event", "program", "workshop", "attendee", "registration")),
        ("collection", ("holdings", "collection", "call_number", "subject", "cost", "vendor")),
        ("circulation", ("checkout", "borrow", "renewal", "hold", "loan", "material")),
        ("survey", ("survey", "qualtrics", "feedback", "satisfaction", "comment", "response_text")),
        ("usage", ("usage", "visits", "sessions", "metric", "count", "value")),
    ]

    for dataset_type, hints in rules:
        if any(hint in text for hint in hints):
            return dataset_type
    return "usage" if df.select_dtypes(include="number").shape[1] else "survey"


def normalize_assessment_dataframe(df: pd.DataFrame, dataset_type: str) -> tuple[pd.DataFrame, List[str]]:
    """Normalize common assessment exports while preserving tabular meaning."""
    notes: List[str] = []
    normalized = _clean_dataframe(df)

    if dataset_type == "e_resource":
        counter_df = _normalize_counter_like_usage(normalized)
        if counter_df is not None:
            notes.append("Converted COUNTER-style wide usage report into metric rows.")
            normalized = counter_df

    if dataset_type in METRIC_DATASET_TYPES:
        normalized = _coerce_metric_friendly_columns(normalized, dataset_type)
    elif dataset_type in TEXT_DATASET_TYPES:
        normalized = _coerce_text_friendly_columns(normalized)

    return normalized, notes


def build_data_dictionary(df: pd.DataFrame, max_examples: int = 3) -> List[Dict[str, Any]]:
    """Create a compact data dictionary from a DataFrame."""
    dictionary: List[Dict[str, Any]] = []
    row_count = len(df)

    for column in df.columns:
        series = df[column]
        non_missing = series.dropna()
        examples = [str(value)[:80] for value in non_missing.astype(str).unique()[:max_examples]]
        dictionary.append(
            {
                "column": str(column),
                "type": _friendly_dtype(series),
                "role": infer_column_role(str(column), series),
                "missing_count": int(series.isna().sum()),
                "missing_pct": round(float(series.isna().mean() * 100), 2) if row_count else 0.0,
                "unique_count": int(series.nunique(dropna=True)),
                "examples": examples,
            }
        )

    return dictionary


def infer_column_role(column: str, series: pd.Series) -> str:
    """Infer a column role for documentation and dashboard design."""
    lower = column.lower()
    if any(token in lower for token in ("date", "time", "month", "year", "period")):
        return "date/time"
    if any(token in lower for token in ("metric", "measure", "indicator", "kpi")):
        return "metric label"
    if any(token in lower for token in ("value", "count", "total", "score", "rating", "amount", "cost")):
        return "numeric measure"
    if any(token in lower for token in ("comment", "response", "feedback", "question", "answer", "text")):
        return "qualitative text"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric measure"
    if series.nunique(dropna=True) <= 25:
        return "category"
    return "descriptor"


def build_metadata_suggestions(df: pd.DataFrame, dataset_type: str, filename: str) -> Dict[str, Any]:
    """Generate FAIR/CARE metadata suggestions from dataset shape and content."""
    title = Path(filename).stem.replace("_", " ").replace("-", " ").title()
    dictionary = build_data_dictionary(df)
    roles = {item["role"] for item in dictionary}
    date_columns = [item["column"] for item in dictionary if item["role"] == "date/time"]
    metric_columns = [item["column"] for item in dictionary if item["role"] == "numeric measure"]
    text_columns = [item["column"] for item in dictionary if item["role"] == "qualitative text"]

    description = [
        f"{DOMAIN_LABELS.get(dataset_type, dataset_type.title())} dataset with {len(df):,} records and {len(df.columns)} fields."
    ]
    if date_columns:
        date_range = _detect_date_range(df, date_columns)
        description.append(
            f"Includes date/time fields ({', '.join(date_columns[:2])})"
            + (f" covering {date_range}." if date_range else ".")
        )
    if metric_columns:
        description.append(f"Contains numeric measures such as {', '.join(metric_columns[:4])}.")
    if text_columns:
        description.append(f"Contains qualitative text fields such as {', '.join(text_columns[:3])}.")

    keywords = [dataset_type]
    for role in sorted(roles):
        if role in {"date/time", "numeric measure", "qualitative text", "category"}:
            keywords.append(role.replace("/", "-").replace(" ", "-"))
    source = _detect_source(filename, df.columns)

    return {
        "title": title,
        "description": " ".join(description),
        "source": source,
        "keywords": _dedupe(keywords),
        "data_dictionary": dictionary,
    }


def _parse_file_to_dataframe(file: Any, extension: str) -> pd.DataFrame:
    content = _read_file_content(file)

    if extension == "xlsx":
        return pd.read_excel(BytesIO(content), sheet_name=0)

    if extension == "json":
        payload = json.loads(content.decode("utf-8-sig"))
        return _json_to_dataframe(payload)

    text = _decode_text(content)
    separator = "\t" if extension == "tsv" else _detect_delimiter(text)
    return pd.read_csv(StringIO(text), sep=separator)


def _read_file_content(file: Any) -> bytes:
    if hasattr(file, "getvalue"):
        value = file.getvalue()
    else:
        if hasattr(file, "seek"):
            file.seek(0)
        value = file.read()
    if isinstance(value, str):
        return value.encode("utf-8")
    return value


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "latin-1", "cp1252", "utf-16"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def _json_to_dataframe(payload: Any) -> pd.DataFrame:
    if isinstance(payload, list):
        return pd.json_normalize(payload)
    if isinstance(payload, dict):
        list_items = [(key, value) for key, value in payload.items() if isinstance(value, list)]
        if list_items:
            _, rows = max(list_items, key=lambda item: len(item[1]))
            return pd.json_normalize(rows)
        return pd.json_normalize(payload)
    raise ValueError("JSON upload must contain an object or a list of objects.")


def _detect_delimiter(text: str) -> str:
    first_lines = "\n".join(text.splitlines()[:5])
    if "\t" in first_lines and first_lines.count("\t") >= first_lines.count(","):
        return "\t"
    if "|" in first_lines and first_lines.count("|") > first_lines.count(","):
        return "|"
    if ";" in first_lines and first_lines.count(";") > first_lines.count(","):
        return ";"
    return ","


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned.columns = _dedupe_column_names([str(col).strip() or "unnamed" for col in cleaned.columns])
    cleaned = cleaned.dropna(axis=0, how="all")
    cleaned = cleaned.dropna(axis=1, how="all")
    return cleaned.reset_index(drop=True)


def _dedupe_column_names(columns: List[str]) -> List[str]:
    seen: Dict[str, int] = {}
    result = []
    for column in columns:
        count = seen.get(column, 0)
        result.append(column if count == 0 else f"{column}_{count + 1}")
        seen[column] = count + 1
    return result


def _normalize_counter_like_usage(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    month_columns = [column for column in df.columns if _looks_like_period(column)]
    if len(month_columns) < 2:
        return None

    metric_col = _first_matching_column(df, ("metric", "measure", "type")) or "Metric"
    title_col = _first_matching_column(df, ("title", "database", "platform", "resource")) or df.columns[0]
    id_vars = [column for column in [title_col, metric_col] if column in df.columns]
    melted = df.melt(
        id_vars=id_vars,
        value_vars=month_columns,
        var_name="date",
        value_name="metric_value",
    )
    melted["metric_name"] = melted[metric_col] if metric_col in melted.columns else "usage"
    melted["category"] = melted[title_col] if title_col in melted.columns else ""
    return melted[["date", "metric_name", "metric_value", "category"]]


def _coerce_metric_friendly_columns(df: pd.DataFrame, dataset_type: str) -> pd.DataFrame:
    normalized = df.copy()
    if "metric_value" not in normalized.columns:
        numeric_cols = normalized.select_dtypes(include="number").columns.tolist()
        value_col = _first_matching_column(normalized, ("value", "count", "total", "number", "visits", "sessions"))
        if value_col is None and numeric_cols:
            value_col = numeric_cols[0]
        if value_col is not None:
            normalized = normalized.rename(columns={value_col: "metric_value"})

    if "metric_name" not in normalized.columns:
        metric_col = _first_matching_column(normalized, ("metric", "measure", "indicator", "title", "room", "event"))
        if metric_col is not None and metric_col != "metric_value":
            normalized = normalized.rename(columns={metric_col: "metric_name"})
        else:
            normalized["metric_name"] = DOMAIN_LABELS.get(dataset_type, dataset_type)

    if "date" not in normalized.columns:
        date_col = _first_matching_column(normalized, ("date", "time", "period", "month", "year"))
        if date_col is not None:
            normalized = normalized.rename(columns={date_col: "date"})

    if "category" not in normalized.columns:
        category_col = _first_matching_column(normalized, ("category", "type", "group", "audience", "department"))
        if category_col is not None and category_col not in {"metric_name", "metric_value", "date"}:
            normalized = normalized.rename(columns={category_col: "category"})
        else:
            normalized["category"] = dataset_type

    return normalized


def _coerce_text_friendly_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    if "response_text" not in normalized.columns:
        text_col = _first_matching_column(normalized, ("response", "answer", "feedback", "comment", "text", "question"))
        if text_col is not None:
            normalized = normalized.rename(columns={text_col: "response_text"})
    if "response_date" not in normalized.columns:
        date_col = _first_matching_column(normalized, ("date", "time", "timestamp"))
        if date_col is not None:
            normalized = normalized.rename(columns={date_col: "response_date"})
    if "question" not in normalized.columns:
        question_col = _first_matching_column(normalized, ("question", "prompt", "topic", "category"))
        if question_col is not None and question_col != "response_text":
            normalized = normalized.rename(columns={question_col: "question"})
    return normalized


def _first_matching_column(df: pd.DataFrame, hints: tuple[str, ...]) -> Optional[str]:
    for column in df.columns:
        lower = str(column).lower()
        if any(hint in lower for hint in hints):
            return column
    return None


def _looks_like_period(column: str) -> bool:
    text = str(column).strip()
    if re.fullmatch(r"\d{4}[-/]\d{1,2}", text):
        return True
    if re.fullmatch(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*[- ]?\d{2,4}", text.lower()):
        return True
    try:
        parsed = pd.to_datetime(text, errors="coerce")
        return not pd.isna(parsed)
    except Exception:
        return False


def _friendly_dtype(series: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(series):
        return "number"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    return "text"


def _detect_date_range(df: pd.DataFrame, date_columns: List[str]) -> Optional[str]:
    for column in date_columns:
        dates = pd.to_datetime(df[column], errors="coerce").dropna()
        if not dates.empty:
            return f"{dates.min().date()} to {dates.max().date()}"
    return None


def _detect_source(filename: str, columns: Any) -> str:
    text = " ".join([filename, *[str(column) for column in columns]]).lower()
    if "qualtrics" in text:
        return "Qualtrics Survey"
    if "libcal" in text:
        return "LibCal"
    if "libanswers" in text:
        return "LibAnswers"
    if "counter" in text:
        return "COUNTER Report"
    if any(term in text for term in ("alma", "sierra", "ils")):
        return "Integrated Library System"
    if any(term in text for term in ("acrl", "arl", "ipeds")):
        return "External Benchmark Source"
    return "Data Import Hub"


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            result.append(item)
            seen.add(item)
    return result

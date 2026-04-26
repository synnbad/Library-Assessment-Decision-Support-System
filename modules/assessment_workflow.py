"""Assessment workflow helpers for projects, benchmarks, dashboards, and training."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from modules import data_importer
from modules.database import execute_query, execute_update, get_db_connection


PROJECT_STATUSES = ("planned", "active", "reporting", "completed")


def ensure_assessment_schema(db_path: Optional[str] = None) -> None:
    """Create workflow tables if an older database does not have them yet."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessment_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                status TEXT DEFAULT 'planned',
                goal TEXT,
                research_questions TEXT,
                stakeholders TEXT,
                methods TEXT,
                dataset_ids TEXT,
                findings TEXT,
                recommendations TEXT,
                due_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dashboard_blueprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                audience TEXT,
                user_story TEXT,
                kpis TEXT,
                dataset_ids TEXT,
                visualizations TEXT,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                topic TEXT,
                audience TEXT,
                content_markdown TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assessment_projects_status ON assessment_projects(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dashboard_blueprints_status ON dashboard_blueprints(status)")


def create_assessment_project(
    title: str,
    goal: str,
    research_questions: List[str],
    stakeholders: List[str],
    methods: List[str],
    dataset_ids: Optional[List[int]] = None,
    due_date: Optional[str] = None,
    status: str = "planned",
    db_path: Optional[str] = None,
) -> int:
    """Create an assessment project record."""
    ensure_assessment_schema(db_path)
    if status not in PROJECT_STATUSES:
        raise ValueError(f"Status must be one of: {', '.join(PROJECT_STATUSES)}")
    return execute_update(
        """
        INSERT INTO assessment_projects (
            title, status, goal, research_questions, stakeholders, methods, dataset_ids, due_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title.strip(),
            status,
            goal.strip(),
            json.dumps(_clean_list(research_questions)),
            json.dumps(_clean_list(stakeholders)),
            json.dumps(_clean_list(methods)),
            json.dumps(dataset_ids or []),
            due_date,
        ),
        db_path,
    )


def list_assessment_projects(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return assessment projects with JSON fields decoded."""
    ensure_assessment_schema(db_path)
    rows = execute_query(
        "SELECT * FROM assessment_projects ORDER BY created_at DESC",
        db_path=db_path,
    )
    for row in rows:
        for field in ("research_questions", "stakeholders", "methods", "dataset_ids"):
            row[field] = _loads(row.get(field), [])
    return rows


def update_project_notes(
    project_id: int,
    findings: str,
    recommendations: str,
    status: str = "reporting",
    db_path: Optional[str] = None,
) -> bool:
    """Update findings, recommendations, and status for a project."""
    ensure_assessment_schema(db_path)
    if status not in PROJECT_STATUSES:
        raise ValueError(f"Status must be one of: {', '.join(PROJECT_STATUSES)}")
    affected = execute_update(
        """
        UPDATE assessment_projects
        SET findings = ?, recommendations = ?, status = ?, updated_at = ?
        WHERE id = ?
        """,
        (findings.strip(), recommendations.strip(), status, datetime.now().isoformat(), project_id),
        db_path,
    )
    return affected > 0


def create_dashboard_blueprint(
    title: str,
    audience: str,
    user_story: str,
    kpis: List[Dict[str, Any]],
    dataset_ids: Optional[List[int]] = None,
    visualizations: Optional[List[str]] = None,
    db_path: Optional[str] = None,
) -> int:
    """Store a dashboard planning blueprint."""
    ensure_assessment_schema(db_path)
    return execute_update(
        """
        INSERT INTO dashboard_blueprints (
            title, audience, user_story, kpis, dataset_ids, visualizations
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            title.strip(),
            audience.strip(),
            user_story.strip(),
            json.dumps(kpis),
            json.dumps(dataset_ids or []),
            json.dumps(visualizations or []),
        ),
        db_path,
    )


def list_dashboard_blueprints(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return stored dashboard blueprints."""
    ensure_assessment_schema(db_path)
    rows = execute_query("SELECT * FROM dashboard_blueprints ORDER BY created_at DESC", db_path=db_path)
    for row in rows:
        for field in ("kpis", "dataset_ids", "visualizations"):
            row[field] = _loads(row.get(field), [])
    return rows


def create_training_material(
    title: str,
    topic: str,
    audience: str,
    content_markdown: str,
    db_path: Optional[str] = None,
) -> int:
    """Persist a generated training handout or workshop outline."""
    ensure_assessment_schema(db_path)
    return execute_update(
        """
        INSERT INTO training_materials (title, topic, audience, content_markdown)
        VALUES (?, ?, ?, ?)
        """,
        (title.strip(), topic.strip(), audience.strip(), content_markdown.strip()),
        db_path,
    )


def list_training_materials(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return generated training materials."""
    ensure_assessment_schema(db_path)
    return execute_query("SELECT * FROM training_materials ORDER BY created_at DESC", db_path=db_path)


def build_assessment_plan(
    title: str,
    goal: str,
    dataset_profiles: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generate a practical assessment plan from selected datasets."""
    methods = ["data profiling", "data quality review", "stakeholder reporting"]
    if any(profile.get("has_text") for profile in dataset_profiles):
        methods.extend(["sentiment analysis", "theme extraction"])
    if any(profile.get("has_numeric") for profile in dataset_profiles):
        methods.extend(["descriptive statistics", "trend analysis", "comparative analysis"])
    if any(profile.get("dataset_type") == "benchmark" for profile in dataset_profiles):
        methods.append("peer benchmarking")

    return {
        "title": title,
        "goal": goal,
        "research_questions": [
            "What patterns, gaps, or opportunities are visible in the available evidence?",
            "Which findings are strong enough to share with stakeholders?",
            "What limitations should be documented before decisions are made?",
        ],
        "methods": _clean_list(methods),
        "phases": [
            "Define decision context and stakeholder questions.",
            "Import, clean, profile, and document datasets.",
            "Analyze qualitative and quantitative evidence.",
            "Create visualizations, dashboard stories, and report recommendations.",
            "Review privacy, limitations, and data governance before sharing.",
        ],
    }


def compare_benchmarks(
    df: pd.DataFrame,
    institution_column: str,
    metric_column: str,
    target_institution: Optional[str] = None,
) -> Dict[str, Any]:
    """Compare an institution against peer benchmark rows."""
    if institution_column not in df.columns:
        raise ValueError(f"Column '{institution_column}' was not found.")
    if metric_column not in df.columns:
        raise ValueError(f"Column '{metric_column}' was not found.")

    values = pd.to_numeric(df[metric_column], errors="coerce")
    usable = df.assign(_metric_value=values).dropna(subset=["_metric_value"])
    if usable.empty:
        raise ValueError(f"Column '{metric_column}' has no numeric values.")

    sorted_values = usable.sort_values("_metric_value", ascending=False).reset_index(drop=True)
    target_row = None
    if target_institution:
        matches = sorted_values[
            sorted_values[institution_column].astype(str).str.lower() == target_institution.lower()
        ]
        if not matches.empty:
            target_row = matches.iloc[0]

    rank = None
    percentile = None
    if target_row is not None:
        rank = int(sorted_values.index[sorted_values[institution_column] == target_row[institution_column]][0]) + 1
        percentile = round((1 - ((rank - 1) / max(len(sorted_values) - 1, 1))) * 100, 1)

    return {
        "metric": metric_column,
        "count": int(len(usable)),
        "mean": float(usable["_metric_value"].mean()),
        "median": float(usable["_metric_value"].median()),
        "min": float(usable["_metric_value"].min()),
        "max": float(usable["_metric_value"].max()),
        "top_performers": sorted_values[[institution_column, "_metric_value"]].head(5).to_dict("records"),
        "target": None
        if target_row is None
        else {
            "institution": str(target_row[institution_column]),
            "value": float(target_row["_metric_value"]),
            "rank": rank,
            "percentile": percentile,
        },
    }


def recommend_dashboard_kpis(df: pd.DataFrame, dataset_type: str) -> List[Dict[str, Any]]:
    """Recommend dashboard KPIs from column roles."""
    dictionary = data_importer.build_data_dictionary(df)
    kpis: List[Dict[str, Any]] = []
    for item in dictionary:
        if item["role"] == "numeric measure":
            kpis.append(
                {
                    "name": item["column"],
                    "definition": f"Track total, average, and change over time for {item['column']}.",
                    "visual": "line chart" if any(d["role"] == "date/time" for d in dictionary) else "bar chart",
                    "audience": _audience_for_type(dataset_type),
                }
            )
    if not kpis and any(item["role"] == "qualitative text" for item in dictionary):
        kpis.append(
            {
                "name": "Feedback themes",
                "definition": "Track recurring themes, sentiment, and representative comments.",
                "visual": "theme frequency bar chart",
                "audience": _audience_for_type(dataset_type),
            }
        )
    return kpis[:6]


def analyze_numeric_edge_cases(df: pd.DataFrame) -> Dict[str, Any]:
    """Run lightweight modeling checks: missingness, outliers, and trend readiness."""
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    date_cols = [
        col for col in df.columns if any(token in str(col).lower() for token in ("date", "time", "month", "year"))
    ]
    outliers = {}
    for column in numeric_cols:
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        if len(values) < 4:
            continue
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            outlier_count = 0
        else:
            outlier_count = int(((values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)).sum())
        outliers[column] = outlier_count

    return {
        "numeric_columns": numeric_cols,
        "date_columns": date_cols,
        "trend_ready": bool(numeric_cols and date_cols),
        "outliers": outliers,
        "missing_pct": {
            str(column): round(float(df[column].isna().mean() * 100), 2) for column in df.columns
        },
    }


def generate_training_outline(topic: str, audience: str = "library staff") -> str:
    """Generate a concise workshop/handout outline."""
    topic = topic.strip() or "library assessment"
    audience = audience.strip() or "library staff"
    return "\n".join(
        [
            f"# {topic.title()} Workshop for {audience.title()}",
            "",
            "## Learning Outcomes",
            "- Identify the assessment question and decision context.",
            "- Select appropriate qualitative or quantitative evidence.",
            "- Apply privacy, FAIR, and CARE checks before sharing results.",
            "- Choose visualizations that match the stakeholder task.",
            "",
            "## Agenda",
            "1. Assessment question framing",
            "2. Data import, cleaning, and metadata review",
            "3. Analysis walkthrough",
            "4. Visualization and dashboard storyboarding",
            "5. Reporting, limitations, and next actions",
            "",
            "## Practice Activity",
            "Use one uploaded dataset to create a data dictionary, one chart, and one stakeholder-ready finding.",
        ]
    )


def _loads(value: Any, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _clean_list(values: List[Any]) -> List[str]:
    return [str(value).strip() for value in values if str(value).strip()]


def _audience_for_type(dataset_type: str) -> str:
    if dataset_type == "benchmark":
        return "library leadership and campus partners"
    if dataset_type in {"e_resource", "collection"}:
        return "collections and acquisitions stakeholders"
    if dataset_type in {"spaces", "instruction", "reference", "events"}:
        return "public services stakeholders"
    return "assessment stakeholders"

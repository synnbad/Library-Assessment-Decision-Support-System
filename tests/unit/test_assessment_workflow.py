import pandas as pd

from modules import assessment_workflow
from modules.database import init_database


def test_assessment_schema_and_project_lifecycle(tmp_path):
    db_path = str(tmp_path / "workflow.db")
    init_database(db_path)
    assessment_workflow.ensure_assessment_schema(db_path)

    project_id = assessment_workflow.create_assessment_project(
        title="Space Use Assessment",
        goal="Improve study space decisions.",
        research_questions=["Where is demand highest?"],
        stakeholders=["UX Librarian"],
        methods=["gate counts"],
        dataset_ids=[1],
        db_path=db_path,
    )

    assert project_id > 0
    projects = assessment_workflow.list_assessment_projects(db_path)
    assert projects[0]["research_questions"] == ["Where is demand highest?"]

    assert assessment_workflow.update_project_notes(
        project_id,
        findings="Demand peaks after 6 PM.",
        recommendations="Extend staffing review.",
        status="reporting",
        db_path=db_path,
    )


def test_benchmark_summary_ranks_target_institution():
    df = pd.DataFrame(
        {
            "Institution": ["Our Library", "Peer A", "Peer B"],
            "Visits": [100, 150, 75],
        }
    )

    summary = assessment_workflow.compare_benchmarks(df, "Institution", "Visits", "Our Library")

    assert summary["target"]["rank"] == 2
    assert summary["target"]["value"] == 100
    assert summary["max"] == 150


def test_dashboard_kpi_and_training_generation():
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02"],
            "visits": [10, 12],
            "branch": ["Main", "Main"],
        }
    )

    kpis = assessment_workflow.recommend_dashboard_kpis(df, "usage")
    outline = assessment_workflow.generate_training_outline("visualization basics", "student workers")

    assert kpis[0]["name"] == "visits"
    assert "Learning Outcomes" in outline

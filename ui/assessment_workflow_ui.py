"""Assessment workflow workspace UI."""

import pandas as pd
import streamlit as st

from modules import assessment_workflow, csv_handler
from ui import smart_guidance


def show_assessment_workflow_page():
    """Display the assessment operations workspace."""
    assessment_workflow.ensure_assessment_schema()
    st.title("Assessment Workspace")
    st.markdown("Plan projects, compare benchmarks, design dashboards, and generate staff training materials.")

    tabs = st.tabs(
        [
            "Projects",
            "Benchmarking",
            "Dashboard Studio",
            "Modeling Checks",
            "Methods & Training",
        ]
    )

    with tabs[0]:
        _show_projects_tab()
    with tabs[1]:
        _show_benchmarking_tab()
    with tabs[2]:
        _show_dashboard_tab()
    with tabs[3]:
        _show_modeling_tab()
    with tabs[4]:
        _show_training_tab()


def _show_projects_tab():
    datasets = csv_handler.get_datasets()
    st.markdown("### Assessment Projects")
    st.caption("Track an initiative from stakeholder question through findings and recommendations.")

    with st.form("assessment_project_form"):
        title = st.text_input("Project Title", value="Library Service Assessment")
        goal = st.text_area(
            "Goal",
            value="Understand evidence patterns and produce actionable recommendations for stakeholders.",
        )
        selected_dataset_ids = st.multiselect(
            "Attach Datasets",
            options=[dataset["id"] for dataset in datasets],
            format_func=lambda dataset_id: _dataset_label(datasets, dataset_id),
        )
        stakeholders = st.text_input(
            "Stakeholders",
            value="Assessment Librarian, UX Librarian, Library Leadership",
            help="Comma-separated",
        )
        due_date = st.text_input("Due Date", value="")
        submitted = st.form_submit_button("Create Project", type="primary")

    if submitted:
        profiles = _profiles_for_datasets(datasets, selected_dataset_ids)
        plan = assessment_workflow.build_assessment_plan(title, goal, profiles)
        project_id = assessment_workflow.create_assessment_project(
            title=title,
            goal=goal,
            research_questions=plan["research_questions"],
            stakeholders=_split_csv(stakeholders),
            methods=plan["methods"],
            dataset_ids=selected_dataset_ids,
            due_date=due_date or None,
        )
        st.success(f"Project created: ID {project_id}")
        with st.expander("Generated Assessment Plan", expanded=True):
            st.json(plan)

    projects = assessment_workflow.list_assessment_projects()
    if not projects:
        st.info("No assessment projects yet.")
        return

    for project in projects:
        with st.expander(f"{project['title']} ({project['status']})", expanded=False):
            st.markdown(f"**Goal:** {project.get('goal') or 'Not provided'}")
            st.markdown(f"**Stakeholders:** {', '.join(project.get('stakeholders', [])) or 'Not provided'}")
            st.markdown(f"**Methods:** {', '.join(project.get('methods', [])) or 'Not provided'}")
            st.markdown("**Research Questions**")
            for question in project.get("research_questions", []):
                st.markdown(f"- {question}")
            _show_project_update_form(project)


def _show_project_update_form(project):
    with st.form(f"project_notes_{project['id']}"):
        findings = st.text_area("Findings", value=project.get("findings") or "")
        recommendations = st.text_area("Recommendations", value=project.get("recommendations") or "")
        status = st.selectbox(
            "Status",
            options=list(assessment_workflow.PROJECT_STATUSES),
            index=list(assessment_workflow.PROJECT_STATUSES).index(project.get("status", "planned")),
        )
        if st.form_submit_button("Update Project"):
            assessment_workflow.update_project_notes(project["id"], findings, recommendations, status)
            st.success("Project updated.")
            st.rerun()


def _show_benchmarking_tab():
    st.markdown("### Peer and Benchmark Comparison")
    dataset = _select_dataset("benchmark_dataset_selector")
    if not dataset:
        return

    df = csv_handler.get_preview(dataset["id"], n_rows=dataset["row_count"])
    if df.empty:
        st.info("This dataset has no previewable rows.")
        return

    st.dataframe(df.head(20), use_container_width=True)
    columns = df.columns.tolist()
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        numeric_cols = [
            col for col in columns if pd.to_numeric(df[col], errors="coerce").notna().sum() > 0
        ]
    institution_guess = next((col for col in columns if "institution" in col.lower() or "peer" in col.lower()), columns[0])

    col1, col2, col3 = st.columns(3)
    with col1:
        institution_col = st.selectbox("Institution Column", columns, index=columns.index(institution_guess))
    with col2:
        metric_col = st.selectbox("Metric Column", numeric_cols or columns)
    with col3:
        target = st.text_input("Target Institution", value="")

    if st.button("Run Benchmark", type="primary"):
        try:
            summary = assessment_workflow.compare_benchmarks(
                df,
                institution_column=institution_col,
                metric_column=metric_col,
                target_institution=target or None,
            )
            _display_benchmark_summary(summary)
        except Exception as e:
            st.error(f"Benchmarking failed: {e}")


def _show_dashboard_tab():
    st.markdown("### Dashboard Studio")
    dataset = _select_dataset("dashboard_dataset_selector")
    if not dataset:
        return

    df = csv_handler.get_preview(dataset["id"], n_rows=dataset["row_count"])
    if df.empty:
        st.info("This dataset has no previewable rows.")
        return

    kpis = assessment_workflow.recommend_dashboard_kpis(df, dataset["dataset_type"])
    st.markdown("#### Recommended KPIs")
    if kpis:
        st.dataframe(pd.DataFrame(kpis), use_container_width=True)
    else:
        st.info("No KPI candidates detected yet. Add numeric or qualitative columns to improve recommendations.")

    with st.form("dashboard_blueprint_form"):
        title = st.text_input("Dashboard Title", value=f"{dataset['name']} Dashboard")
        audience = st.text_input("Audience", value="Library leadership and assessment stakeholders")
        user_story = st.text_area(
            "User Story",
            value="As a library stakeholder, I want to monitor service evidence so I can make timely, data-informed decisions.",
        )
        visualizations = st.text_input("Preferred Visuals", value="trend line, bar chart, summary KPI tiles")
        submitted = st.form_submit_button("Save Dashboard Blueprint", type="primary")

    if submitted:
        blueprint_id = assessment_workflow.create_dashboard_blueprint(
            title=title,
            audience=audience,
            user_story=user_story,
            kpis=kpis,
            dataset_ids=[dataset["id"]],
            visualizations=_split_csv(visualizations),
        )
        st.success(f"Dashboard blueprint saved: ID {blueprint_id}")

    blueprints = assessment_workflow.list_dashboard_blueprints()
    if blueprints:
        with st.expander("Saved Blueprints", expanded=False):
            for blueprint in blueprints:
                st.markdown(f"**{blueprint['title']}** - {blueprint.get('audience') or 'No audience'}")
                st.caption(blueprint.get("user_story") or "")


def _show_modeling_tab():
    st.markdown("### Advanced Modeling Readiness")
    dataset = _select_dataset("modeling_dataset_selector")
    if not dataset:
        return

    df = csv_handler.get_preview(dataset["id"], n_rows=dataset["row_count"])
    if df.empty:
        st.info("This dataset has no previewable rows.")
        return

    checks = assessment_workflow.analyze_numeric_edge_cases(df)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Numeric Columns", len(checks["numeric_columns"]))
    with col2:
        st.metric("Date Columns", len(checks["date_columns"]))
    with col3:
        st.metric("Trend Ready", "Yes" if checks["trend_ready"] else "Needs review")

    if checks["outliers"]:
        st.markdown("#### Outlier Signals")
        st.dataframe(
            pd.DataFrame(
                [{"column": column, "outlier_count": count} for column, count in checks["outliers"].items()]
            ),
            use_container_width=True,
        )
    with st.expander("Missingness", expanded=False):
        st.dataframe(
            pd.DataFrame(
                [{"column": column, "missing_pct": pct} for column, pct in checks["missing_pct"].items()]
            ),
            use_container_width=True,
        )


def _show_training_tab():
    st.markdown("### Methods & Training")
    topic = st.text_input("Topic", value="data-informed library assessment")
    audience = st.text_input("Audience", value="library staff")
    if st.button("Generate Training Outline", type="primary"):
        outline = assessment_workflow.generate_training_outline(topic, audience)
        material_id = assessment_workflow.create_training_material(
            title=f"{topic.title()} Workshop",
            topic=topic,
            audience=audience,
            content_markdown=outline,
        )
        st.success(f"Training material saved: ID {material_id}")
        st.markdown(outline)

    materials = assessment_workflow.list_training_materials()
    if materials:
        with st.expander("Saved Training Materials", expanded=False):
            for material in materials:
                st.markdown(f"**{material['title']}**")
                st.caption(f"{material.get('topic') or ''} for {material.get('audience') or ''}")


def _select_dataset(key: str):
    datasets = csv_handler.get_datasets()
    if not datasets:
        st.info("Upload a dataset first.")
        return None
    selected_id = st.selectbox(
        "Dataset",
        options=[dataset["id"] for dataset in datasets],
        format_func=lambda dataset_id: _dataset_label(datasets, dataset_id),
        key=key,
    )
    dataset = next(dataset for dataset in datasets if dataset["id"] == selected_id)
    try:
        profile = smart_guidance.build_profile(dataset)
        if profile:
            smart_guidance.display_profile_summary(profile)
    except Exception:
        pass
    return dataset


def _profiles_for_datasets(datasets, selected_dataset_ids):
    profiles = []
    for dataset in datasets:
        if dataset["id"] not in selected_dataset_ids:
            continue
        caps = dataset.get("analysis_capabilities") or {}
        stats = caps.get("stats") or {}
        profiles.append(
            {
                "dataset_type": dataset["dataset_type"],
                "has_text": bool(stats.get("text_cols")),
                "has_numeric": bool(stats.get("numeric_cols")),
            }
        )
    return profiles


def _display_benchmark_summary(summary):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Mean", f"{summary['mean']:.2f}")
    with col2:
        st.metric("Median", f"{summary['median']:.2f}")
    with col3:
        st.metric("Minimum", f"{summary['min']:.2f}")
    with col4:
        st.metric("Maximum", f"{summary['max']:.2f}")

    if summary.get("target"):
        target = summary["target"]
        st.success(
            f"{target['institution']} ranks #{target['rank']} of {summary['count']} "
            f"for {summary['metric']} (percentile {target['percentile']})."
        )

    st.markdown("#### Top Performers")
    st.dataframe(pd.DataFrame(summary["top_performers"]), use_container_width=True)


def _dataset_label(datasets, dataset_id):
    dataset = next(dataset for dataset in datasets if dataset["id"] == dataset_id)
    return f"{dataset['name']} ({dataset['dataset_type']}, ID {dataset['id']})"


def _split_csv(value: str):
    return [item.strip() for item in value.split(",") if item.strip()]

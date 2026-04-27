"""Workflow-oriented data section for Streamlit."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from modules import csv_handler
from modules.rag_query import DependencyUnavailableError, RAGQuery, get_rag_dependency_status
from ui import context_ui, data_upload_ui


def show_data_page() -> None:
    """Display dataset import, management, privacy, metadata, and indexing status."""
    st.title("Data")
    st.caption("Import, review, describe, index, archive, and govern assessment datasets.")
    context_ui.show_context_strip()

    tabs = st.tabs(["Import", "Datasets", "PII Review", "Metadata", "Indexing"])
    with tabs[0]:
        data_upload_ui._show_upload_tab()
    with tabs[1]:
        data_upload_ui._show_manage_tab()
    with tabs[2]:
        _show_pii_review_tab()
    with tabs[3]:
        _show_metadata_tab()
    with tabs[4]:
        _show_indexing_tab()


def _show_pii_review_tab() -> None:
    st.markdown("### PII Review")
    st.info(
        "Upload-time PII blocking and redacted import are planned for this workflow. "
        "Until then, generated outputs continue to use existing PII redaction safeguards."
    )
    st.markdown("#### Target Review States")
    st.markdown(
        "- Blocking: high-risk identifiers require redacted import or admin override.\n"
        "- Needs review: possible identifiers should be confirmed before import.\n"
        "- Informational: low-risk findings are recorded in provenance."
    )


def _show_metadata_tab() -> None:
    st.markdown("### Metadata Readiness")
    datasets = csv_handler.get_datasets()
    if not datasets:
        st.info("No active datasets yet. Import a dataset to begin metadata review.")
        return

    rows = []
    for dataset in datasets:
        missing = [
            field
            for field in ("title", "description", "source", "usage_notes", "ethical_considerations")
            if not dataset.get(field)
        ]
        rows.append(
            {
                "id": dataset["id"],
                "name": dataset["name"],
                "type": dataset["dataset_type"],
                "missing_fields": ", ".join(missing) if missing else "complete",
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _show_indexing_tab() -> None:
    st.markdown("### Indexing Status")
    datasets = csv_handler.get_datasets()
    if not datasets:
        st.info("No active datasets yet. Import a dataset to create an indexing job.")
        return

    rows = [
        {
            "id": dataset["id"],
            "name": dataset["name"],
            "status": dataset.get("indexing_status") or "pending",
            "indexed_at": dataset.get("indexed_at") or "",
            "error": dataset.get("indexing_error") or "",
        }
        for dataset in datasets
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    pending = [
        dataset
        for dataset in datasets
        if (dataset.get("indexing_status") or "pending") not in {"completed", "indexed"}
    ]
    if not pending:
        st.success("All datasets are indexed and ready for Ask.")
        return

    st.markdown("#### Index Pending Datasets")
    st.caption("Indexing makes uploaded rows searchable from Ask.")

    selected_ids = st.multiselect(
        "Datasets to index",
        options=[dataset["id"] for dataset in pending],
        default=[dataset["id"] for dataset in pending],
        format_func=lambda dataset_id: next(
            dataset["name"] for dataset in pending if dataset["id"] == dataset_id
        ),
    )

    if st.button("Index Selected Datasets", type="primary", use_container_width=True, disabled=not selected_ids):
        try:
            rag_engine = st.session_state.get("rag_engine")
            if rag_engine is None:
                rag_engine = RAGQuery()
                st.session_state.rag_engine = rag_engine
        except DependencyUnavailableError as exc:
            st.error("Indexing is unavailable because RAG dependencies are missing.")
            st.markdown(str(exc))
            for status in get_rag_dependency_status().values():
                availability = "Available" if status["available"] else "Missing"
                st.markdown(f"- `{status['package']}`: {availability}")
            return
        except Exception as exc:
            st.error(f"Could not initialize indexing engine: {exc}")
            return

        progress = st.progress(0)
        indexed = []
        failed = []
        for index, dataset_id in enumerate(selected_ids, start=1):
            dataset_name = next(dataset["name"] for dataset in pending if dataset["id"] == dataset_id)
            try:
                doc_count = rag_engine.index_dataset(dataset_id)
                indexed.append(f"{dataset_name} ({doc_count} new docs)")
            except Exception as exc:
                failed.append(f"{dataset_name}: {exc}")
            progress.progress(index / len(selected_ids))

        if indexed:
            st.success("Indexed: " + ", ".join(indexed))
        if failed:
            for failure in failed:
                st.error(failure)
        st.rerun()

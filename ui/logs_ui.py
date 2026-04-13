"""
Logs & Monitoring UI Module

This module provides the user interface for viewing application logs, errors,
performance metrics, and audit trails.
"""

import streamlit as st
import pandas as pd
from modules.logging_service import get_recent_logs, get_error_summary, get_operation_stats, get_access_log_summary, APP_LOG_FILE, ERROR_LOG_FILE


def show_logs_page():
    """Logs & Monitoring dashboard - application logs, errors, performance, and audit trail."""
    st.title("Logs & Monitoring")
    st.markdown("Real-time visibility into application activity, errors, and performance.")

    # Controls
    col_h, col_r = st.columns([4, 1])
    with col_r:
        if st.button("Refresh", use_container_width=True):
            st.rerun()

    hours = st.select_slider(
        "Time window",
        options=[1, 6, 12, 24, 48, 168],
        value=24,
        format_func=lambda h: f"Last {h}h" if h < 168 else "Last 7 days",
    )

    tab_overview, tab_logs, tab_errors, tab_perf, tab_audit = st.tabs(
        ["Overview", "Application Logs", "Errors", "Performance", "Audit Trail"]
    )

    # Overview
    with tab_overview:
        _display_overview_tab(hours)

    # Application Logs
    with tab_logs:
        _display_logs_tab()

    # Errors
    with tab_errors:
        _display_errors_tab()

    # Performance
    with tab_perf:
        _display_performance_tab(hours)

    # Audit Trail
    with tab_audit:
        _display_audit_tab(hours)

    # Log file links
    st.markdown("---")
    st.markdown("#### Log Files on Disk")
    st.code(f"Application log : {APP_LOG_FILE}\nErrors only     : {ERROR_LOG_FILE}")


def _display_overview_tab(hours):
    """Display overview tab with summary metrics."""
    logs = get_recent_logs(limit=500)
    errors = get_error_summary(hours=hours)
    ops = get_operation_stats(hours=hours)

    total = len(logs)
    err_count = sum(r["count"] for r in errors)
    warn_count = sum(1 for l in logs if l.get("level") == "WARNING")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Log Entries", total)
    c2.metric("Errors (window)", err_count, delta=None)
    c3.metric("Warnings (all)", warn_count)
    c4.metric("Operations Tracked", len(ops))

    if ops:
        st.markdown("#### Operation Summary")
        ops_df = pd.DataFrame(ops)
        st.dataframe(ops_df, use_container_width=True, hide_index=True)

    if errors:
        st.markdown("#### Error Breakdown by Module")
        err_df = pd.DataFrame(errors)
        st.dataframe(err_df, use_container_width=True, hide_index=True)
    else:
        st.success(f"No errors in the last {hours}h.")


def _display_logs_tab():
    """Display application logs tab with filtering."""
    col_lv, col_mod = st.columns(2)
    with col_lv:
        level_filter = st.selectbox(
            "Level", ["All", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )
    with col_mod:
        module_filter = st.text_input("Module contains", placeholder="e.g. csv_handler")

    logs = get_recent_logs(
        limit=300,
        level=None if level_filter == "All" else level_filter,
        module=module_filter or None,
    )

    if not logs:
        st.info("No log entries match the current filters.")
    else:
        df = pd.DataFrame(logs)[["timestamp", "level", "module", "function", "message"]]
        # Colour-code level column
        def _colour(val):
            colours = {"ERROR": "background-color:#ffd6d6", "CRITICAL": "background-color:#ff9999",
                       "WARNING": "background-color:#fff3cd", "INFO": "", "DEBUG": "color:#888"}
            return colours.get(val, "")
        st.dataframe(
            df.style.map(_colour, subset=["level"]),
            use_container_width=True,
            hide_index=True,
        )

        # Download
        st.download_button(
            "Download as CSV",
            data=df.to_csv(index=False),
            file_name="app_logs.csv",
            mime="text/csv",
        )


def _display_errors_tab():
    """Display errors tab with detailed error information."""
    error_logs = get_recent_logs(limit=200, level="ERROR")
    critical_logs = get_recent_logs(limit=50, level="CRITICAL")
    all_errors = critical_logs + error_logs

    if not all_errors:
        st.success("No errors recorded.")
    else:
        for entry in all_errors[:50]:
            with st.expander(
                f"[{entry['level']}] {entry['timestamp'][:19]}  -  {entry['module']}.{entry['function']}",
                expanded=False,
            ):
                st.markdown(f"**Message:** {entry['message']}")
                if entry.get("exception"):
                    st.code(entry["exception"], language="python")
                if entry.get("context"):
                    st.json(entry["context"])


def _display_performance_tab(hours):
    """Display performance tab with operation statistics."""
    ops = get_operation_stats(hours=hours)
    if not ops:
        st.info("No performance data yet. Operations are tracked automatically once you use the app.")
    else:
        df = pd.DataFrame(ops)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Bar chart of avg duration
        try:
            import plotly.express as px
            fig = px.bar(
                df,
                x="operation",
                y="avg_ms",
                error_y=None,
                labels={"avg_ms": "Avg duration (ms)", "operation": "Operation"},
                title=f"Average Operation Duration (last {hours}h)",
                color="avg_ms",
                color_continuous_scale="Blues",
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass


def _display_audit_tab(hours):
    """Display audit trail tab with access logs."""
    audit = get_access_log_summary(hours=hours)
    if not audit:
        st.info("No audit events in the selected window.")
    else:
        df = pd.DataFrame(audit)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download Audit Log",
            data=df.to_csv(index=False),
            file_name="audit_log.csv",
            mime="text/csv",
        )

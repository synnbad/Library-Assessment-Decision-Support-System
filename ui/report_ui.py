"""
Report Generation UI Module

This module provides the user interface for generating comprehensive reports
with statistical summaries, visualizations, and qualitative analysis.
"""

import streamlit as st
import json
from modules import csv_handler, report_generator, auth


def show_report_generation_page():
    """Display report generation page with report creation and export."""
    st.title("Report Generation")
    st.markdown("Generate comprehensive reports with statistical summaries and narrative text.")

    datasets = csv_handler.get_datasets()
    if not datasets:
        st.info("No datasets available. Please upload data in the Data Upload section.")
        return

    # Smart dataset labels with capability hints
    def _report_label(d):
        caps = d.get('analysis_capabilities', {})
        analyses = caps.get('analyses', {}) if caps else {}
        badges = []
        if analyses.get('qualitative_sentiment', {}).get('available'): badges.append('qualitative')
        if analyses.get('correlation', {}).get('available'): badges.append('quantitative')
        if analyses.get('rag_query', {}).get('available'): badges.append('queryable')
        tag = ', '.join(badges) if badges else d['dataset_type']
        return f"{d['name']} ({d['dataset_type']}) - {tag}"

    dataset_options = {_report_label(d): d['id'] for d in datasets}

    # Auto-select all datasets by default
    all_labels = list(dataset_options.keys())

    st.markdown("### Report Configuration")
    selected_labels = st.multiselect(
        "Select Datasets to Include",
        options=all_labels,
        default=all_labels,
        help="All datasets are pre-selected. Remove any you don't need."
    )

    if not selected_labels:
        st.info("Please select at least one dataset to generate a report.")
        return

    selected_dataset_ids = [dataset_options[lbl] for lbl in selected_labels]
    selected_datasets = [d for d in datasets if d['id'] in selected_dataset_ids]

    # Auto-detect what options to enable
    has_qualitative = any(
        d.get('analysis_capabilities', {}) and
        d['analysis_capabilities'].get('analyses', {}).get('qualitative_sentiment', {}).get('available')
        for d in selected_datasets
    )
    has_quantitative = any(
        d.get('analysis_capabilities', {}) and
        d['analysis_capabilities'].get('analyses', {}).get('correlation', {}).get('available')
        for d in selected_datasets
    )
    has_viz_data = any(
        d.get('analysis_capabilities', {}) and
        (d['analysis_capabilities'].get('analyses', {}).get('trend', {}).get('available') or
         d['analysis_capabilities'].get('analyses', {}).get('distribution', {}).get('available'))
        for d in selected_datasets
    )

    # Show what was auto-detected
    if has_qualitative or has_quantitative or has_viz_data:
        detected = []
        if has_qualitative: detected.append("qualitative analysis")
        if has_quantitative: detected.append("quantitative analysis")
        if has_viz_data: detected.append("visualizations")
        st.success(f"Auto-detected: {', '.join(detected)} - options pre-checked below.")

    col1, col2, col3 = st.columns(3)
    with col1:
        include_visualizations = st.checkbox("Include Visualizations", value=has_viz_data,
            help="Auto-enabled when usage/circulation data is present")
    with col2:
        include_qualitative = st.checkbox("Include Qualitative Analysis", value=has_qualitative,
            help="Auto-enabled when survey data with text responses is present")
    with col3:
        include_quantitative = st.checkbox("Include Quantitative Analysis", value=has_quantitative,
            help="Auto-enabled when numeric usage/circulation data is present")

    custom_title = st.text_input("Custom Report Title (Optional)",
        placeholder="Leave blank for auto-generated title")

    # Show per-dataset capability summary
    with st.expander("Dataset Capability Summary", expanded=False):
        for d in selected_datasets:
            caps = d.get('analysis_capabilities', {})
            analyses = caps.get('analyses', {}) if caps else {}
            st.markdown(f"**{d['name']}** ({d['dataset_type']})")
            if analyses:
                available = [k for k, v in analyses.items() if v.get('available')]
                unavailable = [k for k, v in analyses.items() if not v.get('available')]
                if available:
                    st.markdown(f"  [OK] {', '.join(available)}")
                if unavailable:
                    st.markdown(f"  [N/A] {', '.join(unavailable)}")
            else:
                st.markdown("  _(capabilities not evaluated - re-upload to evaluate)_")

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        generate_button = st.button("Generate Report", type="primary", use_container_width=True)

    if generate_button:
        progress_bar = st.progress(0)
        status_text = st.empty()
        try:
            status_text.text("Creating report structure...")
            progress_bar.progress(20)

            report = report_generator.create_report(
                dataset_ids=selected_dataset_ids,
                include_viz=include_visualizations,
                include_qualitative=include_qualitative,
                include_quantitative=include_quantitative
            )

            if custom_title:
                report['title'] = custom_title

            progress_bar.progress(100)
            status_text.text("Report generated successfully!")
            st.session_state.current_report = report

            auth.log_access(st.session_state.username,
                f"Generated report for datasets: {', '.join([str(i) for i in selected_dataset_ids])}")
            st.success("Report generated successfully!")
            progress_bar.empty()
            status_text.empty()

        except ValueError as e:
            st.error(f"Error: {str(e)}")
            progress_bar.empty()
            status_text.empty()
            return
        except Exception as e:
            st.error(f"Error generating report: {str(e)}")
            progress_bar.empty()
            status_text.empty()
            return

    # Report preview
    if 'current_report' in st.session_state:
        _display_report_preview(st.session_state.current_report)
    
    # Help section
    _display_help_section()


def _display_report_preview(report):
    """Display the generated report preview."""
    st.markdown("---")
    st.markdown("## Report Preview")
    st.markdown(f"# {report['title']}")
    st.markdown("---")

    with st.expander("Report Metadata", expanded=False):
        st.markdown(f"**Generated:** {report['metadata']['generated_at']}")
        st.markdown(f"**Author:** {report['metadata']['author']}")
        st.markdown(f"**Datasets:** {', '.join(report['metadata']['datasets'])}")

    st.markdown("## Executive Summary")
    st.markdown(report['executive_summary'])
    st.markdown("---")

    st.markdown("## Statistical Summaries")
    for summary in report['statistical_summaries']:
        st.markdown(f"### {summary['dataset_name']}")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Dataset Type", summary['dataset_type'].title())
        with col2:
            st.metric("Total Records", summary['row_count'])

        if summary.get('statistics'):
            st.markdown("#### Key Statistics")
            for metric_name, stats in summary['statistics'].items():
                with st.expander(f"{metric_name}", expanded=False):
                    cols = st.columns(5)
                    if 'mean' in stats: cols[0].metric("Mean", f"{stats['mean']:.2f}")
                    if 'median' in stats: cols[1].metric("Median", f"{stats['median']:.2f}")
                    if 'std_dev' in stats: cols[2].metric("Std Dev", f"{stats['std_dev']:.2f}")
                    if 'count' in stats: cols[3].metric("Count", stats['count'])
                    if 'min' in stats and 'max' in stats:
                        cols[4].metric("Range", f"{stats['min']:.2f} - {stats['max']:.2f}")

        if summary.get('categorical_counts'):
            st.markdown("#### Categorical Distributions")
            for category_name, counts in summary['categorical_counts'].items():
                with st.expander(f"{category_name}", expanded=False):
                    items = list(counts.items())
                    cols = st.columns(min(4, len(items)))
                    for i, (value, count) in enumerate(items):
                        cols[i % len(cols)].metric(str(value), count)
        st.markdown("---")

    if report.get('visualizations'):
        st.markdown("## Visualizations")
        for viz in report['visualizations']:
            st.markdown(f"### {viz['title']}")
            st.plotly_chart(viz['figure'], use_container_width=True)
        st.markdown("---")

    if report.get('qualitative_analysis'):
        st.markdown("## Qualitative Analysis")
        qual = report['qualitative_analysis']
        if qual.get('sentiment_distribution'):
            st.markdown("### Sentiment Distribution")
            sentiment_dist = qual['sentiment_distribution']
            total = sum(sentiment_dist.values())
            cols = st.columns(len(sentiment_dist))
            for i, (sentiment, count) in enumerate(sentiment_dist.items()):
                pct = (count / total * 100) if total > 0 else 0
                cols[i].metric(sentiment.title(), f"{count} ({pct:.1f}%)")
        st.markdown("---")

    if report.get('theme_summaries'):
        st.markdown("## Identified Themes")
        for theme in report['theme_summaries']:
            with st.expander(f"{theme['name']} ({theme['frequency']} occurrences)", expanded=False):
                st.markdown(f"**Keywords:** {', '.join(theme['keywords'])}")
                if theme.get('quotes'):
                    st.markdown("**Representative Quotes:**")
                    for quote in theme['quotes']:
                        st.markdown(f"> {quote}")
        st.markdown("---")

    if report.get('citations'):
        st.markdown("## Data Sources")
        for citation in report['citations']:
            st.markdown(f"- {citation}")
        st.markdown("---")

    st.markdown("## Export Report")
    col1, col2 = st.columns(2)
    with col1:
        try:
            md_bytes, _ = report_generator.export_report(report, format='markdown')
            st.download_button("Download as Markdown", data=md_bytes,
                file_name=f"{report['title'].replace(' ', '_')}.md",
                mime="text/markdown", use_container_width=True)
        except Exception as e:
            st.error(f"Error exporting Markdown: {str(e)}")
    
    with col2:
        try:
            pdf_bytes, actual_format = report_generator.export_report(report, format='pdf')
            
            if actual_format == 'markdown':
                st.warning("PDF export failed. Downloading as Markdown instead.")
                st.download_button(
                    "Download as Markdown (Fallback)",
                    data=pdf_bytes,
                    file_name=f"{report['title'].replace(' ', '_')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                    help="PDF export failed, downloading as Markdown"
                )
            else:
                st.download_button(
                    "Download as PDF",
                    data=pdf_bytes,
                    file_name=f"{report['title'].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    help="Download report as PDF file"
                )
        except Exception as e:
            st.warning("PDF export not available. Please use Markdown export.")
            st.caption(f"Error: {str(e)}")
    
    if report.get('metadata', {}).get('visualization_warnings'):
        st.markdown("---")
        st.warning("Visualization Warnings")
        st.caption("Some visualizations could not be generated due to insufficient data:")
        for warning in report['metadata']['visualization_warnings']:
            st.caption(f"- {warning}")


def _display_help_section():
    """Display help information for report generation."""
    st.markdown("---")
    with st.expander("How to use Report Generation", expanded=False):
        st.markdown("""
        ### Getting Started
        
        1. **Select Datasets**: Choose one or more datasets to include in the report
        2. **Configure Options**: Enable/disable visualizations and qualitative analysis
        3. **Custom Title**: Optionally provide a custom report title
        4. **Generate**: Click "Generate Report" to create the report
        5. **Preview**: Review the report preview on this page
        6. **Export**: Download the report as PDF or Markdown
        
        ### Report Components
        
        A complete report includes:
        - **Title and Metadata**: Report information and dataset details
        - **Executive Summary**: AI-generated narrative explaining key findings
        - **Statistical Summaries**: Descriptive statistics for each dataset
        - **Visualizations**: Charts and graphs (if enabled)
        - **Qualitative Analysis**: Sentiment and theme analysis (if enabled and available)
        - **Theme Summaries**: Identified themes with representative quotes
        - **Data Source Citations**: References to all datasets used
        
        ### Export Formats
        
        - **Markdown**: Text-based format, easy to edit and version control
        - **PDF**: Professional format suitable for sharing with stakeholders
        """)
    
    st.markdown("---")
    st.caption("Tip: Generate multiple reports with different dataset combinations to compare findings across different data sources.")

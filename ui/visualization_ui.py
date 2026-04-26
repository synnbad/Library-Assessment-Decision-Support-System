"""
Visualization UI Module

This module provides the user interface for creating and exporting data visualizations
including bar charts, line charts, and pie charts.
"""

import streamlit as st
import pandas as pd
from modules import csv_handler, data_importer, visualization, auth
from ui import smart_guidance


def show_visualizations_page():
    """Display visualizations page with chart generation and export."""
    st.title("Visualizations")
    st.markdown("Generate charts to visualize trends and patterns in your library data.")

    datasets = csv_handler.get_datasets()
    if not datasets:
        st.info("No datasets available. Please upload data in the Data Upload section.")
        return

    # Smart dataset selector
    def _viz_label(d):
        caps = d.get('analysis_capabilities', {})
        stats = caps.get('stats', {}) if caps else {}
        n_num = len(stats.get('usable_numeric_cols', []))
        has_date = len(stats.get('date_cols', [])) > 0
        hints = []
        if d['dataset_type'] in data_importer.METRIC_DATASET_TYPES:
            if has_date:
                hints.append('trend')
            if n_num >= 1:
                hints.append('bar/pie')
        elif d['dataset_type'] in data_importer.TEXT_DATASET_TYPES:
            hints.append('sentiment chart')
        tag = ', '.join(hints) if hints else d['dataset_type']
        return f"{d['name']} ({d['dataset_type']}) - {tag}"

    dataset_options = {_viz_label(d): d['id'] for d in datasets}
    st.markdown("### Select Dataset")
    selected_label = st.selectbox(
        "Choose a dataset to visualize",
        options=list(dataset_options.keys()),
        key="viz_dataset_selector"
    )
    selected_dataset_id = dataset_options[selected_label]
    selected_dataset = next(d for d in datasets if d['id'] == selected_dataset_id)
    
    # Display dataset info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Dataset", selected_dataset['name'])
    with col2:
        st.metric("Type", selected_dataset['dataset_type'].title())
    with col3:
        st.metric("Rows", selected_dataset['row_count'])

    selected_profile = None
    try:
        selected_profile = smart_guidance.build_profile(selected_dataset)
    except Exception as e:
        st.caption(f"Smart guidance unavailable for this dataset: {e}")

    if selected_profile:
        st.markdown("### Chart Guidance")
        smart_guidance.display_profile_summary(selected_profile)
        chart_ideas = _chart_questions(selected_dataset["name"], selected_profile)
        if chart_ideas:
            smart_guidance.display_question_buttons(
                chart_ideas,
                key_prefix=f"viz_question_{selected_dataset_id}",
                limit=4,
            )

    st.markdown("---")

    # Load full dataset for column inspection
    try:
        preview_df = csv_handler.get_preview(selected_dataset_id, n_rows=selected_dataset['row_count'])

        if preview_df.empty:
            st.error("Unable to load dataset. Please try another dataset.")
            return

        available_columns = preview_df.columns.tolist()
        numeric_cols = preview_df.select_dtypes(include='number').columns.tolist()
        date_cols = [c for c in available_columns if any(t in c.lower() for t in ['date', 'time', 'period', 'month', 'year'])]
        text_cols = [c for c in available_columns if preview_df[c].dtype == object]

        # Auto-detect best chart type and columns
        dtype = selected_dataset['dataset_type']
        if dtype in data_importer.METRIC_DATASET_TYPES and date_cols and numeric_cols:
            default_chart = "Line Chart"
            default_x = date_cols[0]
            default_y = numeric_cols[0]
            st.info(f"Time series detected - Line Chart pre-selected using '{default_x}' vs '{default_y}'.")
        elif dtype in data_importer.METRIC_DATASET_TYPES and numeric_cols:
            default_chart = "Bar Chart"
            default_x = text_cols[0] if text_cols else available_columns[0]
            default_y = numeric_cols[0]
            st.info("Numeric data detected - Bar Chart pre-selected.")
        elif dtype in data_importer.TEXT_DATASET_TYPES:
            default_chart = "Pie Chart"
            sentiment_col = next((c for c in available_columns if 'sentiment' in c.lower()), None)
            default_x = sentiment_col or (text_cols[0] if text_cols else available_columns[0])
            default_y = numeric_cols[0] if numeric_cols else available_columns[0]
            st.info("Survey data detected - Pie Chart pre-selected for distribution view.")
        else:
            default_chart = "Bar Chart"
            default_x = available_columns[0]
            default_y = numeric_cols[0] if numeric_cols else available_columns[0]

        # Chart configuration
        st.markdown("### Chart Configuration")
        col1, col2 = st.columns([1, 1])
        with col1:
            chart_type = st.selectbox(
                "Chart Type",
                options=["Bar Chart", "Line Chart", "Pie Chart"],
                index=["Bar Chart", "Line Chart", "Pie Chart"].index(default_chart),
                help="Auto-selected based on dataset type - change if needed"
            )
        with col2:
            chart_title = st.text_input(
                "Chart Title",
                value=f"{selected_dataset['name']} - {chart_type}",
                help="Enter a title for your chart"
            )

        st.markdown("#### Select Columns")

        if chart_type == "Pie Chart":
            col1, col2 = st.columns(2)
            with col1:
                names_column = st.selectbox(
                    "Labels Column",
                    options=available_columns,
                    index=available_columns.index(default_x) if default_x in available_columns else 0,
                    help="Column containing category names"
                )
            with col2:
                val_opts = numeric_cols if numeric_cols else available_columns
                values_column = st.selectbox(
                    "Values Column",
                    options=val_opts,
                    help="Column containing numeric values"
                )
        else:
            col1, col2 = st.columns(2)
            with col1:
                x_column = st.selectbox(
                    "X-Axis Column",
                    options=available_columns,
                    index=available_columns.index(default_x) if default_x in available_columns else 0,
                    help="Column for x-axis"
                )
            with col2:
                y_opts = numeric_cols if numeric_cols else available_columns
                y_default = y_opts.index(default_y) if default_y in y_opts else 0
                y_column = st.selectbox(
                    "Y-Axis Column",
                    options=y_opts,
                    index=y_default,
                    help="Column for y-axis (numeric)"
                )
            with st.expander("Custom Axis Labels (Optional)", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    x_label = st.text_input("X-Axis Label", value="")
                with col2:
                    y_label = st.text_input("Y-Axis Label", value="")

        st.markdown("---")
        generate_button = st.button("Generate Chart", type="primary", use_container_width=True)

        if generate_button:
            with st.spinner("Generating chart..."):
                try:
                    if chart_type == "Pie Chart":
                        chart_data = preview_df[[names_column, values_column]].copy()
                        if not pd.api.types.is_numeric_dtype(chart_data[values_column]):
                            chart_data = chart_data.groupby(names_column).size().reset_index(name=values_column)
                        else:
                            chart_data = chart_data.groupby(names_column)[values_column].sum().reset_index()
                        fig = visualization.create_pie_chart(chart_data, values=values_column, names=names_column, title=chart_title)
                    else:
                        chart_data = preview_df[[x_column, y_column]].copy()
                        if chart_data[x_column].duplicated().any():
                            chart_data = chart_data.groupby(x_column)[y_column].sum().reset_index()
                        if chart_type == "Bar Chart":
                            fig = visualization.create_bar_chart(chart_data, x=x_column, y=y_column, title=chart_title,
                                x_label=x_label if x_label else None, y_label=y_label if y_label else None)
                        else:
                            fig = visualization.create_line_chart(chart_data, x=x_column, y=y_column, title=chart_title,
                                x_label=x_label if x_label else None, y_label=y_label if y_label else None)

                    st.session_state.current_chart = {
                        'figure': fig, 'title': chart_title, 'dataset_name': selected_dataset['name']
                    }
                    auth.log_access(st.session_state.username,
                        f"Generated {chart_type} for dataset: {selected_dataset['name']} (ID: {selected_dataset_id})")
                    st.success("Chart generated successfully!")

                except Exception as e:
                    st.error(f"Error generating chart: {str(e)}")

        if 'current_chart' in st.session_state:
            st.markdown("---")
            st.markdown("### Generated Chart")
            st.plotly_chart(st.session_state.current_chart['figure'], use_container_width=True)
            st.markdown("### Continue in Query")
            smart_guidance.display_question_buttons(
                [
                    f"Explain the chart titled {st.session_state.current_chart['title']} in plain English.",
                    f"What caveats should I mention with {st.session_state.current_chart['title']}?",
                    f"Turn {st.session_state.current_chart['title']} into a report finding.",
                ],
                key_prefix="viz_generated_chart",
                limit=3,
            )

            st.markdown("### Export Chart")
            col1, col2 = st.columns(2)
            with col1:
                try:
                    png_bytes = visualization.export_chart(st.session_state.current_chart['figure'],
                        st.session_state.current_chart['title'], format='png')
                    st.download_button("Download as PNG", data=png_bytes,
                        file_name=f"{st.session_state.current_chart['title']}.png",
                        mime="image/png", use_container_width=True)
                except Exception:
                    st.warning("PNG export not available. Use HTML instead.")
            with col2:
                html_bytes = visualization.export_chart(st.session_state.current_chart['figure'],
                    st.session_state.current_chart['title'], format='html')
                st.download_button("Download as HTML", data=html_bytes,
                    file_name=f"{st.session_state.current_chart['title']}.html",
                    mime="text/html", use_container_width=True)

    except Exception as e:
        st.error(f"Error loading dataset: {str(e)}")
        return
    
    # Help section
    st.markdown("---")
    with st.expander("How to use Visualizations", expanded=False):
        st.markdown("""
        ### Getting Started
        
        1. **Select Dataset**: Choose a dataset from the dropdown
        2. **Choose Chart Type**: Select bar chart, line chart, or pie chart
        3. **Configure Columns**: Select which columns to visualize
        4. **Generate**: Click "Generate Chart" to create the visualization
        5. **Export**: Download the chart as PNG or HTML
        
        ### Chart Types
        
        - **Bar Chart**: Best for comparing categorical data (e.g., usage by department)
        - **Line Chart**: Best for time series data (e.g., trends over time)
        - **Pie Chart**: Best for showing proportions (e.g., distribution of responses)
        
        ### Column Selection
        
        - **Bar/Line Charts**: Select X-axis (categories or time) and Y-axis (numeric values)
        - **Pie Charts**: Select Labels (category names) and Values (numeric values)
        - If your data has duplicate entries, they will be automatically aggregated
        
        ### Export Formats
        
        - **PNG**: Static image suitable for reports and presentations
        - **HTML**: Interactive chart that can be opened in a web browser
        
        ### Tips
        
        - Use descriptive chart titles to make your visualizations clear
        - For time series data, ensure your date column is properly formatted
        - Pie charts work best with 5-10 categories
        - Bar charts can handle more categories but may need rotation for readability
        """)
    
    st.markdown("---")
    st.caption("Tip: Use custom axis labels to make your charts more professional and easier to understand.")


def _chart_questions(dataset_name: str, profile):
    """Suggest chart-oriented questions for the selected dataset."""
    questions = []
    if profile.is_time_ready and profile.is_numeric_ready:
        questions.append(f"What trend chart should I make for {dataset_name}?")
    if profile.is_numeric_ready and profile.category_columns:
        questions.append(f"What categories should I compare visually in {dataset_name}?")
    if profile.is_text_ready:
        questions.append(f"What distribution chart would summarize {dataset_name}?")
    if profile.warnings:
        questions.append(f"What chart limitations should I note for {dataset_name}?")
    return questions

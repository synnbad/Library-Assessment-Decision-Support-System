"""
Qualitative Analysis UI Module

This module provides the user interface for qualitative analysis including
sentiment analysis and theme extraction from survey responses.
"""

import streamlit as st
import pandas as pd
from modules import csv_handler, qualitative_analysis, visualization, auth


def show_qualitative_analysis_page():
    """Display qualitative analysis page with sentiment and theme analysis."""
    st.title("Qualitative Analysis")
    st.markdown("Analyze open-ended survey responses for sentiment and themes.")
    
    # Get available datasets
    datasets = csv_handler.get_datasets()

    if not datasets:
        st.info("No datasets available. Please upload data in the Data Upload section.")
        return

    # Classify datasets and build selector with hints
    def _label(d):
        info = csv_handler.classify_dataset_for_analysis(d)
        tag = "Recommended" if info['recommended'] == 'qualitative' else "Not ideal"
        return f"{d['name']} (ID: {d['id']}, {d['dataset_type']}) - {tag}"

    dataset_options = {_label(d): d['id'] for d in datasets}
    survey_datasets = [d for d in datasets if d['dataset_type'] == 'survey']

    # Default to first survey dataset if available
    default_label = next((_label(d) for d in survey_datasets), list(dataset_options.keys())[0])

    st.markdown("### Select Dataset")
    selected_label = st.selectbox(
        "Choose a dataset to analyze",
        options=list(dataset_options.keys()),
        index=list(dataset_options.keys()).index(default_label),
        key="analysis_dataset_selector"
    )

    selected_dataset_id = dataset_options[selected_label]
    selected_dataset = next(d for d in datasets if d['id'] == selected_dataset_id)
    analysis_info = csv_handler.classify_dataset_for_analysis(selected_dataset)

    # Show suitability banner
    if analysis_info['recommended'] == 'qualitative':
        st.success(analysis_info['reason'])
    else:
        st.warning(f"{analysis_info['reason']} Results may be limited.")

    # Display dataset info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Dataset", selected_dataset['name'])
    with col2:
        st.metric("Total Rows", selected_dataset['row_count'])
    with col3:
        st.metric("Upload Date", selected_dataset['upload_date'][:10])
    
    st.markdown("---")
    
    # Analysis options
    st.markdown("### Analysis Options")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        n_themes = st.slider(
            "Number of themes to identify",
            min_value=2,
            max_value=10,
            value=5,
            help="Select how many themes to extract from the responses"
        )
    
    with col2:
        st.markdown("")
        st.markdown("")
        analyze_button = st.button("Run Analysis", type="primary", use_container_width=True)
    
    # Run analysis
    if analyze_button:
        with st.spinner("Analyzing responses... This may take a moment."):
            try:
                sentiment_results = qualitative_analysis.analyze_dataset_sentiment(selected_dataset_id)
                theme_results = qualitative_analysis.extract_themes(selected_dataset_id, n_themes)
                
                st.session_state.analysis_results = {
                    'dataset_id': selected_dataset_id,
                    'dataset_name': selected_dataset['name'],
                    'sentiment': sentiment_results,
                    'themes': theme_results
                }
                
                auth.log_access(
                    st.session_state.username,
                    f"Performed qualitative analysis on dataset: {selected_dataset['name']} (ID: {selected_dataset_id})"
                )
                
                st.success("Analysis completed successfully!")
                
            except ValueError as e:
                st.error(f"{str(e)}")
                return
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
                return
    
    # Display results if available
    if 'analysis_results' in st.session_state and st.session_state.analysis_results['dataset_id'] == selected_dataset_id:
        _display_analysis_results(st.session_state.analysis_results)
    
    # Help section
    _display_help_section()


def _display_analysis_results(results):
    """Display sentiment and theme analysis results."""
    sentiment_results = results['sentiment']
    theme_results = results['themes']
    
    st.markdown("---")
    st.markdown("## Analysis Results")
    
    # Sentiment Analysis Section
    st.markdown("### Sentiment Distribution")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Responses", sentiment_results['total_responses'])
    with col2:
        st.metric("Positive", f"{sentiment_results['distribution']['positive']:.1%}")
    with col3:
        st.metric("Neutral", f"{sentiment_results['distribution']['neutral']:.1%}")
    with col4:
        st.metric("Negative", f"{sentiment_results['distribution']['negative']:.1%}")
    
    # Sentiment distribution chart
    sentiment_df = pd.DataFrame([
        {"Sentiment": "Positive", "Count": sentiment_results['distribution']['positive'] * sentiment_results['total_responses']},
        {"Sentiment": "Neutral", "Count": sentiment_results['distribution']['neutral'] * sentiment_results['total_responses']},
        {"Sentiment": "Negative", "Count": sentiment_results['distribution']['negative'] * sentiment_results['total_responses']}
    ])
    
    sentiment_chart = visualization.create_bar_chart(
        sentiment_df,
        x="Sentiment",
        y="Count",
        title="Sentiment Distribution",
        x_label="Sentiment Category",
        y_label="Number of Responses"
    )
    st.plotly_chart(sentiment_chart, use_container_width=True)
    
    # Theme Analysis Section
    st.markdown("---")
    st.markdown("### Identified Themes")
    
    st.markdown(f"**{len(theme_results['themes'])} themes identified from {theme_results['total_responses']} responses**")
    
    # Display each theme
    for theme in theme_results['themes']:
        with st.expander(f"**{theme['theme_name']}** ({theme['frequency']} responses, {theme['percentage']:.1f}%)", expanded=True):
            # Theme details
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**Keywords:**")
                st.markdown(", ".join(theme['keywords']))
                
                st.markdown("**Frequency:**")
                st.markdown(f"{theme['frequency']} responses ({theme['percentage']:.1f}%)")
            
            with col2:
                st.markdown("**Sentiment Distribution:**")
                st.markdown(f"- Positive: {theme['sentiment_distribution']['positive']:.1%}")
                st.markdown(f"- Neutral: {theme['sentiment_distribution']['neutral']:.1%}")
                st.markdown(f"- Negative: {theme['sentiment_distribution']['negative']:.1%}")
            
            # Representative quotes
            if theme['representative_quotes']:
                st.markdown("**Representative Quotes:**")
                for i, quote in enumerate(theme['representative_quotes'], 1):
                    st.markdown(f"{i}. *\"{quote}\"*")
    
    # Theme frequency chart
    st.markdown("---")
    st.markdown("### Theme Frequency Distribution")
    
    theme_df = pd.DataFrame([
        {"Theme": theme['theme_name'], "Frequency": theme['frequency']}
        for theme in theme_results['themes']
    ])
    
    theme_chart = visualization.create_bar_chart(
        theme_df,
        x="Theme",
        y="Frequency",
        title="Theme Frequency Distribution",
        x_label="Theme",
        y_label="Number of Responses"
    )
    st.plotly_chart(theme_chart, use_container_width=True)
    
    # Export section
    _display_export_section(results, sentiment_chart, theme_chart)


def _display_export_section(results, sentiment_chart, theme_chart):
    """Display export options for analysis results."""
    st.markdown("---")
    st.markdown("### Export Analysis Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Export themes to CSV
        theme_export_df = pd.DataFrame([
            {
                "Theme": theme['theme_name'],
                "Keywords": ", ".join(theme['keywords']),
                "Frequency": theme['frequency'],
                "Percentage": f"{theme['percentage']:.1f}%",
                "Positive_Sentiment": f"{theme['sentiment_distribution']['positive']:.1%}",
                "Neutral_Sentiment": f"{theme['sentiment_distribution']['neutral']:.1%}",
                "Negative_Sentiment": f"{theme['sentiment_distribution']['negative']:.1%}"
            }
            for theme in results['themes']['themes']
        ])
        
        csv_data = theme_export_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Export Themes (CSV)",
            data=csv_data,
            file_name=f"themes_{results['dataset_name']}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Export sentiment chart
        sentiment_chart_bytes = visualization.export_chart(sentiment_chart, "sentiment_distribution", format='html')
        st.download_button(
            "Export Sentiment Chart",
            data=sentiment_chart_bytes,
            file_name=f"sentiment_chart_{results['dataset_name']}.html",
            mime="text/html",
            use_container_width=True
        )
    
    with col3:
        # Export theme chart
        theme_chart_bytes = visualization.export_chart(theme_chart, "theme_frequency", format='html')
        st.download_button(
            "Export Theme Chart",
            data=theme_chart_bytes,
            file_name=f"theme_chart_{results['dataset_name']}.html",
            mime="text/html",
            use_container_width=True
        )


def _display_help_section():
    """Display help information for qualitative analysis."""
    st.markdown("---")
    with st.expander("How to use Qualitative Analysis", expanded=False):
        st.markdown("""
        ### Getting Started
        
        1. **Select Dataset**: Choose a survey dataset from the dropdown
        2. **Set Options**: Choose the number of themes to identify (2-10)
        3. **Run Analysis**: Click "Run Analysis" to perform sentiment and theme analysis
        4. **Review Results**: Examine sentiment distribution and identified themes
        5. **Export**: Download analysis results as CSV or charts as HTML
        
        ### Sentiment Analysis
        
        The system analyzes each response and categorizes it as:
        - **Positive**: Responses with positive sentiment (polarity > 0.1)
        - **Neutral**: Responses with neutral sentiment (polarity between -0.1 and 0.1)
        - **Negative**: Responses with negative sentiment (polarity < -0.1)
        
        ### Theme Identification
        
        The system uses TF-IDF keyword extraction and K-means clustering to identify
        recurring themes in the responses. For each theme, you'll see:
        - **Keywords**: Top keywords associated with the theme
        - **Frequency**: Number of responses in this theme
        - **Sentiment Distribution**: Sentiment breakdown for responses in this theme
        - **Representative Quotes**: Example responses that exemplify the theme
        
        ### Minimum Requirements
        
        - At least 10 responses are required for analysis
        - At least as many responses as themes requested (e.g., 5 responses for 5 themes)
        
        ### Export Options
        
        - **CSV Export**: Download theme data with keywords, frequencies, and sentiment
        - **Chart Export**: Download interactive HTML charts for presentations
        """)
    
    st.markdown("---")
    st.caption("Tip: Run analysis with different numbers of themes to find the optimal granularity for your data.")

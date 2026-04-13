"""
Quantitative Analysis UI Module

This module provides the user interface for quantitative statistical analysis
including correlation, trend, comparative, and distribution analysis.
"""

import streamlit as st
import pandas as pd
import time
from modules import csv_handler, quantitative_analysis, auth


def show_quantitative_analysis_page():
    """Display quantitative analysis page with statistical analysis and LLM interpretations."""
    st.title("Quantitative Analysis")
    st.markdown("Perform advanced statistical analysis with AI-powered interpretations.")
    
    # Get available datasets
    datasets = csv_handler.get_datasets()
    
    if not datasets:
        st.info("No datasets available. Please upload data in the Data Upload section.")
        return

    # Classify and label datasets
    def _label(d):
        info = csv_handler.classify_dataset_for_analysis(d)
        tag = "Recommended" if info['recommended'] == 'quantitative' else "Not ideal"
        return f"{d['name']} (ID: {d['id']}, {d['dataset_type']}) - {tag}"

    dataset_options = {_label(d): d['id'] for d in datasets}
    quant_datasets = [d for d in datasets if d['dataset_type'] in ('usage', 'circulation')]
    default_label = next((_label(d) for d in quant_datasets), list(dataset_options.keys())[0])

    # Dataset selector
    st.markdown("### Select Dataset")
    selected_label = st.selectbox(
        "Choose a dataset to analyze",
        options=list(dataset_options.keys()),
        index=list(dataset_options.keys()).index(default_label),
        key="quant_dataset_selector"
    )
    
    selected_dataset_id = dataset_options[selected_label]
    selected_dataset = next(d for d in datasets if d['id'] == selected_dataset_id)
    analysis_info = csv_handler.classify_dataset_for_analysis(selected_dataset)

    # Show suitability banner
    if analysis_info['recommended'] == 'quantitative':
        st.success(analysis_info['reason'])
    else:
        st.warning(f"{analysis_info['reason']} Consider using a usage or circulation dataset instead.")
    
    # Display dataset info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Dataset", selected_dataset['name'])
    with col2:
        st.metric("Total Rows", selected_dataset['row_count'])
    with col3:
        st.metric("Type", selected_dataset['dataset_type'])
    
    st.markdown("---")
    
    # Analysis type selector
    st.markdown("### Select Analysis Type")
    analysis_type = st.selectbox(
        "Choose the type of analysis to perform",
        options=[
            "Correlation Analysis",
            "Trend Analysis",
            "Comparative Analysis",
            "Distribution Analysis"
        ],
        key="analysis_type_selector"
    )
    
    # Analysis-specific parameters
    st.markdown("### Configure Parameters")
    
    if analysis_type == "Correlation Analysis":
        _run_correlation_analysis(selected_dataset_id, selected_dataset)
    elif analysis_type == "Trend Analysis":
        _run_trend_analysis(selected_dataset_id, selected_dataset)
    elif analysis_type == "Comparative Analysis":
        _run_comparative_analysis(selected_dataset_id, selected_dataset)
    elif analysis_type == "Distribution Analysis":
        _run_distribution_analysis(selected_dataset_id, selected_dataset)
    
    # Display results if available
    if 'quant_results' in st.session_state:
        _display_analysis_results(st.session_state.quant_results)


def _run_correlation_analysis(dataset_id, dataset):
    """Run correlation analysis."""
    st.markdown("**Correlation Analysis** identifies relationships between numeric variables.")
    
    method = st.selectbox(
        "Correlation Method",
        options=["pearson", "spearman", "kendall"],
        help="Pearson: linear relationships (normal data), Spearman: monotonic relationships (non-normal data), Kendall: ordinal data"
    )
    
    analyze_button = st.button("Run Correlation Analysis", type="primary", use_container_width=True)
    
    if analyze_button:
        with st.spinner("Analyzing correlations... This may take a moment."):
            start_time = time.time()
            try:
                results = quantitative_analysis.calculate_correlation(dataset_id=dataset_id, method=method)
                interpretation_results = quantitative_analysis.generate_interpretation(
                    analysis_type='correlation', results=results, context={'dataset_name': dataset['name']}
                )
                insights_results = quantitative_analysis.generate_insights(
                    dataset_id=dataset_id, analysis_results=results,
                    context={'dataset_name': dataset['name'], 'dataset_type': dataset['dataset_type']}
                )
                recommendations_results = quantitative_analysis.generate_recommendations(
                    analysis_type='correlation', analysis_results=results,
                    context={'dataset_name': dataset['name'], 'dataset_type': dataset['dataset_type']}
                )
                
                results['interpretation'] = interpretation_results.get('interpretation')
                results['insights'] = insights_results.get('insights')
                results['recommendations'] = recommendations_results.get('recommendations')
                
                analysis_id = quantitative_analysis.store_analysis_results(
                    dataset_id=dataset_id, analysis_type='correlation',
                    parameters={'method': method}, results=results
                )
                
                execution_time = time.time() - start_time
                st.session_state.quant_results = {
                    'analysis_id': analysis_id, 'analysis_type': 'correlation',
                    'results': results, 'execution_time': execution_time
                }
                
                auth.log_access(st.session_state.username,
                    f"Performed correlation analysis on dataset: {dataset['name']} (ID: {dataset_id})")
                st.success(f"Analysis completed in {execution_time:.2f} seconds! (Analysis ID: {analysis_id})")
                
            except ValueError as e:
                st.error(f"{str(e)}")
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")


def _run_trend_analysis(dataset_id, dataset):
    """Run trend analysis."""
    st.markdown("**Trend Analysis** identifies patterns and forecasts future values in time series data.")
    
    try:
        df = quantitative_analysis._load_dataset_data(dataset_id)
        columns = df.columns.tolist()
        
        date_column = st.selectbox("Date Column", options=columns,
            help="Select the column containing dates or time periods")
        
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        value_column = st.selectbox("Value Column", options=numeric_columns,
            help="Select the numeric column to analyze for trends")
        
        analyze_button = st.button("Run Trend Analysis", type="primary", use_container_width=True)
        
        if analyze_button:
            with st.spinner("Analyzing trends... This may take a moment."):
                start_time = time.time()
                try:
                    results = quantitative_analysis.calculate_trend(
                        dataset_id=dataset_id, date_column=date_column, value_column=value_column
                    )
                    
                    interpretation_results = quantitative_analysis.generate_interpretation(
                        analysis_type='trend', results=results, context={'dataset_name': dataset['name']}
                    )
                    insights_results = quantitative_analysis.generate_insights(
                        dataset_id=dataset_id, analysis_results=results,
                        context={'dataset_name': dataset['name'], 'dataset_type': dataset['dataset_type']}
                    )
                    recommendations_results = quantitative_analysis.generate_recommendations(
                        analysis_type='trend', analysis_results=results,
                        context={'dataset_name': dataset['name'], 'dataset_type': dataset['dataset_type']}
                    )
                    
                    results['interpretation'] = interpretation_results.get('interpretation')
                    results['insights'] = insights_results.get('insights')
                    results['recommendations'] = recommendations_results.get('recommendations')
                    
                    analysis_id = quantitative_analysis.store_analysis_results(
                        dataset_id=dataset_id, analysis_type='trend',
                        parameters={'date_column': date_column, 'value_column': value_column}, results=results
                    )
                    
                    execution_time = time.time() - start_time
                    st.session_state.quant_results = {
                        'analysis_id': analysis_id, 'analysis_type': 'trend',
                        'results': results, 'execution_time': execution_time
                    }
                    
                    auth.log_access(st.session_state.username,
                        f"Performed trend analysis on dataset: {dataset['name']} (ID: {dataset_id})")
                    st.success(f"Analysis completed in {execution_time:.2f} seconds! (Analysis ID: {analysis_id})")
                    
                except ValueError as e:
                    st.error(f"{str(e)}")
                except Exception as e:
                    st.error(f"Error during analysis: {str(e)}")
                    
    except Exception as e:
        st.error(f"Could not load dataset columns: {str(e)}")


def _run_comparative_analysis(dataset_id, dataset):
    """Run comparative analysis."""
    st.markdown("**Comparative Analysis** compares metrics across different groups or categories.")
    
    try:
        df = quantitative_analysis._load_dataset_data(dataset_id)
        columns = df.columns.tolist()
        
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        value_column = st.selectbox("Value Column", options=numeric_columns,
            help="Select the numeric column to compare across groups")
        
        group_column = st.selectbox("Group Column", options=columns,
            help="Select the column containing group labels")
        
        test_type = st.selectbox("Statistical Test",
            options=["auto", "t-test", "mann-whitney", "anova", "kruskal-wallis"],
            help="Auto: automatically selects based on number of groups and normality")
        
        analyze_button = st.button("Run Comparative Analysis", type="primary", use_container_width=True)
        
        if analyze_button:
            with st.spinner("Comparing groups... This may take a moment."):
                start_time = time.time()
                try:
                    results = quantitative_analysis.perform_comparative_analysis(
                        dataset_id=dataset_id, value_column=value_column, group_column=group_column,
                        test_type=None if test_type == "auto" else test_type
                    )
                    
                    interpretation_results = quantitative_analysis.generate_interpretation(
                        analysis_type='comparative', results=results, context={'dataset_name': dataset['name']}
                    )
                    insights_results = quantitative_analysis.generate_insights(
                        dataset_id=dataset_id, analysis_results=results,
                        context={'dataset_name': dataset['name'], 'dataset_type': dataset['dataset_type']}
                    )
                    recommendations_results = quantitative_analysis.generate_recommendations(
                        analysis_type='comparative', analysis_results=results,
                        context={'dataset_name': dataset['name'], 'dataset_type': dataset['dataset_type']}
                    )
                    
                    results['interpretation'] = interpretation_results.get('interpretation')
                    results['insights'] = insights_results.get('insights')
                    results['recommendations'] = recommendations_results.get('recommendations')
                    
                    analysis_id = quantitative_analysis.store_analysis_results(
                        dataset_id=dataset_id, analysis_type='comparative',
                        parameters={'value_column': value_column, 'group_column': group_column, 'test_type': test_type},
                        results=results
                    )
                    
                    execution_time = time.time() - start_time
                    st.session_state.quant_results = {
                        'analysis_id': analysis_id, 'analysis_type': 'comparative',
                        'results': results, 'execution_time': execution_time
                    }
                    
                    auth.log_access(st.session_state.username,
                        f"Performed comparative analysis on dataset: {dataset['name']} (ID: {dataset_id})")
                    st.success(f"Analysis completed in {execution_time:.2f} seconds! (Analysis ID: {analysis_id})")
                    
                except ValueError as e:
                    st.error(f"{str(e)}")
                except Exception as e:
                    st.error(f"Error during analysis: {str(e)}")
                    
    except Exception as e:
        st.error(f"Could not load dataset columns: {str(e)}")


def _run_distribution_analysis(dataset_id, dataset):
    """Run distribution analysis."""
    st.markdown("**Distribution Analysis** examines data distributions and detects outliers.")
    
    try:
        df = quantitative_analysis._load_dataset_data(dataset_id)
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        
        column = st.selectbox("Column to Analyze", options=numeric_columns,
            help="Select the numeric column to analyze")
        
        outlier_method = st.selectbox("Outlier Detection Method", options=["iqr", "zscore"],
            help="IQR: Interquartile range method (robust to skewed data), Z-score: Standard deviation method (assumes normal distribution)")
        
        analyze_button = st.button("Run Distribution Analysis", type="primary", use_container_width=True)
        
        if analyze_button:
            with st.spinner("Analyzing distribution... This may take a moment."):
                start_time = time.time()
                try:
                    results = quantitative_analysis.analyze_distribution(
                        dataset_id=dataset_id, column=column, outlier_method=outlier_method
                    )
                    
                    interpretation_results = quantitative_analysis.generate_interpretation(
                        analysis_type='distribution', results=results, context={'dataset_name': dataset['name']}
                    )
                    insights_results = quantitative_analysis.generate_insights(
                        dataset_id=dataset_id, analysis_results=results,
                        context={'dataset_name': dataset['name'], 'dataset_type': dataset['dataset_type']}
                    )
                    recommendations_results = quantitative_analysis.generate_recommendations(
                        analysis_type='distribution', analysis_results=results,
                        context={'dataset_name': dataset['name'], 'dataset_type': dataset['dataset_type']}
                    )
                    
                    results['interpretation'] = interpretation_results.get('interpretation')
                    results['insights'] = insights_results.get('insights')
                    results['recommendations'] = recommendations_results.get('recommendations')
                    
                    analysis_id = quantitative_analysis.store_analysis_results(
                        dataset_id=dataset_id, analysis_type='distribution',
                        parameters={'column': column, 'outlier_method': outlier_method}, results=results
                    )
                    
                    execution_time = time.time() - start_time
                    st.session_state.quant_results = {
                        'analysis_id': analysis_id, 'analysis_type': 'distribution',
                        'results': results, 'execution_time': execution_time
                    }
                    
                    auth.log_access(st.session_state.username,
                        f"Performed distribution analysis on dataset: {dataset['name']} (ID: {dataset_id})")
                    st.success(f"Analysis completed in {execution_time:.2f} seconds! (Analysis ID: {analysis_id})")
                    
                except ValueError as e:
                    st.error(f"{str(e)}")
                except Exception as e:
                    st.error(f"Error during analysis: {str(e)}")
                    
    except Exception as e:
        st.error(f"Could not load dataset columns: {str(e)}")


def _display_analysis_results(results_data):
    """Display quantitative analysis results."""
    results = results_data['results']
    analysis_type_key = results_data['analysis_type']
    
    st.markdown("---")
    st.markdown("## Analysis Results")
    
    # Performance metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Analysis ID", results_data['analysis_id'])
    with col2:
        st.metric("Execution Time", f"{results_data['execution_time']:.2f}s")
    
    # Statistical Results
    st.markdown("### Statistical Results")
    
    if analysis_type_key == 'correlation':
        st.markdown(f"**Method:** {results['method'].capitalize()}")
        st.markdown(f"**Observations:** {results['n_observations']}")
        st.markdown(f"**Variables:** {results['n_variables']}")
        
        if results.get('top_correlations'):
            st.markdown("**Top Correlations:**")
            corr_df = pd.DataFrame(results['top_correlations'][:10])
            corr_df['significant'] = corr_df['significant'].map({True: 'Yes', False: 'No'})
            st.dataframe(corr_df[['variable1', 'variable2', 'correlation', 'p_value', 'significant']], use_container_width=True)
            
            try:
                fig = quantitative_analysis.create_correlation_heatmap(results)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not generate visualization: {str(e)}")
    
    elif analysis_type_key == 'trend':
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Trend Direction", results['trend_direction'].capitalize())
        with col2:
            st.metric("R-squared", f"{results['r_squared']:.3f}")
        with col3:
            st.metric("Seasonal Pattern", "Yes" if results.get('seasonal_pattern') else "No")
        
        try:
            fig = quantitative_analysis.create_trend_chart(results)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not generate visualization: {str(e)}")
    
    elif analysis_type_key == 'comparative':
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Test Type", results['test_type'])
        with col2:
            st.metric("P-value", f"{results['p_value']:.4f}")
        with col3:
            st.metric("Significant", "Yes" if results.get('significant') else "No")
        
        if results.get('group_statistics'):
            st.markdown("**Group Statistics:**")
            group_df = pd.DataFrame(results['group_statistics']).T
            st.dataframe(group_df, use_container_width=True)
            
            try:
                fig = quantitative_analysis.create_comparison_boxplot(results)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not generate visualization: {str(e)}")
    
    elif analysis_type_key == 'distribution':
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Skewness", f"{results['skewness']:.3f}")
        with col2:
            st.metric("Kurtosis", f"{results['kurtosis']:.3f}")
        with col3:
            st.metric("Normal", "Yes" if results.get('is_normal') else "No")
        with col4:
            st.metric("Outliers", results['n_outliers'])
        
        try:
            fig = quantitative_analysis.create_distribution_histogram(results)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not generate visualization: {str(e)}")
    
    # LLM-Generated Content
    if results.get('interpretation'):
        st.markdown("### Interpretation")
        st.markdown(results['interpretation'])
    
    if results.get('insights'):
        st.markdown("### Insights")
        st.markdown(results['insights'])
    
    if results.get('recommendations'):
        st.markdown("### Recommendations")
        st.markdown(results['recommendations'])
    
    # Export section
    st.markdown("---")
    st.markdown("### Export Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export Statistical Results (CSV)", use_container_width=True):
            if analysis_type_key == 'correlation' and results.get('top_correlations'):
                export_df = pd.DataFrame(results['top_correlations'])
            elif analysis_type_key == 'comparative' and results.get('group_statistics'):
                export_df = pd.DataFrame(results['group_statistics']).T
            else:
                export_df = pd.DataFrame([results])
            
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"quantitative_analysis_{results_data['analysis_id']}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("Export Full Report (JSON)", use_container_width=True):
            import json
            json_str = json.dumps(results, indent=2, default=str)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name=f"quantitative_analysis_{results_data['analysis_id']}.json",
                mime="application/json"
            )

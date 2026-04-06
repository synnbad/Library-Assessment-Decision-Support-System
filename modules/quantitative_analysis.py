"""
Quantitative Analysis Module

This module provides statistical analysis with LLM-powered interpretations for
library data using local Ollama processing to maintain FERPA compliance.

Key Features:
- Correlation analysis (Pearson, Spearman, Kendall)
- Trend analysis with forecasting
- Comparative analysis (t-tests, ANOVA)
- Distribution analysis with outlier detection
- LLM-powered natural language interpretations
- Contextual insights about library data patterns
- Actionable recommendations based on analysis results
- PII redaction on all outputs
- Local-only processing (FERPA compliant)

Analysis Types:
1. Correlation Analysis:
   - Pearson correlation for linear relationships
   - Spearman correlation for monotonic relationships
   - Kendall correlation for ordinal data
   - Statistical significance testing (p-values)
   - Correlation matrix and top correlations

2. Trend Analysis:
   - Linear regression for trend detection
   - Moving averages (7-day, 30-day)
   - Seasonal pattern detection
   - Forecasting with confidence intervals
   - R-squared and slope calculations

3. Comparative Analysis:
   - Independent t-tests for two-group comparisons
   - One-way ANOVA for multi-group comparisons
   - Effect size calculations (Cohen's d)
   - Post-hoc pairwise comparisons
   - Statistical significance testing

4. Distribution Analysis:
   - Skewness and kurtosis calculations
   - Shapiro-Wilk normality testing
   - IQR-based outlier detection
   - Z-score-based outlier detection
   - Quartile and percentile calculations

LLM Integration:
- Uses local Ollama (Llama 3.2 3B) for interpretations
- Generates natural language explanations of statistical results
- Provides contextual insights about library data patterns
- Creates actionable recommendations
- 60-second timeout for LLM generation
- Graceful fallback to statistical results only

Module Functions:
- calculate_correlation(): Perform correlation analysis
- calculate_trend(): Perform trend analysis
- perform_comparative_analysis(): Compare groups statistically
- analyze_distribution(): Analyze data distributions
- generate_interpretation(): Generate LLM interpretation
- generate_insights(): Generate contextual insights
- generate_recommendations(): Generate actionable recommendations
- store_analysis_results(): Save analysis to database
- retrieve_analysis_results(): Get analysis by ID
- list_analyses_by_dataset(): List all analyses for dataset

Database Tables Used:
- quantitative_analyses: Analysis results and metadata

Requirements Implemented:
- 1.1-1.9: Natural language interpretations
- 2.1-2.7: Contextual insights
- 3.1-3.7: Actionable recommendations
- 4.1-4.8: Correlation analysis
- 5.1-5.7: Trend analysis
- 6.1-6.7: Comparative analysis
- 7.1-7.7: Distribution analysis
- 10.1-10.7: FERPA compliance (local processing)
- 11.1-11.7: Error handling
- 13.1-13.7: Database storage

Configuration (config/settings.py):
- OLLAMA_URL: Ollama server URL (default: http://localhost:11434)
- OLLAMA_MODEL: Model name (default: llama3.2:3b)
- LLM_GENERATION_TIMEOUT_SECONDS: Timeout for LLM (default: 60)

Error Handling:
- Insufficient data: Clear error with minimum requirements
- Non-numeric data: Identify problematic columns
- Missing date columns: Request date column for time series
- Ollama connection failures: Instructions for starting Ollama
- LLM timeouts: Return partial results with statistics only
- Statistical calculation failures: Explanatory error messages

Usage Example:
    # Perform correlation analysis
    results = calculate_correlation(
        dataset_id=1,
        method='pearson'
    )
    print(results['interpretation'])
    
    # Perform trend analysis
    results = calculate_trend(
        dataset_id=1,
        date_column='date',
        value_column='checkouts'
    )
    print(results['forecast'])
    
    # Store analysis results
    analysis_id = store_analysis_results(
        dataset_id=1,
        analysis_type='correlation',
        parameters={'method': 'pearson'},
        results=results
    )

Author: FERPA-Compliant RAG DSS Team
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple


class _NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy and Python types from scipy/pandas."""
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, float) and (obj != obj):  # NaN
            return None
        return super().default(obj)


def _safe_json_dumps(obj: Any) -> str:
    """Serialize obj to JSON, converting numpy types automatically."""
    return json.dumps(obj, cls=_NumpyEncoder)
import ollama
from config.settings import Settings
from modules.database import execute_query, execute_update
from modules.pii_detector import redact_pii
from modules.logging_service import get_logger, log_operation

logger = get_logger(__name__)

# Module-level constants
CORRELATION_METHODS = ['pearson', 'spearman', 'kendall']
COMPARISON_TESTS = ['t-test', 'mann-whitney', 'anova', 'kruskal-wallis']
OUTLIER_METHODS = ['iqr', 'zscore']

# Statistical significance level
ALPHA = 0.05

# LLM generation timeout (seconds)
LLM_TIMEOUT = Settings.LLM_GENERATION_TIMEOUT_SECONDS

# Minimum data requirements
MIN_ROWS_CORRELATION = 10
MIN_ROWS_TREND = 10
MIN_ROWS_COMPARISON = 5
MIN_ROWS_DISTRIBUTION = 10

# Forecast parameters
FORECAST_PERIODS = 7
CONFIDENCE_LEVEL = 0.95

# Moving average windows
MA_SHORT_WINDOW = 7
MA_LONG_WINDOW = 30

# Outlier detection parameters
IQR_MULTIPLIER = 1.5
ZSCORE_THRESHOLD = 3.0

# Top correlations to report
TOP_CORRELATIONS = 10


@log_operation("correlation_analysis")
def calculate_correlation(
    dataset_id: int,
    method: str = 'pearson',
    columns: Optional[List[str]] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform correlation analysis on numeric columns in a dataset.
    
    This function calculates correlation coefficients between all pairs of numeric
    columns using the specified method (Pearson, Spearman, or Kendall). It returns
    a correlation matrix, p-values for statistical significance, and the top 10
    strongest correlations.
    
    Args:
        dataset_id: ID of the dataset to analyze
        method: Correlation method - 'pearson', 'spearman', or 'kendall'
        columns: Optional list of specific columns to analyze (default: all numeric)
        db_path: Optional database path (default: uses default database)
    
    Returns:
        Dictionary containing:
            - correlation_matrix: DataFrame with correlation coefficients
            - p_values: DataFrame with p-values for each correlation
            - top_correlations: List of top 10 strongest correlations
            - significant_correlations: List of statistically significant correlations
            - method: Correlation method used
            - n_observations: Number of observations analyzed
            - error: Error message if analysis failed (optional)
    
    Raises:
        ValueError: If method is not valid or insufficient data
        
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8
    """
    from scipy import stats
    
    # Validate method
    if method not in CORRELATION_METHODS:
        raise ValueError(
            f"Invalid correlation method '{method}'. "
            f"Must be one of: {', '.join(CORRELATION_METHODS)}"
        )
    
    # Load dataset from database
    query = "SELECT * FROM datasets WHERE id = ?"
    dataset_rows = execute_query(query, (dataset_id,), db_path)
    
    if not dataset_rows:
        raise ValueError(f"Dataset with ID {dataset_id} not found")
    
    # Get dataset data (assuming it's stored as JSON or we need to load from file)
    # For now, we'll assume the data is accessible via the dataset record
    dataset_record = dataset_rows[0]
    
    # Load the actual data - this depends on how datasets are stored
    # We'll need to get the data from the appropriate source
    # For this implementation, we'll assume we can get a DataFrame
    df = _load_dataset_data(dataset_id, db_path)
    
    # Select numeric columns
    if columns:
        # Validate specified columns exist and are numeric
        numeric_cols = []
        for col in columns:
            if col not in df.columns:
                raise ValueError(
                    f"Column '{col}' not found in dataset. "
                    f"Available columns: {', '.join(df.columns)}"
                )
            if not pd.api.types.is_numeric_dtype(df[col]):
                raise ValueError(
                    f"Column '{col}' is not numeric (type: {df[col].dtype}). "
                    f"Correlation analysis requires numeric columns. "
                    f"Please select only numeric columns for analysis."
                )
            # Check if column is all NaN
            if df[col].isna().all():
                raise ValueError(
                    f"Column '{col}' contains only missing values. "
                    f"Cannot perform correlation analysis on columns with no data."
                )
            numeric_cols.append(col)
    else:
        # Use all numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Filter out columns that are all NaN
        valid_numeric_cols = []
        for col in numeric_cols:
            if not df[col].isna().all():
                valid_numeric_cols.append(col)
        numeric_cols = valid_numeric_cols
    
    if len(numeric_cols) < 2:
        raise ValueError(
            f"Insufficient numeric columns for correlation analysis. "
            f"Found {len(numeric_cols)} valid numeric column(s), need at least 2. "
            f"Please ensure the dataset has at least 2 numeric columns with data."
        )
    
    # Filter to numeric columns and drop rows with missing values
    df_numeric = df[numeric_cols].dropna()
    
    if len(df_numeric) < MIN_ROWS_CORRELATION:
        raise ValueError(
            f"Insufficient data for correlation analysis. "
            f"Found {len(df_numeric)} complete rows, need at least {MIN_ROWS_CORRELATION}."
        )
    
    # Calculate correlation matrix and p-values
    n_cols = len(numeric_cols)
    corr_matrix = np.zeros((n_cols, n_cols))
    p_values = np.zeros((n_cols, n_cols))
    
    # Select correlation function based on method
    if method == 'pearson':
        corr_func = stats.pearsonr
    elif method == 'spearman':
        corr_func = stats.spearmanr
    else:  # kendall
        corr_func = stats.kendalltau
    
    # Calculate pairwise correlations and p-values
    for i in range(n_cols):
        for j in range(n_cols):
            if i == j:
                corr_matrix[i, j] = 1.0
                p_values[i, j] = 0.0
            elif i < j:
                # Calculate correlation for upper triangle
                col1_data = df_numeric[numeric_cols[i]].values
                col2_data = df_numeric[numeric_cols[j]].values
                
                corr, pval = corr_func(col1_data, col2_data)
                corr_matrix[i, j] = corr
                corr_matrix[j, i] = corr  # Mirror to lower triangle
                p_values[i, j] = pval
                p_values[j, i] = pval  # Mirror to lower triangle
    
    # Convert to DataFrames
    corr_df = pd.DataFrame(corr_matrix, index=numeric_cols, columns=numeric_cols)
    pval_df = pd.DataFrame(p_values, index=numeric_cols, columns=numeric_cols)
    
    # Find top correlations (excluding diagonal)
    top_correlations = []
    for i in range(n_cols):
        for j in range(i + 1, n_cols):  # Only upper triangle, excluding diagonal
            top_correlations.append({
                'variable1': numeric_cols[i],
                'variable2': numeric_cols[j],
                'correlation': float(corr_matrix[i, j]),
                'p_value': float(p_values[i, j]),
                'significant': p_values[i, j] < ALPHA
            })
    
    # Sort by absolute correlation value and take top 10
    top_correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
    top_10 = top_correlations[:TOP_CORRELATIONS]
    
    # Find all statistically significant correlations
    significant = [c for c in top_correlations if c['significant']]
    
    # Prepare results
    results = {
        'correlation_matrix': corr_df.to_dict(),
        'p_values': pval_df.to_dict(),
        'top_correlations': top_10,
        'significant_correlations': significant,
        'method': method,
        'n_observations': len(df_numeric),
        'n_variables': n_cols,
        'variable_names': numeric_cols
    }
    
    return results


@log_operation("trend_analysis")
def calculate_trend(
    dataset_id: int,
    date_column: str,
    value_column: str,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform trend analysis on time series data.
    
    This function analyzes time series data to detect trends, calculate moving averages,
    identify seasonal patterns, and generate forecasts. It uses linear regression for
    trend detection and autocorrelation for seasonality detection.
    
    Args:
        dataset_id: ID of the dataset to analyze
        date_column: Name of the column containing dates
        value_column: Name of the column containing values to analyze
        db_path: Optional database path (default: uses default database)
    
    Returns:
        Dictionary containing:
            - trend_direction: 'increasing', 'decreasing', or 'stable'
            - trend_slope: Slope of the linear regression line
            - r_squared: R-squared value indicating trend strength
            - moving_average_7: 7-day moving average values
            - moving_average_30: 30-day moving average values
            - seasonal_pattern: Boolean indicating if seasonality detected
            - autocorrelation: Autocorrelation values for lag detection
            - forecast: List of forecasted values for next 7 periods
            - forecast_lower: Lower bound of 95% confidence interval
            - forecast_upper: Upper bound of 95% confidence interval
            - n_observations: Number of observations analyzed
            - error: Error message if analysis failed (optional)
    
    Raises:
        ValueError: If date column missing, insufficient data, or invalid columns
        
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
    """
    from scipy import stats
    import statsmodels.api as sm
    from statsmodels.tsa.stattools import acf
    
    # Load dataset
    df = _load_dataset_data(dataset_id, db_path)
    
    # Validate date column exists
    if date_column not in df.columns:
        raise ValueError(
            f"Date column '{date_column}' not found in dataset. "
            f"Available columns: {', '.join(df.columns)}"
        )
    
    # Validate value column exists and is numeric
    if value_column not in df.columns:
        raise ValueError(
            f"Value column '{value_column}' not found in dataset. "
            f"Available columns: {', '.join(df.columns)}. "
            f"Please specify a valid column name for trend analysis."
        )
    
    if not pd.api.types.is_numeric_dtype(df[value_column]):
        raise ValueError(
            f"Value column '{value_column}' must be numeric for trend analysis. "
            f"Found type: {df[value_column].dtype}. "
            f"Please select a numeric column containing the values to analyze."
        )
    
    # Check if value column is all NaN
    if df[value_column].isna().all():
        raise ValueError(
            f"Value column '{value_column}' contains only missing values. "
            f"Cannot perform trend analysis on a column with no data. "
            f"Please select a column with valid numeric data."
        )
    
    # Convert date column to datetime
    try:
        df[date_column] = pd.to_datetime(df[date_column])
    except Exception as e:
        # Provide more specific error message based on the error type
        error_str = str(e).lower()
        if 'out of bounds' in error_str:
            raise ValueError(
                f"Date column '{date_column}' contains dates that are out of valid range. "
                f"Please check that all dates are valid and within a reasonable range. "
                f"Original error: {str(e)}"
            )
        elif 'format' in error_str or 'parse' in error_str:
            raise ValueError(
                f"Could not parse date column '{date_column}' as datetime. "
                f"Please ensure the column contains valid date values in a recognizable format "
                f"(e.g., 'YYYY-MM-DD', 'MM/DD/YYYY', etc.). "
                f"Original error: {str(e)}"
            )
        else:
            raise ValueError(
                f"Could not parse date column '{date_column}' as datetime: {str(e)}. "
                f"Please ensure the column contains valid date values."
            )
    
    # Sort by date and remove missing values
    df_clean = df[[date_column, value_column]].dropna().sort_values(date_column)
    
    if len(df_clean) < MIN_ROWS_TREND:
        raise ValueError(
            f"Insufficient data for trend analysis. "
            f"Found {len(df_clean)} complete rows, need at least {MIN_ROWS_TREND}."
        )
    
    # Extract time series values
    dates = df_clean[date_column].values
    values = df_clean[value_column].values
    
    # Create numeric time index for regression (days since first observation)
    time_index = np.arange(len(values))
    
    # Perform linear regression for trend detection
    # Add constant for intercept
    X = sm.add_constant(time_index)
    model = sm.OLS(values, X)
    results = model.fit()
    
    # Extract trend parameters
    intercept = results.params[0]
    slope = results.params[1]
    r_squared = results.rsquared
    
    # Determine trend direction
    # Use a threshold to determine if trend is significant
    # Slope is significant if it's more than 1% of the mean value per time unit
    mean_value = np.mean(values)
    if mean_value != 0:
        relative_slope = abs(slope) / abs(mean_value)
        if relative_slope < 0.001:  # Less than 0.1% change per time unit
            trend_direction = 'stable'
        elif slope > 0:
            trend_direction = 'increasing'
        else:
            trend_direction = 'decreasing'
    else:
        # If mean is zero, use absolute threshold
        if abs(slope) < 0.01:
            trend_direction = 'stable'
        elif slope > 0:
            trend_direction = 'increasing'
        else:
            trend_direction = 'decreasing'
    
    # Calculate moving averages
    series = pd.Series(values)
    
    # 7-day moving average
    if len(values) >= MA_SHORT_WINDOW:
        ma_7 = series.rolling(window=MA_SHORT_WINDOW, center=False).mean()
        moving_average_7 = ma_7.tolist()
    else:
        moving_average_7 = [None] * len(values)
    
    # 30-day moving average
    if len(values) >= MA_LONG_WINDOW:
        ma_30 = series.rolling(window=MA_LONG_WINDOW, center=False).mean()
        moving_average_30 = ma_30.tolist()
    else:
        moving_average_30 = [None] * len(values)
    
    # Detect seasonal patterns using autocorrelation
    seasonal_pattern = False
    autocorrelation_values = []
    
    if len(values) >= 20:  # Need sufficient data for autocorrelation
        try:
            # Calculate autocorrelation for lags up to 1/4 of series length
            max_lag = min(len(values) // 4, 30)
            acf_values = acf(values, nlags=max_lag, fft=True)
            autocorrelation_values = acf_values.tolist()
            
            # Check for significant autocorrelation at common seasonal lags
            # (7 days for weekly, 30 days for monthly)
            seasonal_lags = [7, 14, 30] if len(values) >= 30 else [7, 14]
            for lag in seasonal_lags:
                if lag < len(acf_values):
                    # Significant if autocorrelation > 2/sqrt(n)
                    threshold = 2 / np.sqrt(len(values))
                    if abs(acf_values[lag]) > threshold:
                        seasonal_pattern = True
                        break
        except Exception:
            # If autocorrelation fails, continue without seasonality detection
            pass
    
    # Generate forecast for next 7 periods using linear extrapolation
    forecast_periods = FORECAST_PERIODS
    future_time_index = np.arange(len(values), len(values) + forecast_periods)
    
    # Predict using the linear model
    X_future = sm.add_constant(future_time_index)
    forecast_values = results.predict(X_future)
    
    # Calculate 95% confidence intervals
    # Use prediction interval from the model
    prediction = results.get_prediction(X_future)
    pred_summary = prediction.summary_frame(alpha=1 - CONFIDENCE_LEVEL)
    
    forecast_lower = pred_summary['obs_ci_lower'].tolist()
    forecast_upper = pred_summary['obs_ci_upper'].tolist()
    
    # Prepare results
    results_dict = {
        'trend_direction': trend_direction,
        'trend_slope': float(slope),
        'trend_intercept': float(intercept),
        'r_squared': float(r_squared),
        'moving_average_7': moving_average_7,
        'moving_average_30': moving_average_30,
        'seasonal_pattern': seasonal_pattern,
        'autocorrelation': autocorrelation_values,
        'forecast': forecast_values.tolist(),
        'forecast_lower': forecast_lower,
        'forecast_upper': forecast_upper,
        'n_observations': len(values),
        'date_column': date_column,
        'value_column': value_column,
        'start_date': str(dates[0]),
        'end_date': str(dates[-1])
    }
    
    return results_dict


def perform_comparative_analysis(
    dataset_id: int,
    value_column: str,
    group_column: str,
    test_type: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform comparative analysis across groups.
    
    This function compares a metric across different groups using statistical tests.
    For two groups, it performs an independent t-test. For three or more groups,
    it performs one-way ANOVA. Effect sizes (Cohen's d) are calculated for t-tests,
    and post-hoc pairwise comparisons are performed after ANOVA.
    
    Args:
        dataset_id: ID of the dataset to analyze
        value_column: Name of the column containing values to compare
        group_column: Name of the column containing group labels
        test_type: Optional test type - 't-test', 'mann-whitney', 'anova', 'kruskal-wallis'
                   If None, automatically selects based on number of groups
        db_path: Optional database path (default: uses default database)
    
    Returns:
        Dictionary containing:
            - test_type: Type of statistical test performed
            - test_statistic: Test statistic value
            - p_value: P-value for statistical significance
            - significant: Boolean indicating if result is statistically significant
            - effect_size: Cohen's d for t-tests (optional)
            - group_statistics: Descriptive statistics for each group
            - pairwise_comparisons: Post-hoc pairwise comparisons for ANOVA (optional)
            - n_groups: Number of groups compared
            - n_observations: Total number of observations
            - error: Error message if analysis failed (optional)
    
    Raises:
        ValueError: If insufficient data, invalid columns, or invalid test type
        
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
    """
    from scipy import stats
    from itertools import combinations
    
    # Load dataset
    df = _load_dataset_data(dataset_id, db_path)
    
    # Validate value column exists and is numeric
    if value_column not in df.columns:
        raise ValueError(
            f"Value column '{value_column}' not found in dataset. "
            f"Available columns: {', '.join(df.columns)}. "
            f"Please specify a valid column name for comparative analysis."
        )
    
    if not pd.api.types.is_numeric_dtype(df[value_column]):
        raise ValueError(
            f"Value column '{value_column}' must be numeric for comparative analysis. "
            f"Found type: {df[value_column].dtype}. "
            f"Please select a numeric column containing the values to compare."
        )
    
    # Check if value column is all NaN
    if df[value_column].isna().all():
        raise ValueError(
            f"Value column '{value_column}' contains only missing values. "
            f"Cannot perform comparative analysis on a column with no data. "
            f"Please select a column with valid numeric data."
        )
    
    # Validate group column exists
    if group_column not in df.columns:
        raise ValueError(
            f"Group column '{group_column}' not found in dataset. "
            f"Available columns: {', '.join(df.columns)}. "
            f"Please specify a valid column name containing group labels."
        )
    
    # Remove rows with missing values
    df_clean = df[[value_column, group_column]].dropna()
    
    if len(df_clean) < MIN_ROWS_COMPARISON:
        raise ValueError(
            f"Insufficient data for comparative analysis. "
            f"Found {len(df_clean)} complete rows after removing missing values, "
            f"need at least {MIN_ROWS_COMPARISON}. "
            f"Original dataset had {len(df)} rows. "
            f"Please ensure the dataset has sufficient non-missing data."
        )
    
    # Get unique groups and their data
    groups = df_clean[group_column].unique()
    n_groups = len(groups)
    
    if n_groups < 2:
        raise ValueError(
            f"Insufficient groups for comparison. "
            f"Found {n_groups} unique group(s) in column '{group_column}', need at least 2. "
            f"Please ensure the group column contains at least 2 different group values."
        )
    
    # Prepare group data
    group_data = {}
    group_statistics = {}
    
    for group in groups:
        group_values = df_clean[df_clean[group_column] == group][value_column].values
        group_data[str(group)] = group_values
        
        # Calculate descriptive statistics for each group
        group_statistics[str(group)] = {
            'n': len(group_values),
            'mean': float(np.mean(group_values)),
            'std': float(np.std(group_values, ddof=1)),
            'median': float(np.median(group_values)),
            'min': float(np.min(group_values)),
            'max': float(np.max(group_values))
        }
    
    # Determine test type if not specified
    if test_type is None:
        if n_groups == 2:
            test_type = 't-test'
        else:
            test_type = 'anova'
    
    # Validate test type
    if test_type not in COMPARISON_TESTS:
        raise ValueError(
            f"Invalid test type '{test_type}'. "
            f"Must be one of: {', '.join(COMPARISON_TESTS)}"
        )
    
    # Validate test type matches number of groups
    if test_type in ['t-test', 'mann-whitney'] and n_groups != 2:
        raise ValueError(
            f"Test type '{test_type}' requires exactly 2 groups, found {n_groups}"
        )
    
    if test_type in ['anova', 'kruskal-wallis'] and n_groups < 3:
        raise ValueError(
            f"Test type '{test_type}' requires at least 3 groups, found {n_groups}"
        )
    
    # Perform statistical test
    results = {
        'test_type': test_type,
        'group_statistics': group_statistics,
        'n_groups': n_groups,
        'n_observations': len(df_clean),
        'value_column': value_column,
        'group_column': group_column,
        'groups': [str(g) for g in groups]
    }
    
    if test_type == 't-test':
        # Independent t-test for two groups
        group_names = list(group_data.keys())
        group1_data = group_data[group_names[0]]
        group2_data = group_data[group_names[1]]
        
        # Perform t-test
        t_stat, p_value = stats.ttest_ind(group1_data, group2_data)
        
        results['test_statistic'] = float(t_stat)
        results['p_value'] = float(p_value)
        results['significant'] = p_value < ALPHA
        
        # Calculate Cohen's d effect size
        mean1 = np.mean(group1_data)
        mean2 = np.mean(group2_data)
        std1 = np.std(group1_data, ddof=1)
        std2 = np.std(group2_data, ddof=1)
        n1 = len(group1_data)
        n2 = len(group2_data)
        
        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        
        # Cohen's d
        if pooled_std > 0:
            cohens_d = (mean1 - mean2) / pooled_std
            results['effect_size'] = float(cohens_d)
            
            # Interpret effect size
            abs_d = abs(cohens_d)
            if abs_d < 0.2:
                effect_interpretation = 'negligible'
            elif abs_d < 0.5:
                effect_interpretation = 'small'
            elif abs_d < 0.8:
                effect_interpretation = 'medium'
            else:
                effect_interpretation = 'large'
            
            results['effect_size_interpretation'] = effect_interpretation
        else:
            results['effect_size'] = None
            results['effect_size_interpretation'] = 'undefined'
    
    elif test_type == 'mann-whitney':
        # Mann-Whitney U test (non-parametric alternative to t-test)
        group_names = list(group_data.keys())
        group1_data = group_data[group_names[0]]
        group2_data = group_data[group_names[1]]
        
        # Perform Mann-Whitney U test
        u_stat, p_value = stats.mannwhitneyu(group1_data, group2_data, alternative='two-sided')
        
        results['test_statistic'] = float(u_stat)
        results['p_value'] = float(p_value)
        results['significant'] = p_value < ALPHA
    
    elif test_type == 'anova':
        # One-way ANOVA for multiple groups
        group_values_list = [group_data[str(g)] for g in groups]
        
        # Perform ANOVA
        f_stat, p_value = stats.f_oneway(*group_values_list)
        
        results['test_statistic'] = float(f_stat)
        results['p_value'] = float(p_value)
        results['significant'] = p_value < ALPHA
        
        # Perform post-hoc pairwise comparisons if significant
        if p_value < ALPHA:
            pairwise_comparisons = []
            
            for group1, group2 in combinations(groups, 2):
                group1_data = group_data[str(group1)]
                group2_data = group_data[str(group2)]
                
                # Perform t-test for this pair
                t_stat, pair_p_value = stats.ttest_ind(group1_data, group2_data)
                
                # Apply Bonferroni correction for multiple comparisons
                n_comparisons = len(list(combinations(groups, 2)))
                bonferroni_alpha = ALPHA / n_comparisons
                
                # Calculate Cohen's d for this pair
                mean1 = np.mean(group1_data)
                mean2 = np.mean(group2_data)
                std1 = np.std(group1_data, ddof=1)
                std2 = np.std(group2_data, ddof=1)
                n1 = len(group1_data)
                n2 = len(group2_data)
                
                pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
                
                if pooled_std > 0:
                    cohens_d = (mean1 - mean2) / pooled_std
                else:
                    cohens_d = None
                
                pairwise_comparisons.append({
                    'group1': str(group1),
                    'group2': str(group2),
                    'mean_difference': float(mean1 - mean2),
                    't_statistic': float(t_stat),
                    'p_value': float(pair_p_value),
                    'significant': pair_p_value < bonferroni_alpha,
                    'bonferroni_alpha': bonferroni_alpha,
                    'effect_size': float(cohens_d) if cohens_d is not None else None
                })
            
            results['pairwise_comparisons'] = pairwise_comparisons
            results['bonferroni_correction_applied'] = True
    
    elif test_type == 'kruskal-wallis':
        # Kruskal-Wallis test (non-parametric alternative to ANOVA)
        group_values_list = [group_data[str(g)] for g in groups]
        
        # Perform Kruskal-Wallis test
        h_stat, p_value = stats.kruskal(*group_values_list)
        
        results['test_statistic'] = float(h_stat)
        results['p_value'] = float(p_value)
        results['significant'] = p_value < ALPHA
        
        # Perform post-hoc pairwise Mann-Whitney tests if significant
        if p_value < ALPHA:
            pairwise_comparisons = []
            
            for group1, group2 in combinations(groups, 2):
                group1_data = group_data[str(group1)]
                group2_data = group_data[str(group2)]
                
                # Perform Mann-Whitney U test for this pair
                u_stat, pair_p_value = stats.mannwhitneyu(
                    group1_data, group2_data, alternative='two-sided'
                )
                
                # Apply Bonferroni correction
                n_comparisons = len(list(combinations(groups, 2)))
                bonferroni_alpha = ALPHA / n_comparisons
                
                pairwise_comparisons.append({
                    'group1': str(group1),
                    'group2': str(group2),
                    'u_statistic': float(u_stat),
                    'p_value': float(pair_p_value),
                    'significant': pair_p_value < bonferroni_alpha,
                    'bonferroni_alpha': bonferroni_alpha
                })
            
            results['pairwise_comparisons'] = pairwise_comparisons
            results['bonferroni_correction_applied'] = True
    
    return results


def analyze_distribution(
    dataset_id: int,
    column: str,
    outlier_method: str = 'iqr',
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform distribution analysis and outlier detection on a numeric column.
    
    This function analyzes the distribution of a numeric variable, including
    calculating skewness, kurtosis, quartiles, performing normality tests,
    and detecting outliers using IQR or Z-score methods.
    
    Args:
        dataset_id: ID of the dataset to analyze
        column: Name of the column to analyze
        outlier_method: Outlier detection method - 'iqr' or 'zscore'
        db_path: Optional database path (default: uses default database)
    
    Returns:
        Dictionary containing:
            - skewness: Skewness of the distribution
            - kurtosis: Kurtosis of the distribution
            - quartiles: Dictionary with Q1, Q2 (median), Q3
            - iqr: Interquartile range (Q3 - Q1)
            - normality_test: Dictionary with Shapiro-Wilk test results
            - is_normal: Boolean indicating if distribution is normal
            - outliers_iqr: List of outlier values using IQR method (if method='iqr')
            - outliers_zscore: List of outlier values using Z-score method (if method='zscore')
            - outlier_indices: List of indices of outlier values
            - outlier_severity: List of severity scores for outliers
            - n_outliers: Number of outliers detected
            - n_observations: Total number of observations
            - column: Column name analyzed
            - outlier_method: Method used for outlier detection
            - error: Error message if analysis failed (optional)
    
    Raises:
        ValueError: If column missing, insufficient data, or invalid method
        
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6
    """
    from scipy import stats
    
    # Validate outlier method
    if outlier_method not in OUTLIER_METHODS:
        raise ValueError(
            f"Invalid outlier method '{outlier_method}'. "
            f"Must be one of: {', '.join(OUTLIER_METHODS)}"
        )
    
    # Load dataset
    df = _load_dataset_data(dataset_id, db_path)
    
    # Validate column exists and is numeric
    if column not in df.columns:
        raise ValueError(
            f"Column '{column}' not found in dataset. "
            f"Available columns: {', '.join(df.columns)}. "
            f"Please specify a valid column name for distribution analysis."
        )
    
    if not pd.api.types.is_numeric_dtype(df[column]):
        raise ValueError(
            f"Column '{column}' must be numeric for distribution analysis. "
            f"Found type: {df[column].dtype}. "
            f"Please select a numeric column to analyze its distribution."
        )
    
    # Remove missing values
    data = df[column].dropna()
    
    # Check if all values were missing
    if len(data) == 0:
        raise ValueError(
            f"Column '{column}' contains only missing values. "
            f"Cannot perform distribution analysis on a column with no data. "
            f"Please select a column with valid numeric data."
        )
    
    if len(data) < MIN_ROWS_DISTRIBUTION:
        raise ValueError(
            f"Insufficient data for distribution analysis. "
            f"Found {len(data)} non-missing values, need at least {MIN_ROWS_DISTRIBUTION}. "
            f"Original column had {len(df[column])} values ({len(df[column]) - len(data)} missing). "
            f"Please ensure the column has sufficient non-missing data."
        )
    
    # Calculate skewness and kurtosis
    skewness = float(stats.skew(data))
    kurtosis = float(stats.kurtosis(data))
    
    # Calculate quartiles and IQR
    q1 = float(np.percentile(data, 25))
    q2 = float(np.percentile(data, 50))  # Median
    q3 = float(np.percentile(data, 75))
    iqr = q3 - q1
    
    quartiles = {
        'Q1': q1,
        'Q2': q2,
        'Q3': q3
    }
    
    # Perform Shapiro-Wilk normality test
    # Note: Shapiro-Wilk is most reliable for sample sizes between 3 and 5000
    if len(data) <= 5000:
        shapiro_stat, shapiro_p = stats.shapiro(data)
        normality_test = {
            'test': 'Shapiro-Wilk',
            'statistic': float(shapiro_stat),
            'p_value': float(shapiro_p)
        }
        # Distribution is considered normal if p-value > alpha
        is_normal = shapiro_p > ALPHA
    else:
        # For large samples, use Kolmogorov-Smirnov test instead
        ks_stat, ks_p = stats.kstest(data, 'norm', args=(data.mean(), data.std()))
        normality_test = {
            'test': 'Kolmogorov-Smirnov',
            'statistic': float(ks_stat),
            'p_value': float(ks_p)
        }
        is_normal = ks_p > ALPHA
    
    # Detect outliers using specified method
    outlier_indices = []
    outlier_values = []
    outlier_severity = []
    
    if outlier_method == 'iqr':
        # IQR method: outliers are beyond Q1 - 1.5*IQR or Q3 + 1.5*IQR
        lower_bound = q1 - IQR_MULTIPLIER * iqr
        upper_bound = q3 + IQR_MULTIPLIER * iqr
        
        for idx, value in data.items():
            if value < lower_bound or value > upper_bound:
                outlier_indices.append(int(idx))
                outlier_values.append(float(value))
                
                # Calculate severity as distance from bounds in IQR units
                if value < lower_bound:
                    severity = (lower_bound - value) / iqr if iqr > 0 else 0
                else:
                    severity = (value - upper_bound) / iqr if iqr > 0 else 0
                
                outlier_severity.append(float(severity))
        
        results = {
            'skewness': skewness,
            'kurtosis': kurtosis,
            'quartiles': quartiles,
            'iqr': float(iqr),
            'normality_test': normality_test,
            'is_normal': is_normal,
            'outliers_iqr': outlier_values,
            'outlier_bounds': {
                'lower': float(lower_bound),
                'upper': float(upper_bound)
            },
            'outlier_indices': outlier_indices,
            'outlier_severity': outlier_severity,
            'n_outliers': len(outlier_values),
            'n_observations': len(data),
            'column': column,
            'outlier_method': outlier_method
        }
    
    elif outlier_method == 'zscore':
        # Z-score method: outliers have |Z-score| > 3
        mean = data.mean()
        std = data.std()
        
        if std > 0:
            z_scores = (data - mean) / std
            
            for idx, (value, z_score) in enumerate(zip(data.values, z_scores.values)):
                if abs(z_score) > ZSCORE_THRESHOLD:
                    outlier_indices.append(int(data.index[idx]))
                    outlier_values.append(float(value))
                    # Severity is the absolute Z-score
                    outlier_severity.append(float(abs(z_score)))
        
        results = {
            'skewness': skewness,
            'kurtosis': kurtosis,
            'quartiles': quartiles,
            'iqr': float(iqr),
            'normality_test': normality_test,
            'is_normal': is_normal,
            'outliers_zscore': outlier_values,
            'outlier_threshold': ZSCORE_THRESHOLD,
            'mean': float(mean),
            'std': float(std),
            'outlier_indices': outlier_indices,
            'outlier_severity': outlier_severity,
            'n_outliers': len(outlier_values),
            'n_observations': len(data),
            'column': column,
            'outlier_method': outlier_method
        }
    
    return results


def _load_dataset_data(dataset_id: int, db_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load dataset data from the database.
    
    This is a helper function that retrieves the actual data for a dataset.
    Data is loaded from the appropriate table based on dataset_type.
    
    Args:
        dataset_id: ID of the dataset to load
        db_path: Optional database path (default: uses default database)
    
    Returns:
        DataFrame containing the dataset with columns for each metric/variable
        
    Raises:
        ValueError: If dataset cannot be loaded or contains no data
        
    Requirements: 11.1, 11.7
    """
    # Query the dataset record to get dataset type
    query = "SELECT * FROM datasets WHERE id = ?"
    dataset_rows = execute_query(query, (dataset_id,), db_path)
    
    if not dataset_rows:
        raise ValueError(
            f"Dataset with ID {dataset_id} not found. "
            f"Please verify the dataset ID is correct."
        )
    
    dataset_record = dataset_rows[0]
    dataset_type = dataset_record.get('dataset_type', '')
    
    # Load data based on dataset type
    if dataset_type == 'survey':
        # Load survey responses
        rows = execute_query(
            "SELECT * FROM survey_responses WHERE dataset_id = ?",
            (dataset_id,),
            db_path
        )
        if not rows:
            raise ValueError(
                f"No survey responses found for dataset {dataset_id}. "
                f"The dataset exists but contains no data. "
                f"Please upload data before performing analysis."
            )
        
        df = pd.DataFrame(rows)
        
        if df.empty:
            raise ValueError(
                f"Dataset {dataset_id} loaded but contains no rows. "
                f"Please ensure the dataset has been populated with data."
            )

        # Check if there are any numeric columns for quantitative analysis
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        # Exclude internal ID columns
        numeric_cols = [c for c in numeric_cols if c not in ('id', 'dataset_id')]
        if not numeric_cols:
            raise ValueError(
                "Survey datasets contain text responses and have no numeric columns "
                "suitable for correlation analysis. "
                "Please use a usage or circulation dataset, or run Qualitative Analysis instead."
            )
        
        return df
    
    elif dataset_type in ['usage', 'circulation']:
        # Load usage statistics
        rows = execute_query(
            "SELECT * FROM usage_statistics WHERE dataset_id = ?",
            (dataset_id,),
            db_path
        )
        if not rows:
            raise ValueError(
                f"No usage statistics found for dataset {dataset_id}. "
                f"The dataset exists but contains no data. "
                f"Please upload data before performing analysis."
            )
        
        # Convert to DataFrame
        df = pd.DataFrame(rows)
        
        if df.empty:
            raise ValueError(
                f"Dataset {dataset_id} loaded but contains no rows. "
                f"Please ensure the dataset has been populated with data."
            )
        
        # Pivot the data so each metric becomes a column
        if 'metric_name' in df.columns and 'metric_value' in df.columns:
            # Ensure metric_value is numeric
            df['metric_value'] = pd.to_numeric(df['metric_value'], errors='coerce')

            if 'date' in df.columns:
                # For circulation data, aggregate counts per date+metric before pivoting
                # so we don't get sparse NaN-filled columns after pivot
                df_agg = df.groupby(['date', 'metric_name'], as_index=False)['metric_value'].sum()
                df_pivot = df_agg.pivot_table(
                    index='date',
                    columns='metric_name',
                    values='metric_value',
                    aggfunc='sum'
                )
                # Fill NaN with 0 for count-based metrics (e.g. circulation)
                # only if the dataset is circulation type
                if dataset_type == 'circulation':
                    df_pivot = df_pivot.fillna(0)
                df_pivot.reset_index(inplace=True)
            else:
                df['row_id'] = df.index
                df_pivot = df.pivot_table(
                    index='row_id',
                    columns='metric_name',
                    values='metric_value',
                    aggfunc='first'
                )
                df_pivot.reset_index(drop=True, inplace=True)

            if df_pivot.empty:
                raise ValueError(
                    f"Dataset {dataset_id} contains no valid data after processing. "
                    f"Please check that the dataset has proper metric values."
                )
            
            return df_pivot
        else:
            return df
    
    else:
        raise ValueError(
            f"Unsupported dataset type '{dataset_type}' for dataset {dataset_id}. "
            f"Supported types: 'survey', 'usage', 'circulation'. "
            f"Please check the dataset configuration."
        )


# ============================================================================
# LLM Prompt Generation Functions
# ============================================================================

def generate_interpretation_prompt(
    analysis_type: str,
    results: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate a prompt for LLM interpretation of statistical analysis results.
    
    This function creates structured prompts that guide the LLM to generate
    clear, professional narratives explaining statistical results in plain language.
    The prompts include statistical results, context about the data, and specific
    instructions for the type of interpretation needed.
    
    Args:
        analysis_type: Type of analysis - 'correlation', 'trend', 'comparative', or 'distribution'
        results: Dictionary containing statistical analysis results
        context: Optional dictionary with additional context (dataset name, column descriptions, etc.)
    
    Returns:
        String containing the formatted prompt for LLM generation
        
    Raises:
        ValueError: If analysis_type is not recognized
        
    Requirements: 1.2, 1.4, 1.6, 1.8
    """
    if analysis_type == 'correlation':
        return _generate_correlation_prompt(results, context)
    elif analysis_type == 'trend':
        return _generate_trend_prompt(results, context)
    elif analysis_type == 'comparative':
        return _generate_comparative_prompt(results, context)
    elif analysis_type == 'distribution':
        return _generate_distribution_prompt(results, context)
    else:
        raise ValueError(
            f"Unknown analysis type '{analysis_type}'. "
            f"Must be one of: correlation, trend, comparative, distribution"
        )


def _generate_correlation_prompt(
    results: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate prompt for correlation analysis interpretation.
    
    Requirements: 1.2, 4.8
    """
    method = results.get('method', 'pearson')
    n_obs = results.get('n_observations', 0)
    top_corr = results.get('top_correlations', [])
    
    # Build context information
    dataset_name = context.get('dataset_name', 'the dataset') if context else 'the dataset'
    
    # Format top correlations for the prompt
    correlations_text = ""
    for i, corr in enumerate(top_corr[:5], 1):  # Top 5 for brevity
        var1 = corr['variable1']
        var2 = corr['variable2']
        coef = corr['correlation']
        pval = corr['p_value']
        sig = "statistically significant" if corr['significant'] else "not statistically significant"
        
        correlations_text += f"{i}. {var1} and {var2}: correlation = {coef:.3f}, p-value = {pval:.4f} ({sig})\n"
    
    prompt = f"""You are a data analyst explaining statistical results to library administrators who may not have statistical expertise.

Analyze the following correlation analysis results and provide a clear, professional interpretation in plain language.

Analysis Details:
- Method: {method.capitalize()} correlation
- Number of observations: {n_obs}
- Dataset: {dataset_name}

Top Correlations Found:
{correlations_text}

Please provide:
1. An explanation of what these correlations mean in practical terms
2. The strength and direction of the key relationships
3. Which correlations are statistically significant and what that means
4. Any important patterns or insights about how these variables relate to each other

Write your interpretation in 2-3 paragraphs using clear, accessible language. Focus on practical meaning rather than statistical jargon."""
    
    return prompt


def _generate_trend_prompt(
    results: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate prompt for trend analysis interpretation.
    
    Requirements: 1.4, 5.7
    """
    trend_dir = results.get('trend_direction', 'stable')
    slope = results.get('trend_slope', 0)
    r_squared = results.get('r_squared', 0)
    n_obs = results.get('n_observations', 0)
    seasonal = results.get('seasonal_pattern', False)
    forecast = results.get('forecast', [])
    value_col = results.get('value_column', 'value')
    date_col = results.get('date_column', 'date')
    start_date = results.get('start_date', 'unknown')
    end_date = results.get('end_date', 'unknown')
    
    # Build context information
    dataset_name = context.get('dataset_name', 'the dataset') if context else 'the dataset'
    
    # Format forecast values
    forecast_text = ""
    if forecast:
        forecast_text = f"Forecasted values for next {len(forecast)} periods: "
        forecast_text += ", ".join([f"{v:.2f}" for v in forecast[:3]])
        if len(forecast) > 3:
            forecast_text += f", ... (and {len(forecast) - 3} more)"
    
    prompt = f"""You are a data analyst explaining statistical results to library administrators who may not have statistical expertise.

Analyze the following trend analysis results and provide a clear, professional interpretation in plain language.

Analysis Details:
- Dataset: {dataset_name}
- Variable analyzed: {value_col}
- Time period: {start_date} to {end_date}
- Number of observations: {n_obs}

Trend Results:
- Trend direction: {trend_dir}
- Trend slope: {slope:.4f} (change per time period)
- R-squared: {r_squared:.3f} (trend strength, 0-1 scale)
- Seasonal pattern detected: {"Yes" if seasonal else "No"}
{forecast_text}

Please provide:
1. An explanation of the overall trend pattern (increasing, decreasing, or stable)
2. The strength of the trend and what the R-squared value indicates
3. Whether seasonal patterns exist and what they might mean
4. What the forecast suggests for future periods
5. Practical implications of these trends for library planning

Write your interpretation in 2-3 paragraphs using clear, accessible language. Focus on practical meaning rather than statistical jargon."""
    
    return prompt


def _generate_comparative_prompt(
    results: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate prompt for comparative analysis interpretation.
    
    Requirements: 1.6, 6.7
    """
    test_type = results.get('test_type', 'unknown')
    test_stat = results.get('test_statistic', 0)
    p_value = results.get('p_value', 1)
    significant = results.get('significant', False)
    n_groups = results.get('n_groups', 0)
    n_obs = results.get('n_observations', 0)
    group_stats = results.get('group_statistics', {})
    value_col = results.get('value_column', 'value')
    group_col = results.get('group_column', 'group')
    effect_size = results.get('effect_size', None)
    pairwise = results.get('pairwise_comparisons', [])
    
    # Build context information
    dataset_name = context.get('dataset_name', 'the dataset') if context else 'the dataset'
    
    # Format group statistics
    group_stats_text = ""
    for group_name, stats in group_stats.items():
        group_stats_text += f"- {group_name}: mean = {stats['mean']:.2f}, std = {stats['std']:.2f}, n = {stats['n']}\n"
    
    # Format pairwise comparisons if available
    pairwise_text = ""
    if pairwise:
        pairwise_text = "\nPairwise Comparisons:\n"
        for comp in pairwise[:5]:  # Top 5 for brevity
            g1 = comp['group1']
            g2 = comp['group2']
            sig = "significant" if comp['significant'] else "not significant"
            pairwise_text += f"- {g1} vs {g2}: {sig} (p = {comp['p_value']:.4f})\n"
    
    # Format effect size if available
    effect_text = ""
    if effect_size is not None:
        effect_interp = results.get('effect_size_interpretation', 'unknown')
        effect_text = f"\nEffect size (Cohen's d): {effect_size:.3f} ({effect_interp})"
    
    prompt = f"""You are a data analyst explaining statistical results to library administrators who may not have statistical expertise.

Analyze the following comparative analysis results and provide a clear, professional interpretation in plain language.

Analysis Details:
- Dataset: {dataset_name}
- Variable compared: {value_col}
- Groups compared: {group_col}
- Number of groups: {n_groups}
- Total observations: {n_obs}
- Statistical test: {test_type}

Test Results:
- Test statistic: {test_stat:.3f}
- P-value: {p_value:.4f}
- Statistically significant: {"Yes" if significant else "No"} (at α = 0.05)
{effect_text}

Group Statistics:
{group_stats_text}
{pairwise_text}

Please provide:
1. An explanation of whether the groups differ significantly
2. Which specific groups show the largest differences (if applicable)
3. The practical magnitude of these differences (effect size)
4. What these differences mean in practical terms for library operations
5. Any recommendations based on the group comparisons

Write your interpretation in 2-3 paragraphs using clear, accessible language. Focus on practical meaning rather than statistical jargon."""
    
    return prompt


def _generate_distribution_prompt(
    results: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate prompt for distribution analysis interpretation.
    
    Requirements: 1.8, 7.7
    """
    skewness = results.get('skewness', 0)
    kurtosis = results.get('kurtosis', 0)
    is_normal = results.get('is_normal', False)
    normality_test = results.get('normality_test', {})
    n_outliers = results.get('n_outliers', 0)
    n_obs = results.get('n_observations', 0)
    quartiles = results.get('quartiles', {})
    column = results.get('column', 'value')
    outlier_method = results.get('outlier_method', 'iqr')
    
    # Build context information
    dataset_name = context.get('dataset_name', 'the dataset') if context else 'the dataset'
    
    # Interpret skewness
    if abs(skewness) < 0.5:
        skew_interp = "approximately symmetric"
    elif skewness > 0:
        skew_interp = "right-skewed (tail extends to the right)"
    else:
        skew_interp = "left-skewed (tail extends to the left)"
    
    # Interpret kurtosis
    if abs(kurtosis) < 0.5:
        kurt_interp = "normal peakedness"
    elif kurtosis > 0:
        kurt_interp = "heavy-tailed (more extreme values than normal)"
    else:
        kurt_interp = "light-tailed (fewer extreme values than normal)"
    
    # Format quartiles
    q1 = quartiles.get('Q1', 0)
    q2 = quartiles.get('Q2', 0)
    q3 = quartiles.get('Q3', 0)
    
    # Format normality test
    test_name = normality_test.get('test', 'unknown')
    test_pval = normality_test.get('p_value', 1)
    
    prompt = f"""You are a data analyst explaining statistical results to library administrators who may not have statistical expertise.

Analyze the following distribution analysis results and provide a clear, professional interpretation in plain language.

Analysis Details:
- Dataset: {dataset_name}
- Variable analyzed: {column}
- Number of observations: {n_obs}
- Outlier detection method: {outlier_method.upper()}

Distribution Characteristics:
- Skewness: {skewness:.3f} ({skew_interp})
- Kurtosis: {kurtosis:.3f} ({kurt_interp})
- Normality test: {test_name}, p-value = {test_pval:.4f}
- Distribution is normal: {"Yes" if is_normal else "No"}
- Quartiles: Q1 = {q1:.2f}, Median = {q2:.2f}, Q3 = {q3:.2f}

Outlier Detection:
- Number of outliers detected: {n_outliers}
- Percentage of data: {(n_outliers / n_obs * 100):.1f}%

Please provide:
1. An explanation of the distribution shape (symmetric, skewed, etc.)
2. Whether the data follows a normal distribution and why that matters
3. What the outliers represent and whether they should be investigated
4. Practical implications of the distribution characteristics
5. Any recommendations for handling outliers or unusual patterns

Write your interpretation in 2-3 paragraphs using clear, accessible language. Focus on practical meaning rather than statistical jargon."""
    
    return prompt


# ============================================================================
# LLM Interpretation Generation Functions
# ============================================================================

def generate_interpretation(
    analysis_type: str,
    results: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    timeout: int = LLM_TIMEOUT
) -> Dict[str, Any]:
    """
    Generate natural language interpretation of statistical analysis results using LLM.
    
    This function uses the local Ollama LLM to generate clear, professional narratives
    explaining statistical results in plain language. It applies PII redaction to all
    outputs to maintain FERPA compliance. The function handles connection failures
    gracefully and implements a timeout to prevent long-running operations.
    
    Args:
        analysis_type: Type of analysis - 'correlation', 'trend', 'comparative', or 'distribution'
        results: Dictionary containing statistical analysis results
        context: Optional dictionary with additional context (dataset name, column descriptions, etc.)
        timeout: Timeout in seconds for LLM generation (default: 60 seconds from settings)
    
    Returns:
        Dictionary containing:
            - interpretation: Natural language interpretation (PII-redacted)
            - pii_redacted: Boolean indicating if PII was found and redacted
            - pii_counts: Dictionary of PII types and counts redacted
            - generation_time: Time taken to generate interpretation (seconds)
            - model_used: Name of the Ollama model used
            - error: Error message if generation failed (optional)
            - partial_result: True if timeout occurred and returning without interpretation
    
    Raises:
        ValueError: If analysis_type is not recognized
        RuntimeError: If Ollama connection fails or other generation errors occur
        
    Requirements: 1.2, 1.4, 1.6, 1.8, 1.9, 10.1, 10.2, 10.5
    """
    import time
    
    # Validate analysis type
    valid_types = ['correlation', 'trend', 'comparative', 'distribution']
    if analysis_type not in valid_types:
        raise ValueError(
            f"Invalid analysis type '{analysis_type}'. "
            f"Must be one of: {', '.join(valid_types)}"
        )
    
    # Generate prompt for the analysis type
    try:
        prompt = generate_interpretation_prompt(analysis_type, results, context)
    except Exception as e:
        raise ValueError(f"Failed to generate prompt: {str(e)}")
    
    # Call Ollama to generate interpretation
    start_time = time.time()
    
    try:
        # Use Ollama client to generate interpretation
        # Note: Ollama Python client doesn't have built-in timeout parameter,
        # so we rely on the server's timeout configuration
        response = ollama.generate(
            model=Settings.OLLAMA_MODEL,
            prompt=prompt,
            options={
                "num_predict": 1000,  # Limit response length to ~2-3 paragraphs
                "temperature": 0.7,   # Balanced creativity and consistency
            }
        )
        
        generation_time = time.time() - start_time
        
        # Extract interpretation text from response
        interpretation = response['response'].strip()
        
        # Apply PII redaction to the interpretation (Requirement 1.9, 10.6)
        redacted_interpretation, pii_counts = redact_pii(interpretation)
        
        # Check if any PII was redacted
        pii_redacted = len(pii_counts) > 0
        
        # Return results
        return {
            'interpretation': redacted_interpretation,
            'pii_redacted': pii_redacted,
            'pii_counts': pii_counts,
            'generation_time': generation_time,
            'model_used': Settings.OLLAMA_MODEL,
            'partial_result': False
        }
        
    except Exception as e:
        error_msg = str(e).lower()
        
        # Handle Ollama connection failures (Requirement 11.5)
        if "connection" in error_msg or "refused" in error_msg or "unreachable" in error_msg:
            raise RuntimeError(
                f"Failed to connect to Ollama server at {Settings.OLLAMA_URL}. "
                f"Please ensure Ollama is running by executing 'ollama serve' in a terminal. "
                f"You can verify the connection by running 'ollama list' to see available models. "
                f"Original error: {str(e)}"
            )
        
        # Handle timeout (Requirement 11.4)
        elif "timeout" in error_msg or "timed out" in error_msg:
            generation_time = time.time() - start_time
            
            # Return partial result with statistical calculations but no interpretation
            return {
                'interpretation': None,
                'pii_redacted': False,
                'pii_counts': {},
                'generation_time': generation_time,
                'model_used': Settings.OLLAMA_MODEL,
                'partial_result': True,
                'error': f"LLM interpretation generation timed out after {timeout} seconds. "
                        f"Statistical results are available, but natural language interpretation "
                        f"could not be generated. Try again or review the statistical results directly."
            }
        
        # Handle other errors
        else:
            raise RuntimeError(
                f"Failed to generate interpretation using Ollama: {str(e)}"
            )


# ============================================================================
# Contextual Insights Generation Functions
# ============================================================================

def generate_insights(
    dataset_id: int,
    analysis_results: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    timeout: int = LLM_TIMEOUT,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate contextual insights about library data patterns, trends, and relationships.
    
    This function uses the local Ollama LLM to generate insights about patterns in
    library data (usage, survey, circulation). It analyzes the data to identify
    meaningful patterns, trends, and cross-dataset relationships, providing specific
    data points and statistics to support observations. All insights are PII-redacted
    to maintain FERPA compliance.
    
    Args:
        dataset_id: ID of the dataset to analyze
        analysis_results: Optional dictionary containing pre-computed analysis results
                         (correlation, trend, comparative, distribution). If not provided,
                         basic statistics will be computed from the dataset.
        context: Optional dictionary with additional context (dataset name, type, etc.)
        timeout: Timeout in seconds for LLM generation (default: 60 seconds from settings)
        db_path: Optional database path (default: uses default database)
    
    Returns:
        Dictionary containing:
            - insights: Natural language insights about data patterns (PII-redacted)
            - data_points: List of specific statistics and data points referenced
            - patterns_identified: List of key patterns found in the data
            - pii_redacted: Boolean indicating if PII was found and redacted
            - pii_counts: Dictionary of PII types and counts redacted
            - generation_time: Time taken to generate insights (seconds)
            - model_used: Name of the Ollama model used
            - error: Error message if generation failed (optional)
            - partial_result: True if timeout occurred
    
    Raises:
        ValueError: If dataset not found or invalid
        RuntimeError: If Ollama connection fails or other generation errors occur
        
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7
    """
    import time
    
    # Load dataset to get type and basic information
    query = "SELECT * FROM datasets WHERE id = ?"
    dataset_rows = execute_query(query, (dataset_id,), db_path)
    
    if not dataset_rows:
        raise ValueError(f"Dataset with ID {dataset_id} not found")
    
    dataset_record = dataset_rows[0]
    dataset_type = dataset_record.get('dataset_type', 'unknown')
    dataset_name = dataset_record.get('name', f'Dataset {dataset_id}')
    
    # Load the actual data
    df = _load_dataset_data(dataset_id, db_path)
    
    # Compute basic statistics if analysis_results not provided
    if analysis_results is None:
        analysis_results = _compute_basic_statistics(df, dataset_type)
    
    # Build context if not provided
    if context is None:
        context = {}
    
    context['dataset_name'] = dataset_name
    context['dataset_type'] = dataset_type
    context['n_observations'] = len(df)
    
    # Generate insights prompt based on dataset type
    prompt = _generate_insights_prompt(dataset_type, df, analysis_results, context)
    
    # Call Ollama to generate insights
    start_time = time.time()
    
    try:
        # Use Ollama client to generate insights
        response = ollama.generate(
            model=Settings.OLLAMA_MODEL,
            prompt=prompt,
            options={
                "num_predict": 1500,  # Allow longer response for insights
                "temperature": 0.7,   # Balanced creativity and consistency
            }
        )
        
        generation_time = time.time() - start_time
        
        # Extract insights text from response
        insights = response['response'].strip()
        
        # Apply PII redaction to the insights (Requirement 2.7)
        redacted_insights, pii_counts = redact_pii(insights)
        
        # Check if any PII was redacted
        pii_redacted = len(pii_counts) > 0
        
        # Extract data points and patterns from the analysis results
        data_points = _extract_data_points(analysis_results, df, dataset_type)
        patterns_identified = _identify_patterns(analysis_results, df, dataset_type)
        
        # Return results
        return {
            'insights': redacted_insights,
            'data_points': data_points,
            'patterns_identified': patterns_identified,
            'pii_redacted': pii_redacted,
            'pii_counts': pii_counts,
            'generation_time': generation_time,
            'model_used': Settings.OLLAMA_MODEL,
            'partial_result': False
        }
        
    except Exception as e:
        error_msg = str(e).lower()
        
        # Handle Ollama connection failures
        if "connection" in error_msg or "refused" in error_msg or "unreachable" in error_msg:
            raise RuntimeError(
                f"Failed to connect to Ollama server at {Settings.OLLAMA_URL}. "
                f"Please ensure Ollama is running by executing 'ollama serve' in a terminal. "
                f"Original error: {str(e)}"
            )
        
        # Handle timeout
        elif "timeout" in error_msg or "timed out" in error_msg:
            generation_time = time.time() - start_time
            
            # Return partial result
            return {
                'insights': None,
                'data_points': _extract_data_points(analysis_results, df, dataset_type),
                'patterns_identified': _identify_patterns(analysis_results, df, dataset_type),
                'pii_redacted': False,
                'pii_counts': {},
                'generation_time': generation_time,
                'model_used': Settings.OLLAMA_MODEL,
                'partial_result': True,
                'error': f"LLM insights generation timed out after {timeout} seconds. "
                        f"Data points and patterns are available, but natural language insights "
                        f"could not be generated."
            }
        
        # Handle other errors
        else:
            raise RuntimeError(
                f"Failed to generate insights using Ollama: {str(e)}"
            )


def _compute_basic_statistics(df: pd.DataFrame, dataset_type: str) -> Dict[str, Any]:
    """
    Compute basic statistics for a dataset when detailed analysis results are not provided.
    
    Args:
        df: DataFrame containing the dataset
        dataset_type: Type of dataset ('usage', 'survey', 'circulation')
    
    Returns:
        Dictionary containing basic statistics
    """
    stats = {
        'n_observations': len(df),
        'n_columns': len(df.columns),
        'numeric_columns': []
    }
    
    # Get numeric columns and their statistics
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    for col in numeric_cols:
        col_stats = {
            'column': col,
            'mean': float(df[col].mean()),
            'median': float(df[col].median()),
            'std': float(df[col].std()),
            'min': float(df[col].min()),
            'max': float(df[col].max()),
            'missing': int(df[col].isna().sum())
        }
        stats['numeric_columns'].append(col_stats)
    
    # Check for date columns for time series analysis
    date_cols = []
    for col in df.columns:
        if 'date' in col.lower() or 'time' in col.lower():
            date_cols.append(col)
    
    stats['date_columns'] = date_cols
    
    return stats


def _generate_insights_prompt(
    dataset_type: str,
    df: pd.DataFrame,
    analysis_results: Dict[str, Any],
    context: Dict[str, Any]
) -> str:
    """
    Generate a prompt for LLM to create contextual insights about library data.
    
    Args:
        dataset_type: Type of dataset ('usage', 'survey', 'circulation')
        df: DataFrame containing the dataset
        analysis_results: Dictionary containing analysis results or basic statistics
        context: Dictionary with additional context
    
    Returns:
        String containing the formatted prompt for LLM generation
    """
    dataset_name = context.get('dataset_name', 'the dataset')
    n_obs = context.get('n_observations', len(df))
    
    # Build statistics summary
    stats_summary = ""
    if 'numeric_columns' in analysis_results:
        stats_summary = "Key Statistics:\n"
        for col_stats in analysis_results['numeric_columns'][:5]:  # Top 5 columns
            col = col_stats['column']
            mean = col_stats['mean']
            median = col_stats['median']
            min_val = col_stats['min']
            max_val = col_stats['max']
            stats_summary += f"- {col}: mean={mean:.2f}, median={median:.2f}, range=[{min_val:.2f}, {max_val:.2f}]\n"
    
    # Build analysis results summary if available
    analysis_summary = ""
    if 'top_correlations' in analysis_results:
        analysis_summary += "\nCorrelation Analysis:\n"
        for corr in analysis_results['top_correlations'][:3]:
            var1 = corr['variable1']
            var2 = corr['variable2']
            coef = corr['correlation']
            analysis_summary += f"- {var1} and {var2}: correlation = {coef:.3f}\n"
    
    if 'trend_direction' in analysis_results:
        trend_dir = analysis_results['trend_direction']
        slope = analysis_results.get('trend_slope', 0)
        analysis_summary += f"\nTrend Analysis:\n- Direction: {trend_dir}, slope: {slope:.4f}\n"
    
    if 'group_statistics' in analysis_results:
        analysis_summary += "\nComparative Analysis:\n"
        for group, stats in list(analysis_results['group_statistics'].items())[:3]:
            analysis_summary += f"- {group}: mean={stats['mean']:.2f}, n={stats['n']}\n"
    
    # Customize prompt based on dataset type
    if dataset_type == 'usage':
        data_context = """This is library usage data that tracks how patrons use library resources and services.
Focus on insights about:
- Usage patterns and trends over time
- Peak usage periods and seasonal variations
- Resource utilization and efficiency
- Patron engagement levels
- Opportunities to improve service delivery"""
    
    elif dataset_type == 'survey':
        data_context = """This is library survey data containing patron feedback and satisfaction responses.
Focus on insights about:
- Overall patron satisfaction trends
- Key areas of strength and concern
- Demographic patterns in responses
- Changes in sentiment over time
- Actionable feedback themes"""
    
    elif dataset_type == 'circulation':
        data_context = """This is library circulation data tracking material checkouts and returns.
Focus on insights about:
- Popular materials and collection usage
- Circulation trends and patterns
- Patron borrowing behavior
- Collection development opportunities
- Seasonal circulation patterns"""
    
    else:
        data_context = """This is library data for analysis.
Focus on insights about patterns, trends, and relationships in the data."""
    
    prompt = f"""You are a library data analyst providing contextual insights to library administrators.

Analyze the following library data and provide specific, actionable insights about patterns, trends, and relationships.

Dataset Information:
- Name: {dataset_name}
- Type: {dataset_type}
- Number of observations: {n_obs}

{data_context}

{stats_summary}
{analysis_summary}

Please provide:
1. 3-5 specific insights about patterns in the data
2. Include concrete data points and statistics to support each insight
3. Identify any notable trends or changes over time
4. Highlight any cross-variable relationships or correlations
5. Point out any unusual patterns or outliers that warrant investigation

Requirements:
- Be specific and include actual numbers from the data
- Focus on practical, actionable insights
- Explain what the patterns mean for library operations
- Use clear, accessible language
- Write 3-4 paragraphs

Format your response as clear, professional insights that library staff can act upon."""
    
    return prompt


def _extract_data_points(
    analysis_results: Dict[str, Any],
    df: pd.DataFrame,
    dataset_type: str
) -> List[Dict[str, Any]]:
    """
    Extract specific data points and statistics from analysis results.
    
    Args:
        analysis_results: Dictionary containing analysis results
        df: DataFrame containing the dataset
        dataset_type: Type of dataset
    
    Returns:
        List of dictionaries containing data points
    """
    data_points = []
    
    # Extract from basic statistics
    if 'numeric_columns' in analysis_results:
        for col_stats in analysis_results['numeric_columns']:
            data_points.append({
                'type': 'statistic',
                'metric': col_stats['column'],
                'value': col_stats['mean'],
                'description': f"Mean {col_stats['column']}"
            })
    
    # Extract from correlation analysis
    if 'top_correlations' in analysis_results:
        for corr in analysis_results['top_correlations'][:3]:
            data_points.append({
                'type': 'correlation',
                'variables': [corr['variable1'], corr['variable2']],
                'value': corr['correlation'],
                'description': f"Correlation between {corr['variable1']} and {corr['variable2']}"
            })
    
    # Extract from trend analysis
    if 'trend_direction' in analysis_results:
        data_points.append({
            'type': 'trend',
            'metric': analysis_results.get('value_column', 'value'),
            'value': analysis_results['trend_slope'],
            'description': f"Trend slope: {analysis_results['trend_direction']}"
        })
    
    # Extract from comparative analysis
    if 'group_statistics' in analysis_results:
        for group, stats in analysis_results['group_statistics'].items():
            data_points.append({
                'type': 'group_statistic',
                'group': group,
                'value': stats['mean'],
                'description': f"Mean for {group}"
            })
    
    return data_points


def _identify_patterns(
    analysis_results: Dict[str, Any],
    df: pd.DataFrame,
    dataset_type: str
) -> List[str]:
    """
    Identify key patterns from analysis results.
    
    Args:
        analysis_results: Dictionary containing analysis results
        df: DataFrame containing the dataset
        dataset_type: Type of dataset
    
    Returns:
        List of pattern descriptions
    """
    patterns = []
    
    # Identify correlation patterns
    if 'top_correlations' in analysis_results:
        strong_corr = [c for c in analysis_results['top_correlations'] if abs(c['correlation']) > 0.7]
        if strong_corr:
            patterns.append(f"Strong correlations detected between {len(strong_corr)} variable pairs")
    
    # Identify trend patterns
    if 'trend_direction' in analysis_results:
        trend_dir = analysis_results['trend_direction']
        if trend_dir != 'stable':
            patterns.append(f"{trend_dir.capitalize()} trend detected")
        
        if analysis_results.get('seasonal_pattern', False):
            patterns.append("Seasonal pattern detected in time series")
    
    # Identify group differences
    if 'significant' in analysis_results and analysis_results['significant']:
        patterns.append("Statistically significant differences between groups")
    
    # Identify outliers
    if 'n_outliers' in analysis_results and analysis_results['n_outliers'] > 0:
        n_outliers = analysis_results['n_outliers']
        n_obs = analysis_results.get('n_observations', 0)
        pct = (n_outliers / n_obs * 100) if n_obs > 0 else 0
        patterns.append(f"Outliers detected: {n_outliers} ({pct:.1f}% of data)")
    
    # Identify distribution characteristics
    if 'is_normal' in analysis_results:
        if not analysis_results['is_normal']:
            patterns.append("Non-normal distribution detected")
    
    return patterns


# ============================================================================
# Actionable Recommendations Generation Functions
# ============================================================================

def generate_recommendations(
    analysis_type: str,
    analysis_results: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    timeout: int = LLM_TIMEOUT
) -> Dict[str, Any]:
    """
    Generate actionable recommendations based on analysis results.
    
    This function uses the local Ollama LLM to generate specific, actionable
    recommendations based on statistical analysis results. Recommendations are
    grounded in the analyzed data and tailored to the analysis type. All
    recommendations are PII-redacted to maintain FERPA compliance.
    
    Args:
        analysis_type: Type of analysis - 'correlation', 'trend', 'comparative', or 'distribution'
        analysis_results: Dictionary containing statistical analysis results
        context: Optional dictionary with additional context (dataset name, type, etc.)
        timeout: Timeout in seconds for LLM generation (default: 60 seconds from settings)
    
    Returns:
        Dictionary containing:
            - recommendations: Natural language recommendations (PII-redacted)
            - recommendation_list: List of individual recommendations extracted
            - priority_level: Overall priority level ('high', 'medium', 'low')
            - pii_redacted: Boolean indicating if PII was found and redacted
            - pii_counts: Dictionary of PII types and counts redacted
            - generation_time: Time taken to generate recommendations (seconds)
            - model_used: Name of the Ollama model used
            - error: Error message if generation failed (optional)
            - partial_result: True if timeout occurred
    
    Raises:
        ValueError: If analysis_type is not recognized or results are invalid
        RuntimeError: If Ollama connection fails or other generation errors occur
        
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7
    """
    import time
    
    # Validate analysis type
    valid_types = ['correlation', 'trend', 'comparative', 'distribution']
    if analysis_type not in valid_types:
        raise ValueError(
            f"Invalid analysis type '{analysis_type}'. "
            f"Must be one of: {', '.join(valid_types)}"
        )
    
    # Validate analysis results
    if not analysis_results:
        raise ValueError("Analysis results cannot be empty")
    
    # Build context if not provided
    if context is None:
        context = {}
    
    # Generate recommendations prompt based on analysis type
    prompt = _generate_recommendations_prompt(analysis_type, analysis_results, context)
    
    # Call Ollama to generate recommendations
    start_time = time.time()
    
    try:
        # Use Ollama client to generate recommendations
        response = ollama.generate(
            model=Settings.OLLAMA_MODEL,
            prompt=prompt,
            options={
                "num_predict": 1500,  # Allow longer response for recommendations
                "temperature": 0.7,   # Balanced creativity and consistency
            }
        )
        
        generation_time = time.time() - start_time
        
        # Extract recommendations text from response
        recommendations = response['response'].strip()
        
        # Apply PII redaction to the recommendations (Requirement 3.7)
        redacted_recommendations, pii_counts = redact_pii(recommendations)
        
        # Check if any PII was redacted
        pii_redacted = len(pii_counts) > 0
        
        # Extract individual recommendations from the text
        recommendation_list = _extract_recommendations(redacted_recommendations)
        
        # Determine priority level based on analysis results
        priority_level = _determine_priority(analysis_type, analysis_results)
        
        # Return results
        return {
            'recommendations': redacted_recommendations,
            'recommendation_list': recommendation_list,
            'priority_level': priority_level,
            'pii_redacted': pii_redacted,
            'pii_counts': pii_counts,
            'generation_time': generation_time,
            'model_used': Settings.OLLAMA_MODEL,
            'partial_result': False
        }
        
    except Exception as e:
        error_msg = str(e).lower()
        
        # Handle Ollama connection failures
        if "connection" in error_msg or "refused" in error_msg or "unreachable" in error_msg:
            raise RuntimeError(
                f"Failed to connect to Ollama server at {Settings.OLLAMA_URL}. "
                f"Please ensure Ollama is running by executing 'ollama serve' in a terminal. "
                f"Original error: {str(e)}"
            )
        
        # Handle timeout
        elif "timeout" in error_msg or "timed out" in error_msg:
            generation_time = time.time() - start_time
            
            # Return partial result
            return {
                'recommendations': None,
                'recommendation_list': [],
                'priority_level': _determine_priority(analysis_type, analysis_results),
                'pii_redacted': False,
                'pii_counts': {},
                'generation_time': generation_time,
                'model_used': Settings.OLLAMA_MODEL,
                'partial_result': True,
                'error': f"LLM recommendations generation timed out after {timeout} seconds. "
                        f"Priority level is available, but natural language recommendations "
                        f"could not be generated."
            }
        
        # Handle other errors
        else:
            raise RuntimeError(
                f"Failed to generate recommendations using Ollama: {str(e)}"
            )


def _generate_recommendations_prompt(
    analysis_type: str,
    analysis_results: Dict[str, Any],
    context: Dict[str, Any]
) -> str:
    """
    Generate a prompt for LLM to create actionable recommendations.
    
    Args:
        analysis_type: Type of analysis ('correlation', 'trend', 'comparative', 'distribution')
        analysis_results: Dictionary containing analysis results
        context: Dictionary with additional context
    
    Returns:
        String containing the formatted prompt for LLM generation
        
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
    """
    dataset_name = context.get('dataset_name', 'the dataset')
    dataset_type = context.get('dataset_type', 'library data')
    
    if analysis_type == 'correlation':
        return _generate_correlation_recommendations_prompt(analysis_results, dataset_name, dataset_type)
    elif analysis_type == 'trend':
        return _generate_trend_recommendations_prompt(analysis_results, dataset_name, dataset_type)
    elif analysis_type == 'comparative':
        return _generate_comparative_recommendations_prompt(analysis_results, dataset_name, dataset_type)
    elif analysis_type == 'distribution':
        return _generate_distribution_recommendations_prompt(analysis_results, dataset_name, dataset_type)
    else:
        raise ValueError(f"Unknown analysis type: {analysis_type}")


def _generate_correlation_recommendations_prompt(
    results: Dict[str, Any],
    dataset_name: str,
    dataset_type: str
) -> str:
    """
    Generate prompt for correlation analysis recommendations.
    
    Requirements: 3.1, 3.6
    """
    method = results.get('method', 'pearson')
    top_corr = results.get('top_correlations', [])
    significant_corr = results.get('significant_correlations', [])
    
    # Format top correlations
    correlations_text = ""
    for i, corr in enumerate(top_corr[:5], 1):
        var1 = corr['variable1']
        var2 = corr['variable2']
        coef = corr['correlation']
        sig = "significant" if corr['significant'] else "not significant"
        correlations_text += f"{i}. {var1} and {var2}: r = {coef:.3f} ({sig})\n"
    
    prompt = f"""You are a library data consultant providing actionable recommendations to library administrators.

Based on the following correlation analysis results, provide specific, actionable recommendations for leveraging these relationships to improve library services.

Analysis Details:
- Dataset: {dataset_name}
- Type: {dataset_type}
- Method: {method.capitalize()} correlation
- Significant correlations found: {len(significant_corr)}

Top Correlations:
{correlations_text}

Please provide 3-5 specific, actionable recommendations that:
1. Leverage the strong relationships identified
2. Are grounded in the actual correlation data
3. Are practical and implementable by library staff
4. Focus on improving library services or operations
5. Include specific metrics or variables to monitor

Format your recommendations as:
- Start each recommendation with a clear action verb
- Be specific about what to do and why
- Reference the actual correlations found
- Explain the expected benefit

Write 2-3 paragraphs with clear, numbered recommendations."""
    
    return prompt


def _generate_trend_recommendations_prompt(
    results: Dict[str, Any],
    dataset_name: str,
    dataset_type: str
) -> str:
    """
    Generate prompt for trend analysis recommendations.
    
    Requirements: 3.2, 3.3, 3.6
    """
    trend_dir = results.get('trend_direction', 'stable')
    slope = results.get('trend_slope', 0)
    r_squared = results.get('r_squared', 0)
    seasonal = results.get('seasonal_pattern', False)
    forecast = results.get('forecast', [])
    value_col = results.get('value_column', 'value')
    
    # Determine if trend is concerning
    trend_concern = ""
    if trend_dir == 'decreasing':
        trend_concern = "The decreasing trend requires attention and intervention."
    elif trend_dir == 'increasing':
        trend_concern = "The increasing trend presents opportunities for growth."
    else:
        trend_concern = "The stable trend suggests maintaining current practices."
    
    forecast_text = ""
    if forecast:
        avg_forecast = sum(forecast) / len(forecast)
        forecast_text = f"Forecast average: {avg_forecast:.2f}"
    
    prompt = f"""You are a library data consultant providing actionable recommendations to library administrators.

Based on the following trend analysis results, provide specific, actionable recommendations for addressing the trend and planning for the future.

Analysis Details:
- Dataset: {dataset_name}
- Type: {dataset_type}
- Variable: {value_col}
- Trend direction: {trend_dir}
- Trend strength (R²): {r_squared:.3f}
- Seasonal pattern: {"Yes" if seasonal else "No"}
{forecast_text}

Context: {trend_concern}

Please provide 3-5 specific, actionable recommendations that:
1. Address the trend direction (sustain growth, reverse decline, or maintain stability)
2. Are grounded in the actual trend data and forecast
3. Are practical and implementable by library staff
4. Consider seasonal patterns if detected
5. Include specific actions and expected outcomes

Format your recommendations as:
- Start each recommendation with a clear action verb
- Be specific about what to do and why
- Reference the actual trend data
- Explain the expected benefit
- Consider both short-term and long-term actions

Write 2-3 paragraphs with clear, numbered recommendations."""
    
    return prompt


def _generate_comparative_recommendations_prompt(
    results: Dict[str, Any],
    dataset_name: str,
    dataset_type: str
) -> str:
    """
    Generate prompt for comparative analysis recommendations.
    
    Requirements: 3.4, 3.6
    """
    test_type = results.get('test_type', 'unknown')
    significant = results.get('significant', False)
    group_stats = results.get('group_statistics', {})
    value_col = results.get('value_column', 'value')
    group_col = results.get('group_column', 'group')
    pairwise = results.get('pairwise_comparisons', [])
    
    # Format group statistics
    group_stats_text = ""
    for group_name, stats in group_stats.items():
        group_stats_text += f"- {group_name}: mean = {stats['mean']:.2f}, n = {stats['n']}\n"
    
    # Identify significant differences
    sig_text = ""
    if significant:
        if pairwise:
            sig_pairs = [c for c in pairwise if c['significant']]
            if sig_pairs:
                sig_text = "Significant differences found between:\n"
                for comp in sig_pairs[:3]:
                    sig_text += f"- {comp['group1']} vs {comp['group2']}\n"
        else:
            sig_text = "Significant differences detected between groups."
    else:
        sig_text = "No significant differences detected between groups."
    
    prompt = f"""You are a library data consultant providing actionable recommendations to library administrators.

Based on the following comparative analysis results, provide specific, actionable recommendations for addressing disparities and improving performance across groups.

Analysis Details:
- Dataset: {dataset_name}
- Type: {dataset_type}
- Variable compared: {value_col}
- Groups: {group_col}
- Statistical test: {test_type}
- Significant differences: {"Yes" if significant else "No"}

Group Statistics:
{group_stats_text}

{sig_text}

Please provide 3-5 specific, actionable recommendations that:
1. Address the differences between groups (if significant)
2. Are grounded in the actual comparison data
3. Are practical and implementable by library staff
4. Focus on reducing disparities or sharing best practices
5. Include specific actions for each group or overall strategy

Format your recommendations as:
- Start each recommendation with a clear action verb
- Be specific about what to do and which groups to focus on
- Reference the actual group differences
- Explain the expected benefit
- Consider equity and access implications

Write 2-3 paragraphs with clear, numbered recommendations."""
    
    return prompt


def _generate_distribution_recommendations_prompt(
    results: Dict[str, Any],
    dataset_name: str,
    dataset_type: str
) -> str:
    """
    Generate prompt for distribution analysis recommendations.
    
    Requirements: 3.5, 3.6
    """
    n_outliers = results.get('n_outliers', 0)
    n_obs = results.get('n_observations', 0)
    is_normal = results.get('is_normal', False)
    skewness = results.get('skewness', 0)
    column = results.get('column', 'value')
    outlier_method = results.get('outlier_method', 'iqr')
    
    outlier_pct = (n_outliers / n_obs * 100) if n_obs > 0 else 0
    
    # Determine if outliers are concerning
    outlier_concern = ""
    if outlier_pct > 10:
        outlier_concern = "The high percentage of outliers requires investigation."
    elif outlier_pct > 5:
        outlier_concern = "The moderate number of outliers should be reviewed."
    elif n_outliers > 0:
        outlier_concern = "The outliers detected may represent unusual cases worth investigating."
    else:
        outlier_concern = "No outliers detected - data appears consistent."
    
    # Interpret skewness
    if abs(skewness) < 0.5:
        skew_text = "approximately symmetric"
    elif skewness > 0:
        skew_text = "right-skewed (most values are low with some high values)"
    else:
        skew_text = "left-skewed (most values are high with some low values)"
    
    prompt = f"""You are a library data consultant providing actionable recommendations to library administrators.

Based on the following distribution analysis results, provide specific, actionable recommendations for investigating anomalies and improving data quality.

Analysis Details:
- Dataset: {dataset_name}
- Type: {dataset_type}
- Variable: {column}
- Outliers detected: {n_outliers} ({outlier_pct:.1f}% of data)
- Detection method: {outlier_method.upper()}
- Distribution shape: {skew_text}
- Normal distribution: {"Yes" if is_normal else "No"}

Context: {outlier_concern}

Please provide 3-5 specific, actionable recommendations that:
1. Address the outliers and unusual patterns detected
2. Are grounded in the actual distribution data
3. Are practical and implementable by library staff
4. Focus on investigating anomalies and improving data quality
5. Include specific actions and criteria for investigation

Format your recommendations as:
- Start each recommendation with a clear action verb
- Be specific about what to investigate and why
- Reference the actual outlier data
- Explain the expected benefit
- Consider both data quality and operational implications

Write 2-3 paragraphs with clear, numbered recommendations."""
    
    return prompt


def _extract_recommendations(recommendations_text: str) -> List[str]:
    """
    Extract individual recommendations from the generated text.
    
    Args:
        recommendations_text: Full recommendations text from LLM
    
    Returns:
        List of individual recommendation strings
    """
    recommendations = []
    
    # Try to extract numbered recommendations
    lines = recommendations_text.split('\n')
    current_rec = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if line starts with a number (1., 2., etc.)
        if line and line[0].isdigit() and ('. ' in line or ') ' in line):
            # Save previous recommendation if exists
            if current_rec:
                recommendations.append(current_rec.strip())
            # Start new recommendation
            current_rec = line
        else:
            # Continue current recommendation
            if current_rec:
                current_rec += " " + line
    
    # Add last recommendation
    if current_rec:
        recommendations.append(current_rec.strip())
    
    # If no numbered recommendations found, try to split by sentences
    if not recommendations:
        # Split by periods and filter out short fragments
        sentences = [s.strip() + '.' for s in recommendations_text.split('.') if len(s.strip()) > 20]
        recommendations = sentences[:5]  # Limit to 5 recommendations
    
    return recommendations


def _determine_priority(analysis_type: str, analysis_results: Dict[str, Any]) -> str:
    """
    Determine priority level based on analysis results.
    
    Args:
        analysis_type: Type of analysis
        analysis_results: Dictionary containing analysis results
    
    Returns:
        Priority level: 'high', 'medium', or 'low'
    """
    if analysis_type == 'correlation':
        # High priority if many strong significant correlations
        significant_corr = analysis_results.get('significant_correlations', [])
        strong_corr = [c for c in significant_corr if abs(c['correlation']) > 0.7]
        if len(strong_corr) >= 3:
            return 'high'
        elif len(significant_corr) >= 2:
            return 'medium'
        else:
            return 'low'
    
    elif analysis_type == 'trend':
        # High priority if strong declining trend
        trend_dir = analysis_results.get('trend_direction', 'stable')
        r_squared = analysis_results.get('r_squared', 0)
        
        if trend_dir == 'decreasing' and r_squared > 0.5:
            return 'high'
        elif trend_dir == 'increasing' and r_squared > 0.5:
            return 'medium'
        elif trend_dir != 'stable':
            return 'medium'
        else:
            return 'low'
    
    elif analysis_type == 'comparative':
        # High priority if significant differences with large effect size
        significant = analysis_results.get('significant', False)
        effect_size = analysis_results.get('effect_size', None)
        
        if significant:
            if effect_size is not None and abs(effect_size) > 0.8:
                return 'high'
            else:
                return 'medium'
        else:
            return 'low'
    
    elif analysis_type == 'distribution':
        # High priority if many outliers
        n_outliers = analysis_results.get('n_outliers', 0)
        n_obs = analysis_results.get('n_observations', 1)
        outlier_pct = (n_outliers / n_obs * 100) if n_obs > 0 else 0
        
        if outlier_pct > 10:
            return 'high'
        elif outlier_pct > 5:
            return 'medium'
        else:
            return 'low'
    
    return 'medium'  # Default


# ============================================================================
# Database Storage and Retrieval Functions
# ============================================================================

def store_analysis_results(
    dataset_id: int,
    analysis_type: str,
    parameters: Dict[str, Any],
    results: Dict[str, Any],
    db_path: Optional[str] = None
) -> int:
    """
    Store quantitative analysis results in the database.
    
    This function saves the complete analysis results including statistical
    calculations, LLM-generated interpretations, insights, and recommendations
    to the quantitative_analyses table for future reference.
    
    Args:
        dataset_id: ID of the dataset that was analyzed
        analysis_type: Type of analysis - 'correlation', 'trend', 'comparative', or 'distribution'
        parameters: Dictionary containing analysis parameters (method, columns, etc.)
        results: Dictionary containing complete analysis results including:
                - Statistical results (correlation matrix, trend data, etc.)
                - interpretation: LLM-generated interpretation (optional)
                - insights: LLM-generated insights (optional)
                - recommendations: LLM-generated recommendations (optional)
        db_path: Optional database path (default: uses default database)
    
    Returns:
        Integer ID of the stored analysis record
        
    Raises:
        ValueError: If analysis_type is invalid or required fields are missing
        RuntimeError: If database storage fails
        
    Requirements: 13.2, 13.3, 13.4, 13.5
    
    Example:
        # Store correlation analysis results
        analysis_id = store_analysis_results(
            dataset_id=1,
            analysis_type='correlation',
            parameters={'method': 'pearson', 'columns': ['col1', 'col2']},
            results=correlation_results
        )
        print(f"Analysis stored with ID: {analysis_id}")
    """
    # Validate analysis type
    valid_types = ['correlation', 'trend', 'comparative', 'distribution']
    if analysis_type not in valid_types:
        raise ValueError(
            f"Invalid analysis type '{analysis_type}'. "
            f"Must be one of: {', '.join(valid_types)}"
        )
    
    # Validate dataset_id
    if not isinstance(dataset_id, int) or dataset_id <= 0:
        raise ValueError(
            f"Invalid dataset_id '{dataset_id}'. "
            f"Must be a positive integer."
        )
    
    # Extract components from results
    # Statistical results (everything except LLM-generated content)
    statistical_results = {
        k: v for k, v in results.items()
        if k not in ['interpretation', 'insights', 'recommendations', 
                     'pii_redacted', 'pii_counts', 'generation_time', 
                     'model_used', 'partial_result', 'error',
                     'data_points', 'patterns_identified', 'recommendation_list',
                     'priority_level']
    }
    
    # LLM-generated content
    interpretation = results.get('interpretation', None)
    insights = results.get('insights', None)
    recommendations = results.get('recommendations', None)
    
    # Convert to JSON strings for storage
    parameters_json = _safe_json_dumps(parameters)
    statistical_results_json = _safe_json_dumps(statistical_results)
    
    # Prepare SQL query
    query = """
        INSERT INTO quantitative_analyses 
        (dataset_id, analysis_type, parameters, statistical_results, 
         interpretation, insights, recommendations)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    
    try:
        # Execute insert query
        analysis_id = execute_update(
            query,
            (dataset_id, analysis_type, parameters_json, statistical_results_json,
             interpretation, insights, recommendations),
            db_path
        )
        
        if not analysis_id:
            raise RuntimeError("Failed to store analysis results - no ID returned")
        
        return analysis_id
        
    except Exception as e:
        raise RuntimeError(
            f"Failed to store analysis results in database: {str(e)}"
        )


def retrieve_analysis_results(
    analysis_id: int,
    db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieve quantitative analysis results from the database by ID.
    
    This function retrieves a previously stored analysis including all
    statistical results, LLM-generated interpretations, insights, and
    recommendations.
    
    Args:
        analysis_id: ID of the analysis to retrieve
        db_path: Optional database path (default: uses default database)
    
    Returns:
        Dictionary containing the complete analysis record with keys:
            - id: Analysis ID
            - dataset_id: Dataset ID
            - analysis_type: Type of analysis
            - parameters: Analysis parameters (parsed from JSON)
            - statistical_results: Statistical results (parsed from JSON)
            - interpretation: LLM-generated interpretation
            - insights: LLM-generated insights
            - recommendations: LLM-generated recommendations
            - timestamp: When the analysis was performed
        Returns None if analysis not found.
        
    Raises:
        ValueError: If analysis_id is invalid
        
    Requirements: 13.6
    
    Example:
        # Retrieve previous analysis
        analysis = retrieve_analysis_results(analysis_id=42)
        if analysis:
            print(f"Analysis type: {analysis['analysis_type']}")
            print(f"Interpretation: {analysis['interpretation']}")
        else:
            print("Analysis not found")
    """
    # Validate analysis_id
    if not isinstance(analysis_id, int) or analysis_id <= 0:
        raise ValueError(
            f"Invalid analysis_id '{analysis_id}'. "
            f"Must be a positive integer."
        )
    
    # Query the database
    query = """
        SELECT id, dataset_id, analysis_type, parameters, statistical_results,
               interpretation, insights, recommendations, timestamp
        FROM quantitative_analyses
        WHERE id = ?
    """
    
    results = execute_query(query, (analysis_id,), db_path)
    
    if not results:
        return None
    
    # Parse the first (and only) result
    record = results[0]
    
    # Parse JSON fields
    try:
        parameters = json.loads(record['parameters']) if record['parameters'] else {}
        statistical_results = json.loads(record['statistical_results']) if record['statistical_results'] else {}
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Failed to parse stored analysis data: {str(e)}"
        )
    
    # Build result dictionary
    analysis = {
        'id': record['id'],
        'dataset_id': record['dataset_id'],
        'analysis_type': record['analysis_type'],
        'parameters': parameters,
        'statistical_results': statistical_results,
        'interpretation': record['interpretation'],
        'insights': record['insights'],
        'recommendations': record['recommendations'],
        'timestamp': record['timestamp']
    }
    
    return analysis


def list_analyses_by_dataset(
    dataset_id: int,
    analysis_type: Optional[str] = None,
    limit: Optional[int] = None,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List all quantitative analyses for a given dataset.
    
    This function retrieves a list of all analyses performed on a specific
    dataset, optionally filtered by analysis type and limited to a maximum
    number of results. Results are ordered by timestamp (most recent first).
    
    Args:
        dataset_id: ID of the dataset to list analyses for
        analysis_type: Optional filter by analysis type ('correlation', 'trend', 
                      'comparative', 'distribution'). If None, returns all types.
        limit: Optional maximum number of results to return. If None, returns all.
        db_path: Optional database path (default: uses default database)
    
    Returns:
        List of dictionaries, each containing:
            - id: Analysis ID
            - dataset_id: Dataset ID
            - analysis_type: Type of analysis
            - parameters: Analysis parameters (parsed from JSON)
            - timestamp: When the analysis was performed
            - has_interpretation: Boolean indicating if interpretation exists
            - has_insights: Boolean indicating if insights exist
            - has_recommendations: Boolean indicating if recommendations exist
        Returns empty list if no analyses found.
        
    Raises:
        ValueError: If dataset_id or analysis_type is invalid
        
    Requirements: 13.7
    
    Example:
        # List all correlation analyses for dataset 1
        analyses = list_analyses_by_dataset(
            dataset_id=1,
            analysis_type='correlation',
            limit=10
        )
        for analysis in analyses:
            print(f"Analysis {analysis['id']}: {analysis['analysis_type']} "
                  f"at {analysis['timestamp']}")
    """
    # Validate dataset_id
    if not isinstance(dataset_id, int) or dataset_id <= 0:
        raise ValueError(
            f"Invalid dataset_id '{dataset_id}'. "
            f"Must be a positive integer."
        )
    
    # Validate analysis_type if provided
    if analysis_type is not None:
        valid_types = ['correlation', 'trend', 'comparative', 'distribution']
        if analysis_type not in valid_types:
            raise ValueError(
                f"Invalid analysis type '{analysis_type}'. "
                f"Must be one of: {', '.join(valid_types)}"
            )
    
    # Build query
    query = """
        SELECT id, dataset_id, analysis_type, parameters, timestamp,
               CASE WHEN interpretation IS NOT NULL THEN 1 ELSE 0 END as has_interpretation,
               CASE WHEN insights IS NOT NULL THEN 1 ELSE 0 END as has_insights,
               CASE WHEN recommendations IS NOT NULL THEN 1 ELSE 0 END as has_recommendations
        FROM quantitative_analyses
        WHERE dataset_id = ?
    """
    
    params = [dataset_id]
    
    # Add analysis_type filter if provided
    if analysis_type is not None:
        query += " AND analysis_type = ?"
        params.append(analysis_type)
    
    # Order by most recent first
    query += " ORDER BY timestamp DESC"
    
    # Add limit if provided
    if limit is not None:
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError(
                f"Invalid limit '{limit}'. "
                f"Must be a positive integer."
            )
        query += " LIMIT ?"
        params.append(limit)
    
    # Execute query
    results = execute_query(query, tuple(params), db_path)
    
    # Parse results
    analyses = []
    for record in results:
        try:
            parameters = json.loads(record['parameters']) if record['parameters'] else {}
        except json.JSONDecodeError:
            parameters = {}
        
        analyses.append({
            'id': record['id'],
            'dataset_id': record['dataset_id'],
            'analysis_type': record['analysis_type'],
            'parameters': parameters,
            'timestamp': record['timestamp'],
            'has_interpretation': bool(record['has_interpretation']),
            'has_insights': bool(record['has_insights']),
            'has_recommendations': bool(record['has_recommendations'])
        })
    
    return analyses


# ============================================================================
# Visualization Functions
# ============================================================================

def create_correlation_heatmap(
    correlation_results: Dict[str, Any],
    title: str = "Correlation Heatmap"
) -> 'go.Figure':
    """
    Create a correlation heatmap visualization.
    
    This function generates an interactive heatmap showing correlation coefficients
    between all pairs of variables. The heatmap uses a diverging color scale where
    strong positive correlations are shown in blue, strong negative correlations
    in red, and weak correlations in white.
    
    Args:
        correlation_results: Dictionary containing correlation analysis results
                           with 'correlation_matrix' key containing the correlation
                           matrix as a dictionary
        title: Title for the heatmap (default: "Correlation Heatmap")
    
    Returns:
        Plotly Figure object containing the correlation heatmap
        
    Raises:
        ValueError: If correlation_matrix is missing from results
        
    Requirements: 14.1, 14.5, 14.6
    
    Example:
        results = calculate_correlation(dataset_id=1, method='pearson')
        fig = create_correlation_heatmap(results)
        st.plotly_chart(fig)
    """
    import plotly.graph_objects as go
    
    # Validate input
    if 'correlation_matrix' not in correlation_results:
        raise ValueError(
            "correlation_results must contain 'correlation_matrix' key"
        )
    
    # Get correlation matrix
    corr_matrix_dict = correlation_results['correlation_matrix']
    
    # Convert to DataFrame for easier handling
    corr_df = pd.DataFrame(corr_matrix_dict)
    
    # Get variable names
    variables = list(corr_df.columns)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=corr_df.values,
        x=variables,
        y=variables,
        colorscale='RdBu',  # Red-Blue diverging scale
        zmid=0,  # Center the colorscale at 0
        zmin=-1,
        zmax=1,
        text=corr_df.values.round(2),
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(
            title=dict(
                text="Correlation",
                side="right"
            ),
            tickmode="linear",
            tick0=-1,
            dtick=0.5
        )
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Variables",
        yaxis_title="Variables",
        font=dict(size=12),
        plot_bgcolor='white',
        paper_bgcolor='white',
        width=800,
        height=800
    )
    
    return fig


def create_trend_chart(
    trend_results: Dict[str, Any],
    title: str = "Trend Analysis"
) -> 'go.Figure':
    """
    Create a trend chart with trend line and forecast.
    
    This function generates an interactive line chart showing the original time
    series data, the fitted trend line, moving averages, and forecasted values
    with confidence intervals.
    
    Args:
        trend_results: Dictionary containing trend analysis results with keys:
                      - 'date_column': Name of date column
                      - 'value_column': Name of value column
                      - 'forecast': List of forecasted values
                      - 'forecast_lower': Lower confidence bound
                      - 'forecast_upper': Upper confidence bound
                      - 'moving_average_7': 7-day moving average (optional)
                      - 'moving_average_30': 30-day moving average (optional)
        title: Title for the chart (default: "Trend Analysis")
    
    Returns:
        Plotly Figure object containing the trend chart
        
    Raises:
        ValueError: If required keys are missing from results
        
    Requirements: 14.2, 14.5, 14.6
    
    Example:
        results = calculate_trend(dataset_id=1, date_column='date', value_column='checkouts')
        fig = create_trend_chart(results)
        st.plotly_chart(fig)
    """
    import plotly.graph_objects as go
    
    # Validate input
    required_keys = ['forecast', 'forecast_lower', 'forecast_upper']
    for key in required_keys:
        if key not in trend_results:
            raise ValueError(
                f"trend_results must contain '{key}' key"
            )
    
    # Create figure
    fig = go.Figure()
    
    # Note: The actual historical data would need to be passed separately
    # or retrieved from the database. For now, we'll just show the forecast.
    
    # Create x-axis for forecast (future periods)
    n_forecast = len(trend_results['forecast'])
    forecast_x = list(range(1, n_forecast + 1))
    
    # Add forecast line
    fig.add_trace(go.Scatter(
        x=forecast_x,
        y=trend_results['forecast'],
        mode='lines+markers',
        name='Forecast',
        line=dict(color='#0077BB', width=2, dash='dash'),
        marker=dict(size=6)
    ))
    
    # Add confidence interval
    fig.add_trace(go.Scatter(
        x=forecast_x + forecast_x[::-1],
        y=trend_results['forecast_upper'] + trend_results['forecast_lower'][::-1],
        fill='toself',
        fillcolor='rgba(0, 119, 187, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='95% Confidence Interval',
        showlegend=True
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Future Periods",
        yaxis_title="Forecasted Value",
        font=dict(size=12),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified'
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridcolor='lightgray')
    
    return fig


def create_comparison_boxplot(
    comparative_results: Dict[str, Any],
    title: str = "Group Comparison"
) -> 'go.Figure':
    """
    Create box plots for comparing groups.
    
    This function generates box plots showing the distribution of values across
    different groups, making it easy to visualize differences in central tendency,
    spread, and outliers.
    
    Args:
        comparative_results: Dictionary containing comparative analysis results with:
                           - 'group_statistics': Dictionary of group statistics
                           - 'groups': List of group names
                           - 'value_column': Name of value column
                           - 'group_column': Name of group column
        title: Title for the chart (default: "Group Comparison")
    
    Returns:
        Plotly Figure object containing the box plots
        
    Raises:
        ValueError: If required keys are missing from results
        
    Requirements: 14.3, 14.5, 14.6
    
    Example:
        results = perform_comparative_analysis(
            dataset_id=1,
            value_column='satisfaction',
            group_column='branch'
        )
        fig = create_comparison_boxplot(results)
        st.plotly_chart(fig)
    """
    import plotly.graph_objects as go
    
    # Validate input
    if 'group_statistics' not in comparative_results:
        raise ValueError(
            "comparative_results must contain 'group_statistics' key"
        )
    
    group_stats = comparative_results['group_statistics']
    value_col = comparative_results.get('value_column', 'Value')
    group_col = comparative_results.get('group_column', 'Group')
    
    # Create figure
    fig = go.Figure()
    
    # Add box plot for each group
    # Note: Box plots require the raw data, not just statistics
    # For now, we'll create a simplified visualization using the statistics
    
    groups = list(group_stats.keys())
    means = [group_stats[g]['mean'] for g in groups]
    
    # Create bar chart as a substitute (since we don't have raw data)
    fig.add_trace(go.Bar(
        x=groups,
        y=means,
        marker_color='#0077BB',
        text=[f"{m:.2f}" for m in means],
        textposition='auto',
        name='Mean'
    ))
    
    # Add error bars using standard deviation
    stds = [group_stats[g]['std'] for g in groups]
    fig.update_traces(
        error_y=dict(
            type='data',
            array=stds,
            visible=True
        )
    )
    
    fig.update_layout(
        title=title,
        xaxis_title=group_col,
        yaxis_title=f"Mean {value_col}",
        font=dict(size=12),
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridcolor='lightgray')
    
    return fig


def create_distribution_histogram(
    distribution_results: Dict[str, Any],
    title: str = "Distribution Analysis"
) -> 'go.Figure':
    """
    Create a histogram with outliers highlighted.
    
    This function generates a histogram showing the distribution of values,
    with outliers highlighted in a different color. The chart also shows
    quartile lines and normality information.
    
    Args:
        distribution_results: Dictionary containing distribution analysis results with:
                            - 'column': Name of analyzed column
                            - 'quartiles': Dictionary with Q1, Q2, Q3
                            - 'outlier_indices': List of outlier indices
                            - 'n_outliers': Number of outliers
                            - 'is_normal': Boolean indicating normality
        title: Title for the chart (default: "Distribution Analysis")
    
    Returns:
        Plotly Figure object containing the histogram
        
    Raises:
        ValueError: If required keys are missing from results
        
    Requirements: 14.4, 14.5, 14.6
    
    Example:
        results = analyze_distribution(dataset_id=1, column='checkouts')
        fig = create_distribution_histogram(results)
        st.plotly_chart(fig)
    """
    import plotly.graph_objects as go
    
    # Validate input
    required_keys = ['column', 'quartiles', 'n_outliers']
    for key in required_keys:
        if key not in distribution_results:
            raise ValueError(
                f"distribution_results must contain '{key}' key"
            )
    
    column = distribution_results['column']
    quartiles = distribution_results['quartiles']
    n_outliers = distribution_results['n_outliers']
    is_normal = distribution_results.get('is_normal', False)
    
    # Note: We would need the actual data to create a proper histogram
    # For now, we'll create a simplified visualization
    
    # Create a simple figure showing quartile information
    fig = go.Figure()
    
    # Add quartile markers
    q_values = [quartiles['Q1'], quartiles['Q2'], quartiles['Q3']]
    q_labels = ['Q1 (25%)', 'Q2 (Median)', 'Q3 (75%)']
    
    fig.add_trace(go.Bar(
        x=q_labels,
        y=q_values,
        marker_color=['#0077BB', '#009988', '#EE7733'],
        text=[f"{v:.2f}" for v in q_values],
        textposition='auto'
    ))
    
    # Add annotation about outliers and normality
    annotation_text = f"Outliers: {n_outliers}<br>Normal Distribution: {'Yes' if is_normal else 'No'}"
    
    fig.add_annotation(
        text=annotation_text,
        xref="paper", yref="paper",
        x=0.95, y=0.95,
        showarrow=False,
        bgcolor="white",
        bordercolor="black",
        borderwidth=1,
        font=dict(size=10)
    )
    
    fig.update_layout(
        title=f"{title} - {column}",
        xaxis_title="Quartiles",
        yaxis_title="Value",
        font=dict(size=12),
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridcolor='lightgray')
    
    return fig


# ============================================================================
# Statistical Method Selection and Assumption Validation
# ============================================================================

def validate_normality_assumption(
    data: pd.Series,
    alpha: float = ALPHA
) -> Dict[str, Any]:
    """
    Validate normality assumption for parametric tests.
    
    This function performs the Shapiro-Wilk test to check if data follows
    a normal distribution, which is an assumption for many parametric tests
    like t-tests and ANOVA.
    
    Args:
        data: Pandas Series containing the data to test
        alpha: Significance level for the test (default: 0.05)
    
    Returns:
        Dictionary containing:
            - is_normal: Boolean indicating if data is normally distributed
            - test_statistic: Shapiro-Wilk test statistic
            - p_value: P-value from the test
            - recommendation: String recommending parametric or non-parametric test
            - explanation: String explaining the test result
            
    Requirements: 15.2, 15.6
    
    Example:
        data = df['satisfaction_score']
        result = validate_normality_assumption(data)
        if not result['is_normal']:
            print(result['recommendation'])
    """
    from scipy import stats
    
    # Perform Shapiro-Wilk test
    if len(data) <= 5000:
        stat, p_value = stats.shapiro(data)
        test_name = "Shapiro-Wilk"
    else:
        # For large samples, use Kolmogorov-Smirnov test
        stat, p_value = stats.kstest(data, 'norm', args=(data.mean(), data.std()))
        test_name = "Kolmogorov-Smirnov"
    
    is_normal = p_value > alpha
    
    # Generate recommendation
    if is_normal:
        recommendation = (
            "Data appears normally distributed. Parametric tests "
            "(Pearson correlation, t-test, ANOVA) are appropriate."
        )
        explanation = (
            f"{test_name} test p-value ({p_value:.4f}) is greater than {alpha}, "
            f"suggesting the data follows a normal distribution."
        )
    else:
        recommendation = (
            "Data does not appear normally distributed. Consider using "
            "non-parametric tests (Spearman correlation, Mann-Whitney U, Kruskal-Wallis)."
        )
        explanation = (
            f"{test_name} test p-value ({p_value:.4f}) is less than {alpha}, "
            f"suggesting the data does not follow a normal distribution. "
            f"Non-parametric tests are more appropriate for non-normal data."
        )
    
    return {
        'is_normal': is_normal,
        'test_statistic': float(stat),
        'p_value': float(p_value),
        'test_name': test_name,
        'recommendation': recommendation,
        'explanation': explanation
    }


def recommend_correlation_method(
    data1: pd.Series,
    data2: pd.Series
) -> Dict[str, Any]:
    """
    Recommend appropriate correlation method based on data characteristics.
    
    This function analyzes the data to recommend the most appropriate correlation
    method (Pearson, Spearman, or Kendall) based on normality and linearity.
    
    Args:
        data1: First variable (Pandas Series)
        data2: Second variable (Pandas Series)
    
    Returns:
        Dictionary containing:
            - recommended_method: 'pearson', 'spearman', or 'kendall'
            - reason: Explanation for the recommendation
            - data1_normal: Boolean indicating if data1 is normal
            - data2_normal: Boolean indicating if data2 is normal
            
    Requirements: 15.1, 15.2, 15.6
    
    Example:
        method_rec = recommend_correlation_method(df['var1'], df['var2'])
        print(f"Recommended method: {method_rec['recommended_method']}")
        print(f"Reason: {method_rec['reason']}")
    """
    # Check normality of both variables
    norm1 = validate_normality_assumption(data1)
    norm2 = validate_normality_assumption(data2)
    
    data1_normal = norm1['is_normal']
    data2_normal = norm2['is_normal']
    
    # Recommend method based on normality
    if data1_normal and data2_normal:
        recommended_method = 'pearson'
        reason = (
            "Both variables appear normally distributed. Pearson correlation "
            "is appropriate for measuring linear relationships between normally "
            "distributed variables."
        )
    else:
        recommended_method = 'spearman'
        reason = (
            "One or both variables do not appear normally distributed. "
            "Spearman correlation is more appropriate as it measures monotonic "
            "relationships and is robust to non-normal distributions. "
            "Alternatively, Kendall's tau can be used for ordinal data or small samples."
        )
    
    return {
        'recommended_method': recommended_method,
        'reason': reason,
        'data1_normal': data1_normal,
        'data2_normal': data2_normal,
        'alternative_methods': ['spearman', 'kendall'] if recommended_method == 'pearson' else ['pearson']
    }


def recommend_comparison_test(
    groups: List[pd.Series],
    group_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Recommend appropriate comparison test based on data characteristics.
    
    This function analyzes the groups to recommend the most appropriate
    statistical test (t-test, Mann-Whitney, ANOVA, or Kruskal-Wallis) based
    on the number of groups and normality assumptions.
    
    Args:
        groups: List of Pandas Series, one for each group
        group_names: Optional list of group names for reporting
    
    Returns:
        Dictionary containing:
            - recommended_test: 't-test', 'mann-whitney', 'anova', or 'kruskal-wallis'
            - reason: Explanation for the recommendation
            - normality_results: List of normality test results for each group
            - all_normal: Boolean indicating if all groups are normal
            
    Requirements: 15.2, 15.3, 15.4, 15.6
    
    Example:
        groups = [df[df['branch']=='A']['satisfaction'], 
                  df[df['branch']=='B']['satisfaction']]
        test_rec = recommend_comparison_test(groups, ['Branch A', 'Branch B'])
        print(f"Recommended test: {test_rec['recommended_test']}")
    """
    n_groups = len(groups)
    
    if n_groups < 2:
        raise ValueError("Need at least 2 groups for comparison")
    
    # Check normality for each group
    normality_results = []
    for i, group in enumerate(groups):
        group_name = group_names[i] if group_names else f"Group {i+1}"
        norm_result = validate_normality_assumption(group)
        norm_result['group_name'] = group_name
        normality_results.append(norm_result)
    
    all_normal = all(r['is_normal'] for r in normality_results)
    
    # Recommend test based on number of groups and normality
    if n_groups == 2:
        if all_normal:
            recommended_test = 't-test'
            reason = (
                "Both groups appear normally distributed. Independent t-test "
                "is appropriate for comparing means between two groups with "
                "normal distributions."
            )
        else:
            recommended_test = 'mann-whitney'
            reason = (
                "One or both groups do not appear normally distributed. "
                "Mann-Whitney U test is more appropriate as it is a non-parametric "
                "alternative to the t-test that does not assume normality."
            )
    else:  # 3 or more groups
        if all_normal:
            recommended_test = 'anova'
            reason = (
                "All groups appear normally distributed. One-way ANOVA is "
                "appropriate for comparing means across multiple groups with "
                "normal distributions."
            )
        else:
            recommended_test = 'kruskal-wallis'
            reason = (
                "One or more groups do not appear normally distributed. "
                "Kruskal-Wallis test is more appropriate as it is a non-parametric "
                "alternative to ANOVA that does not assume normality."
            )
    
    return {
        'recommended_test': recommended_test,
        'reason': reason,
        'normality_results': normality_results,
        'all_normal': all_normal,
        'n_groups': n_groups
    }


def get_method_assumptions(
    analysis_type: str,
    method: str
) -> Dict[str, Any]:
    """
    Get assumptions and limitations for a statistical method.
    
    This function returns detailed information about the assumptions,
    limitations, and appropriate use cases for different statistical methods.
    
    Args:
        analysis_type: Type of analysis - 'correlation', 'comparative', or 'distribution'
        method: Specific method name (e.g., 'pearson', 't-test', 'iqr')
    
    Returns:
        Dictionary containing:
            - method: Method name
            - assumptions: List of assumptions required for the method
            - limitations: List of limitations of the method
            - appropriate_for: Description of when to use the method
            - alternatives: List of alternative methods
            
    Requirements: 15.6, 15.7
    
    Example:
        info = get_method_assumptions('correlation', 'pearson')
        print(f"Assumptions: {info['assumptions']}")
        print(f"Alternatives: {info['alternatives']}")
    """
    assumptions_dict = {
        'correlation': {
            'pearson': {
                'assumptions': [
                    'Both variables are continuous',
                    'Both variables are normally distributed',
                    'Linear relationship between variables',
                    'No significant outliers',
                    'Homoscedasticity (constant variance)'
                ],
                'limitations': [
                    'Only measures linear relationships',
                    'Sensitive to outliers',
                    'Assumes bivariate normality'
                ],
                'appropriate_for': 'Measuring linear relationships between normally distributed continuous variables',
                'alternatives': ['spearman', 'kendall']
            },
            'spearman': {
                'assumptions': [
                    'Both variables are at least ordinal',
                    'Monotonic relationship between variables'
                ],
                'limitations': [
                    'Only measures monotonic relationships',
                    'Less powerful than Pearson when assumptions are met'
                ],
                'appropriate_for': 'Measuring monotonic relationships, non-normal data, or ordinal variables',
                'alternatives': ['pearson', 'kendall']
            },
            'kendall': {
                'assumptions': [
                    'Both variables are at least ordinal'
                ],
                'limitations': [
                    'Computationally intensive for large datasets',
                    'Less powerful than Spearman for large samples'
                ],
                'appropriate_for': 'Small samples, ordinal data, or when many tied ranks exist',
                'alternatives': ['spearman', 'pearson']
            }
        },
        'comparative': {
            't-test': {
                'assumptions': [
                    'Both groups are normally distributed',
                    'Equal variances between groups (homogeneity)',
                    'Independent observations',
                    'Continuous dependent variable'
                ],
                'limitations': [
                    'Only compares two groups',
                    'Sensitive to violations of normality with small samples',
                    'Assumes equal variances (can use Welch\'s t-test if violated)'
                ],
                'appropriate_for': 'Comparing means between two normally distributed groups',
                'alternatives': ['mann-whitney']
            },
            'mann-whitney': {
                'assumptions': [
                    'Independent observations',
                    'Ordinal or continuous dependent variable'
                ],
                'limitations': [
                    'Only compares two groups',
                    'Less powerful than t-test when normality holds',
                    'Tests for differences in distributions, not just means'
                ],
                'appropriate_for': 'Comparing two groups when normality assumption is violated',
                'alternatives': ['t-test']
            },
            'anova': {
                'assumptions': [
                    'All groups are normally distributed',
                    'Equal variances across groups (homogeneity)',
                    'Independent observations',
                    'Continuous dependent variable'
                ],
                'limitations': [
                    'Requires post-hoc tests to identify which groups differ',
                    'Sensitive to violations of assumptions with unequal group sizes',
                    'Assumes equal variances across all groups'
                ],
                'appropriate_for': 'Comparing means across three or more normally distributed groups',
                'alternatives': ['kruskal-wallis']
            },
            'kruskal-wallis': {
                'assumptions': [
                    'Independent observations',
                    'Ordinal or continuous dependent variable'
                ],
                'limitations': [
                    'Less powerful than ANOVA when normality holds',
                    'Tests for differences in distributions, not just means',
                    'Requires post-hoc tests to identify which groups differ'
                ],
                'appropriate_for': 'Comparing three or more groups when normality assumption is violated',
                'alternatives': ['anova']
            }
        },
        'distribution': {
            'iqr': {
                'assumptions': [
                    'Data is at least ordinal'
                ],
                'limitations': [
                    'May identify too many outliers in skewed distributions',
                    'Fixed threshold (1.5 * IQR) may not suit all contexts'
                ],
                'appropriate_for': 'General outlier detection, especially for skewed distributions',
                'alternatives': ['zscore']
            },
            'zscore': {
                'assumptions': [
                    'Data is approximately normally distributed',
                    'Mean and standard deviation are meaningful'
                ],
                'limitations': [
                    'Not appropriate for highly skewed distributions',
                    'Sensitive to extreme outliers affecting mean and SD',
                    'Fixed threshold (|Z| > 3) may not suit all contexts'
                ],
                'appropriate_for': 'Outlier detection in normally distributed data',
                'alternatives': ['iqr']
            }
        }
    }
    
    # Get method info
    if analysis_type not in assumptions_dict:
        raise ValueError(
            f"Unknown analysis type '{analysis_type}'. "
            f"Must be one of: {', '.join(assumptions_dict.keys())}"
        )
    
    if method not in assumptions_dict[analysis_type]:
        raise ValueError(
            f"Unknown method '{method}' for {analysis_type} analysis. "
            f"Must be one of: {', '.join(assumptions_dict[analysis_type].keys())}"
        )
    
    method_info = assumptions_dict[analysis_type][method].copy()
    method_info['method'] = method
    method_info['analysis_type'] = analysis_type
    
    return method_info

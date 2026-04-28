# Quantitative Analysis Enhancement Proposal

## Executive Summary

The current Library Assessment Decision Support System has strong **qualitative analysis** capabilities (sentiment analysis, theme identification) but limited **quantitative analysis** features. This proposal outlines how to add comprehensive quantitative analysis capabilities to complement the existing qualitative features.

**Current State:**
- ✅ Qualitative: Sentiment analysis, theme extraction, representative quotes
- ✅ Basic Statistics: Mean, median, std dev for numeric columns
- ❌ Advanced Quantitative: Statistical tests, correlations, trends, forecasting
- ❌ Comparative Analysis: Cross-dataset comparisons, benchmarking
- ❌ Time Series Analysis: Trend detection, seasonality, forecasting

---

## Current System Analysis

### Existing Capabilities

#### 1. Data Types Supported
- **Survey Responses**: Text responses with sentiment scores
- **Usage Statistics**: Numeric metrics (visits, checkouts, etc.)
- **Circulation Data**: Categorical and numeric data

#### 2. Current Analysis Features

**Qualitative Analysis** (`modules/qualitative_analysis.py`):
- Sentiment analysis using TextBlob
- Theme identification using TF-IDF + K-means
- Representative quote extraction
- Sentiment distribution statistics

**Statistical Summaries** (`modules/report_generator.py`):
- Descriptive statistics (mean, median, std dev, min, max, count)
- Categorical distributions (counts and percentages)
- Response length statistics

**Visualizations** (`modules/visualization.py`):
- Bar charts (categorical comparisons)
- Line charts (time series trends)
- Pie charts (proportions)

### Gaps Identified

1. **No Statistical Testing**: No hypothesis testing, significance tests, or confidence intervals
2. **No Correlation Analysis**: Cannot identify relationships between variables
3. **No Trend Analysis**: Limited time series analysis capabilities
4. **No Comparative Analysis**: Cannot compare across datasets or time periods
5. **No Forecasting**: No predictive capabilities
6. **No Segmentation**: No clustering or segmentation of numeric data
7. **No Outlier Detection**: No anomaly detection capabilities

---

## Proposed Quantitative Analysis Module

### Module Structure

```
modules/quantitative_analysis.py
```

### Core Features

#### 1. Descriptive Statistics (Enhanced)
**Current**: Basic mean, median, std dev
**Proposed**: Add quartiles, IQR, skewness, kurtosis, percentiles

```python
def calculate_descriptive_stats(dataset_id: int, column: str) -> Dict[str, Any]:
    """
    Calculate comprehensive descriptive statistics.
    
    Returns:
        {
            'mean': float,
            'median': float,
            'mode': float,
            'std_dev': float,
            'variance': float,
            'min': float,
            'max': float,
            'range': float,
            'q1': float,  # 25th percentile
            'q3': float,  # 75th percentile
            'iqr': float,  # Interquartile range
            'skewness': float,
            'kurtosis': float,
            'percentiles': {5: float, 10: float, ..., 95: float}
        }
    """
```

#### 2. Correlation Analysis
**Purpose**: Identify relationships between numeric variables

```python
def calculate_correlations(dataset_id: int, method: str = 'pearson') -> Dict[str, Any]:
    """
    Calculate correlation matrix for numeric columns.
    
    Args:
        dataset_id: Dataset identifier
        method: 'pearson', 'spearman', or 'kendall'
        
    Returns:
        {
            'correlation_matrix': pd.DataFrame,
            'significant_correlations': List[Dict],  # p-value < 0.05
            'strongest_correlations': List[Dict],  # Top 10 by absolute value
            'interpretation': str  # LLM-generated interpretation
        }
    """
```

#### 3. Trend Analysis
**Purpose**: Detect trends and patterns in time series data

```python
def analyze_trends(dataset_id: int, date_column: str, value_column: str) -> Dict[str, Any]:
    """
    Analyze trends in time series data.
    
    Returns:
        {
            'trend_direction': str,  # 'increasing', 'decreasing', 'stable'
            'trend_strength': float,  # R-squared value
            'slope': float,
            'intercept': float,
            'seasonal_pattern': bool,
            'seasonality_period': Optional[int],  # days/months
            'moving_averages': {
                '7_day': List[float],
                '30_day': List[float]
            },
            'forecast': {
                'next_7_days': List[float],
                'confidence_interval': List[Tuple[float, float]]
            }
        }
    """
```

#### 4. Comparative Analysis
**Purpose**: Compare metrics across datasets, time periods, or categories

```python
def compare_datasets(dataset_ids: List[int], metric: str) -> Dict[str, Any]:
    """
    Compare a metric across multiple datasets.
    
    Returns:
        {
            'datasets': List[str],
            'metric': str,
            'values': List[float],
            'statistical_test': {
                'test_name': str,  # 'ANOVA', 't-test', etc.
                'statistic': float,
                'p_value': float,
                'significant': bool,
                'interpretation': str
            },
            'effect_size': float,
            'visualization_data': pd.DataFrame
        }
    """
```

#### 5. Distribution Analysis
**Purpose**: Analyze data distributions and test for normality

```python
def analyze_distribution(dataset_id: int, column: str) -> Dict[str, Any]:
    """
    Analyze distribution of numeric data.
    
    Returns:
        {
            'distribution_type': str,  # 'normal', 'skewed', 'bimodal', etc.
            'normality_test': {
                'test_name': str,  # 'Shapiro-Wilk'
                'statistic': float,
                'p_value': float,
                'is_normal': bool
            },
            'histogram_data': List[Dict],
            'outliers': {
                'count': int,
                'values': List[float],
                'indices': List[int]
            },
            'recommended_transformations': List[str]
        }
    """
```

#### 6. Segmentation Analysis
**Purpose**: Identify natural groupings in numeric data

```python
def segment_data(dataset_id: int, columns: List[str], n_segments: int = 3) -> Dict[str, Any]:
    """
    Segment data using K-means clustering on numeric columns.
    
    Returns:
        {
            'n_segments': int,
            'segments': List[Dict],  # Each with centroid, size, characteristics
            'silhouette_score': float,  # Quality metric
            'segment_profiles': List[Dict],  # Statistical profile per segment
            'visualization_data': pd.DataFrame
        }
    """
```

#### 7. Outlier Detection
**Purpose**: Identify anomalies and unusual patterns

```python
def detect_outliers(dataset_id: int, column: str, method: str = 'iqr') -> Dict[str, Any]:
    """
    Detect outliers using various methods.
    
    Args:
        method: 'iqr', 'zscore', 'isolation_forest'
        
    Returns:
        {
            'method': str,
            'outlier_count': int,
            'outlier_percentage': float,
            'outliers': List[Dict],  # Each with value, index, severity
            'threshold': float,
            'visualization_data': pd.DataFrame
        }
    """
```

#### 8. Hypothesis Testing
**Purpose**: Test statistical hypotheses

```python
def test_hypothesis(dataset_id: int, test_type: str, **kwargs) -> Dict[str, Any]:
    """
    Perform statistical hypothesis tests.
    
    Args:
        test_type: 't-test', 'chi-square', 'anova', 'mann-whitney'
        
    Returns:
        {
            'test_name': str,
            'null_hypothesis': str,
            'alternative_hypothesis': str,
            'statistic': float,
            'p_value': float,
            'reject_null': bool,
            'confidence_level': float,
            'interpretation': str,  # LLM-generated
            'effect_size': Optional[float]
        }
    """
```

---

## Integration Points

### 1. Database Schema Updates

Add new table for quantitative analysis results:

```sql
CREATE TABLE IF NOT EXISTS quantitative_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id INTEGER,
    analysis_type TEXT,  -- 'correlation', 'trend', 'comparison', etc.
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parameters TEXT,  -- JSON
    results TEXT,  -- JSON
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
);
```

### 2. Streamlit UI Updates

Add new page: **"Quantitative Analysis"**

**Page Structure:**
```
📊 Quantitative Analysis
├── Dataset Selection
├── Analysis Type Selection
│   ├── Descriptive Statistics
│   ├── Correlation Analysis
│   ├── Trend Analysis
│   ├── Comparative Analysis
│   ├── Distribution Analysis
│   ├── Segmentation
│   ├── Outlier Detection
│   └── Hypothesis Testing
├── Parameter Configuration
├── Results Display
│   ├── Statistical Tables
│   ├── Visualizations
│   └── LLM-Generated Interpretation
└── Export Options
```

### 3. Report Generator Integration

Update `modules/report_generator.py` to include quantitative analysis:

```python
def create_report(
    dataset_ids: List[int],
    include_viz: bool = True,
    include_qualitative: bool = False,
    include_quantitative: bool = False,  # NEW
    quantitative_analyses: Optional[List[str]] = None,  # NEW
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create complete report with quantitative analysis.
    
    Args:
        quantitative_analyses: List of analysis types to include
            ['correlations', 'trends', 'comparisons', 'distributions']
    """
```

### 4. Visualization Enhancements

Add new chart types to `modules/visualization.py`:

```python
# New visualization functions
def create_correlation_heatmap(correlation_matrix: pd.DataFrame) -> go.Figure
def create_scatter_plot(data: pd.DataFrame, x: str, y: str) -> go.Figure
def create_box_plot(data: pd.DataFrame, column: str, group_by: Optional[str]) -> go.Figure
def create_histogram(data: pd.DataFrame, column: str, bins: int = 30) -> go.Figure
def create_time_series_with_forecast(data: pd.DataFrame, forecast: pd.DataFrame) -> go.Figure
```

---

## Implementation Plan

### Phase 1: Core Quantitative Module (Week 1-2)
- [ ] Create `modules/quantitative_analysis.py`
- [ ] Implement descriptive statistics (enhanced)
- [ ] Implement correlation analysis
- [ ] Implement distribution analysis
- [ ] Add database schema updates
- [ ] Write unit tests

### Phase 2: Time Series & Trends (Week 3)
- [ ] Implement trend analysis
- [ ] Implement forecasting (simple moving average, linear regression)
- [ ] Add time series visualizations
- [ ] Write integration tests

### Phase 3: Comparative & Advanced Analysis (Week 4)
- [ ] Implement comparative analysis
- [ ] Implement hypothesis testing
- [ ] Implement segmentation analysis
- [ ] Implement outlier detection
- [ ] Write property-based tests

### Phase 4: UI Integration (Week 5)
- [ ] Create Quantitative Analysis page in Streamlit
- [ ] Add analysis type selection
- [ ] Add parameter configuration UI
- [ ] Add results display with visualizations
- [ ] Add export functionality

### Phase 5: Report Integration (Week 6)
- [ ] Update report generator to include quantitative analysis
- [ ] Add quantitative sections to PDF/Markdown exports
- [ ] Add LLM-generated interpretations
- [ ] Write end-to-end tests
- [ ] Update documentation

---

## Dependencies

### New Python Packages Required

```txt
# Statistical analysis
scipy>=1.11.0           # Statistical tests, distributions
statsmodels>=0.14.0     # Time series, regression, ANOVA
scikit-learn>=1.3.0     # Already included (clustering, outliers)

# Optional (for advanced features)
prophet>=1.1.0          # Facebook's forecasting library (optional)
```

### Update requirements.txt

```bash
# Add to requirements.txt
scipy>=1.11.0
statsmodels>=0.14.0
```

---

## Example Use Cases

### Use Case 1: Library Visit Trends
**Question**: "Are library visits increasing or decreasing over time?"

**Analysis**:
1. Trend analysis on usage_statistics (visits over time)
2. Seasonal decomposition
3. Forecast next 30 days
4. Statistical significance test

**Output**:
- Trend direction and strength
- Seasonal patterns identified
- Forecast with confidence intervals
- Visualization with trend line

### Use Case 2: Correlation Between Services
**Question**: "Is there a relationship between reference desk usage and circulation?"

**Analysis**:
1. Correlation analysis between two metrics
2. Scatter plot visualization
3. Statistical significance test
4. LLM interpretation

**Output**:
- Correlation coefficient (r = 0.72, p < 0.001)
- Scatter plot with regression line
- Interpretation: "Strong positive correlation suggests..."

### Use Case 3: Comparing Branches
**Question**: "Do different library branches have significantly different satisfaction scores?"

**Analysis**:
1. Comparative analysis across datasets (branches)
2. ANOVA test
3. Box plot visualization
4. Post-hoc tests if significant

**Output**:
- Statistical test results
- Box plots comparing distributions
- Pairwise comparisons
- Interpretation: "Branch A significantly higher than B and C..."

### Use Case 4: Identifying Unusual Patterns
**Question**: "Are there any unusual spikes or drops in circulation data?"

**Analysis**:
1. Outlier detection using IQR method
2. Time series visualization with outliers highlighted
3. Context analysis (dates, events)

**Output**:
- List of outliers with dates and values
- Visualization with outliers marked
- Possible explanations

---

## Benefits

### 1. Comprehensive Analysis
- Combines qualitative (themes, sentiment) with quantitative (trends, correlations)
- Provides complete picture of library assessment data

### 2. Evidence-Based Decision Making
- Statistical significance testing
- Confidence intervals
- Effect sizes

### 3. Predictive Capabilities
- Forecasting future trends
- Identifying patterns early
- Proactive planning

### 4. Comparative Insights
- Benchmark across branches
- Compare time periods
- Identify best practices

### 5. Anomaly Detection
- Identify unusual patterns
- Early warning system
- Quality control

---

## Risks & Mitigation

### Risk 1: Complexity for Non-Technical Users
**Mitigation**:
- Provide LLM-generated plain language interpretations
- Use visual representations
- Offer guided workflows
- Include tooltips and help text

### Risk 2: Statistical Misinterpretation
**Mitigation**:
- Include warnings about assumptions
- Provide context and limitations
- Require minimum sample sizes
- Add validation checks

### Risk 3: Performance with Large Datasets
**Mitigation**:
- Implement sampling for very large datasets
- Add progress indicators
- Optimize calculations
- Cache results

### Risk 4: Increased Dependencies
**Mitigation**:
- Use well-maintained libraries (scipy, statsmodels)
- Make advanced features optional
- Provide fallbacks
- Document installation

---

## Success Metrics

1. **Adoption**: % of users who use quantitative analysis features
2. **Completeness**: % of reports that include quantitative analysis
3. **Accuracy**: Validation of statistical calculations
4. **Performance**: Analysis completion time < 30 seconds
5. **User Satisfaction**: Feedback on usefulness and clarity

---

## Next Steps

1. **Review & Approval**: Review this proposal with stakeholders
2. **Prioritization**: Decide which features are MVP vs. future enhancements
3. **Spec Creation**: Create detailed spec for quantitative analysis module
4. **Implementation**: Follow 6-week implementation plan
5. **Testing**: Comprehensive testing with real library data
6. **Documentation**: Update user guide and technical docs
7. **Training**: Provide training materials for users

---

## Conclusion

Adding quantitative analysis capabilities will transform the system from a qualitative-focused tool to a comprehensive library assessment platform. The proposed features complement existing qualitative analysis and provide statistical rigor for evidence-based decision making.

**Recommended Approach**: Start with Phase 1-2 (core statistics, correlations, trends) as MVP, then expand based on user feedback and needs.


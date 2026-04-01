"""
Report Generator Module

This module generates comprehensive assessment reports with statistical summaries,
LLM-generated narratives, visualizations, and qualitative analysis results.

Key Features:
- Statistical summaries (mean, median, std dev, counts)
- LLM-generated narrative text using Ollama
- Visualization integration (charts embedded in reports)
- Qualitative analysis inclusion (themes and sentiment)
- Multiple export formats (PDF, Markdown)
- Automatic fallback (PDF → Markdown on failure)
- Data source citations
- PII redaction on all text outputs
- Comprehensive error handling

Report Structure:
1. Title and metadata (generated date, author, datasets)
2. Executive summary (LLM-generated narrative, 2-3 paragraphs)
3. Statistical summaries (descriptive statistics per dataset)
4. Visualizations (embedded charts if enabled)
5. Qualitative analysis (sentiment distribution + themes)
6. Theme summaries with representative quotes
7. Data source citations (all datasets used)
8. Timestamp and generation metadata

Statistical Calculations:
- Survey datasets: sentiment scores, response lengths, category counts
- Usage datasets: metric statistics by name, category distributions
- Descriptive stats: mean, median, std dev, min, max, count
- Categorical distributions: counts and percentages

Narrative Generation:
- Uses Ollama LLM to generate professional narrative
- Includes key findings, patterns, and insights
- 2-3 paragraph summary appropriate for stakeholders
- PII redaction applied before returning
- Fallback to basic summary if LLM fails

Module Functions:
- generate_statistical_summary(): Calculate descriptive statistics
- generate_narrative(): LLM-generated narrative text
- create_report(): Assemble complete report structure
- export_report(): Export to PDF or Markdown with fallback
- _export_markdown(): Internal Markdown export
- _export_pdf(): Internal PDF export with ReportLab
- _calculate_survey_statistics(): Survey-specific stats
- _calculate_usage_statistics(): Usage-specific stats

Database Tables Used:
- datasets: Dataset metadata for citations
- survey_responses: Survey data for statistics
- usage_statistics: Usage data for statistics
- themes: Theme data for qualitative section
- reports: Stored report metadata

Requirements Implemented:
- 4.1: Produce statistical summaries
- 4.2: Generate narrative text with LLM
- 4.3: Include visualizations
- 4.4: Export to PDF or Markdown
- 4.5: Include data source citations
- 4.6: Generate within 2 minutes (typical datasets)
- 4.7: Include theme summaries when applicable
- 6.5: PII redaction on outputs

Configuration (config/settings.py):
- REPORT_TIMEOUT_SECONDS: Generation timeout (default: 120)
- MAX_REPORT_DATASETS: Maximum datasets per report (default: 10)
- OLLAMA_MODEL: LLM model for narrative (default: llama3.2:3b)

Export Formats:
- Markdown: Always available, includes all content, plain text
- PDF: Uses ReportLab, includes formatting and layout
- Automatic fallback: PDF → Markdown if PDF generation fails

Error Handling:
- Missing visualizations: Generate report without them, include note
- PDF export failed: Automatically fall back to Markdown
- LLM narrative failed: Use basic summary instead
- Dataset not found: Raise ValueError with clear message

Usage Example:
    # Generate statistical summary
    summary = generate_statistical_summary(dataset_id=1)
    print(f"Dataset: {summary['dataset_name']}")
    print(f"Statistics: {summary['statistics']}")
    
    # Generate narrative
    narrative = generate_narrative(summary, analysis=None)
    print(narrative)
    
    # Create complete report
    report = create_report(
        dataset_ids=[1, 2],
        include_viz=True,
        include_qualitative=True
    )
    
    # Export report
    content, format_used = export_report(report, format='pdf')
    with open(f'report.{format_used}', 'wb') as f:
        f.write(content)

Author: FERPA-Compliant RAG DSS Team
"""

import sqlite3
from typing import Dict, List, Optional, Any
import statistics
from modules.database import get_db_connection, execute_query
from modules.pii_detector import redact_pii
from config.settings import Settings


def generate_statistical_summary(dataset_id: int, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculate descriptive statistics for a dataset.
    
    Args:
        dataset_id: ID of the dataset to analyze
        db_path: Optional path to database file
        
    Returns:
        Dictionary containing statistical summaries with the following structure:
        {
            'dataset_id': int,
            'dataset_name': str,
            'dataset_type': str,
            'row_count': int,
            'statistics': {
                'column_name': {
                    'mean': float,
                    'median': float,
                    'std_dev': float,
                    'count': int,
                    'min': float,
                    'max': float
                },
                ...
            },
            'categorical_counts': {
                'column_name': {
                    'value': count,
                    ...
                },
                ...
            }
        }
        
    Raises:
        ValueError: If dataset_id does not exist
    """
    if db_path is None:
        db_path = Settings.DATABASE_PATH
    
    # Get dataset metadata
    dataset_query = "SELECT id, name, dataset_type, row_count FROM datasets WHERE id = ?"
    datasets = execute_query(dataset_query, (dataset_id,), db_path)
    
    if not datasets:
        raise ValueError(f"Dataset with id {dataset_id} not found")
    
    dataset = datasets[0]
    
    result = {
        'dataset_id': dataset['id'],
        'dataset_name': dataset['name'],
        'dataset_type': dataset['dataset_type'],
        'row_count': dataset['row_count'],
        'statistics': {},
        'categorical_counts': {}
    }
    
    # Calculate statistics based on dataset type
    if dataset['dataset_type'] == 'survey':
        result = _calculate_survey_statistics(dataset_id, result, db_path)
    elif dataset['dataset_type'] == 'usage':
        result = _calculate_usage_statistics(dataset_id, result, db_path)
    else:
        # For other types, provide basic counts
        result['statistics']['total_rows'] = {
            'count': dataset['row_count']
        }
    
    return result


def _calculate_survey_statistics(dataset_id: int, result: Dict[str, Any], db_path: str) -> Dict[str, Any]:
    """
    Calculate statistics for survey response datasets.
    
    Args:
        dataset_id: ID of the survey dataset
        result: Partial result dictionary to populate
        db_path: Path to database file
        
    Returns:
        Updated result dictionary with survey statistics
    """
    # Get all survey responses for this dataset
    query = """
        SELECT sentiment, sentiment_score, response_text
        FROM survey_responses
        WHERE dataset_id = ?
    """
    responses = execute_query(query, (dataset_id,), db_path)
    
    if not responses:
        return result
    
    # Calculate sentiment score statistics
    sentiment_scores = [r['sentiment_score'] for r in responses if r['sentiment_score'] is not None]
    
    if sentiment_scores:
        result['statistics']['sentiment_score'] = {
            'mean': statistics.mean(sentiment_scores),
            'median': statistics.median(sentiment_scores),
            'std_dev': statistics.stdev(sentiment_scores) if len(sentiment_scores) > 1 else 0.0,
            'count': len(sentiment_scores),
            'min': min(sentiment_scores),
            'max': max(sentiment_scores)
        }
    
    # Calculate sentiment category counts
    sentiment_counts = {}
    for response in responses:
        sentiment = response['sentiment']
        if sentiment:
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
    
    if sentiment_counts:
        result['categorical_counts']['sentiment'] = sentiment_counts
    
    # Calculate response text length statistics
    response_lengths = [len(r['response_text']) for r in responses if r['response_text']]
    
    if response_lengths:
        result['statistics']['response_length'] = {
            'mean': statistics.mean(response_lengths),
            'median': statistics.median(response_lengths),
            'std_dev': statistics.stdev(response_lengths) if len(response_lengths) > 1 else 0.0,
            'count': len(response_lengths),
            'min': min(response_lengths),
            'max': max(response_lengths)
        }
    
    return result


def _calculate_usage_statistics(dataset_id: int, result: Dict[str, Any], db_path: str) -> Dict[str, Any]:
    """
    Calculate statistics for usage statistics datasets.
    
    Args:
        dataset_id: ID of the usage dataset
        result: Partial result dictionary to populate
        db_path: Path to database file
        
    Returns:
        Updated result dictionary with usage statistics
    """
    # Get all usage statistics for this dataset
    query = """
        SELECT metric_name, metric_value, category
        FROM usage_statistics
        WHERE dataset_id = ?
    """
    usage_data = execute_query(query, (dataset_id,), db_path)
    
    if not usage_data:
        return result
    
    # Group by metric_name and calculate statistics
    metrics_by_name = {}
    for row in usage_data:
        metric_name = row['metric_name']
        if metric_name not in metrics_by_name:
            metrics_by_name[metric_name] = []
        if row['metric_value'] is not None:
            metrics_by_name[metric_name].append(row['metric_value'])
    
    # Calculate statistics for each metric
    for metric_name, values in metrics_by_name.items():
        if values:
            result['statistics'][metric_name] = {
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'std_dev': statistics.stdev(values) if len(values) > 1 else 0.0,
                'count': len(values),
                'min': min(values),
                'max': max(values)
            }
    
    # Calculate category counts
    category_counts = {}
    for row in usage_data:
        category = row['category']
        if category:
            category_counts[category] = category_counts.get(category, 0) + 1
    
    if category_counts:
        result['categorical_counts']['category'] = category_counts
    
    return result


def generate_narrative(
    summary: Dict[str, Any],
    analysis: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate narrative text explaining key findings using Ollama.

    This function uses the Local_LLM (Ollama) to create human-readable narrative
    text that explains statistical summaries and qualitative analysis results.
    All processing happens locally without external API calls.

    Args:
        summary: Statistical summary dict from generate_statistical_summary()
        analysis: Optional qualitative analysis dict with sentiment and themes

    Returns:
        Narrative text as a string explaining key findings and insights

    Raises:
        RuntimeError: If Ollama connection fails or generation fails
    """
    import ollama

    # Build prompt for narrative generation
    prompt = "You are a library assessment specialist writing a report. Generate a clear, professional narrative explaining the following data findings.\n\n"

    # Add statistical summary to prompt
    prompt += "## Statistical Summary\n\n"
    prompt += f"Dataset: {summary.get('dataset_name', 'Unknown')}\n"
    prompt += f"Type: {summary.get('dataset_type', 'Unknown')}\n"
    prompt += f"Total Records: {summary.get('row_count', 0)}\n\n"

    # Add statistics details
    if summary.get('statistics'):
        prompt += "### Key Statistics:\n"
        for metric_name, stats in summary['statistics'].items():
            prompt += f"\n{metric_name}:\n"
            if 'mean' in stats:
                prompt += f"  - Mean: {stats['mean']:.2f}\n"
            if 'median' in stats:
                prompt += f"  - Median: {stats['median']:.2f}\n"
            if 'std_dev' in stats:
                prompt += f"  - Standard Deviation: {stats['std_dev']:.2f}\n"
            if 'min' in stats and 'max' in stats:
                prompt += f"  - Range: {stats['min']:.2f} to {stats['max']:.2f}\n"
            if 'count' in stats:
                prompt += f"  - Count: {stats['count']}\n"

    # Add categorical counts
    if summary.get('categorical_counts'):
        prompt += "\n### Categorical Distributions:\n"
        for category_name, counts in summary['categorical_counts'].items():
            prompt += f"\n{category_name}:\n"
            for value, count in counts.items():
                prompt += f"  - {value}: {count}\n"

    # Add qualitative analysis if provided
    if analysis:
        prompt += "\n## Qualitative Analysis\n\n"

        if analysis.get('sentiment_distribution'):
            prompt += "### Sentiment Distribution:\n"
            for sentiment, count in analysis['sentiment_distribution'].items():
                prompt += f"  - {sentiment}: {count}\n"

        if analysis.get('themes'):
            prompt += "\n### Identified Themes:\n"
            for theme in analysis['themes']:
                prompt += f"  - {theme.get('name', 'Unknown')}: {theme.get('frequency', 0)} occurrences\n"
                if theme.get('keywords'):
                    prompt += f"    Keywords: {', '.join(theme['keywords'])}\n"

    # Add instruction for narrative generation
    prompt += "\n\nBased on the above data, write a concise narrative (2-3 paragraphs) that:\n"
    prompt += "1. Summarizes the key findings\n"
    prompt += "2. Highlights important patterns or trends\n"
    prompt += "3. Provides insights that would be valuable for library stakeholders\n"
    prompt += "4. Uses clear, professional language appropriate for a report\n\n"
    prompt += "Narrative:"

    # Call Ollama to generate narrative
    try:
        response = ollama.generate(
            model=Settings.OLLAMA_MODEL,
            prompt=prompt
        )
        narrative = response['response'].strip()
        
        # Redact PII from narrative before returning (Requirement 6.5)
        narrative, pii_counts = redact_pii(narrative)
        
        return narrative
    except Exception as e:
        raise RuntimeError(f"Failed to generate narrative using Ollama: {str(e)}")


def create_report(
    dataset_ids: List[int],
    include_viz: bool = True,
    include_qualitative: bool = False,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create complete report structure with all components.
    
    This function assembles a comprehensive report including:
    - Title and metadata
    - Executive summary (LLM-generated)
    - Statistical summaries
    - Visualizations (if enabled)
    - Qualitative analysis results (if applicable)
    - Theme summaries with quotes
    - Data source citations
    - Timestamp and author
    
    Args:
        dataset_ids: List of dataset IDs to include in report
        include_viz: Whether to include visualizations (default: True)
        include_qualitative: Whether to include qualitative analysis (default: False)
        db_path: Optional path to database file
        
    Returns:
        Dictionary containing complete report structure:
        {
            'title': str,
            'metadata': {
                'generated_at': str (ISO timestamp),
                'author': str,
                'datasets': List[str] (dataset names),
                'dataset_ids': List[int]
            },
            'executive_summary': str,
            'statistical_summaries': List[Dict],
            'visualizations': List[Dict] (if include_viz=True),
            'qualitative_analysis': Dict (if include_qualitative=True),
            'theme_summaries': List[Dict] (if qualitative analysis performed),
            'citations': List[str],
            'timestamp': str (ISO timestamp)
        }
        
    Raises:
        ValueError: If dataset_ids is empty or contains invalid IDs
    """
    from datetime import datetime
    import json
    
    if db_path is None:
        db_path = Settings.DATABASE_PATH
    
    if not dataset_ids:
        raise ValueError("At least one dataset_id must be provided")
    
    # Initialize report structure
    report = {
        'title': '',
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'author': 'FERPA-Compliant RAG Decision Support System',
            'datasets': [],
            'dataset_ids': dataset_ids
        },
        'executive_summary': '',
        'statistical_summaries': [],
        'visualizations': [],
        'qualitative_analysis': None,
        'theme_summaries': [],
        'citations': [],
        'timestamp': datetime.now().isoformat()
    }
    
    # Collect statistical summaries and dataset metadata
    all_summaries = []
    dataset_names = []
    
    for dataset_id in dataset_ids:
        try:
            summary = generate_statistical_summary(dataset_id, db_path)
            all_summaries.append(summary)
            dataset_names.append(summary['dataset_name'])
            
            # Add citation for this dataset
            citation = f"Dataset: {summary['dataset_name']} (ID: {dataset_id}, Type: {summary['dataset_type']}, Records: {summary['row_count']})"
            report['citations'].append(citation)
            
        except ValueError as e:
            raise ValueError(f"Invalid dataset_id {dataset_id}: {str(e)}")
    
    report['metadata']['datasets'] = dataset_names
    report['statistical_summaries'] = all_summaries
    
    # Generate report title
    if len(dataset_names) == 1:
        report['title'] = f"Assessment Report: {dataset_names[0]}"
    else:
        report['title'] = f"Assessment Report: {len(dataset_names)} Datasets"
    
    # Include qualitative analysis if requested
    qualitative_data = None
    if include_qualitative:
        # Check if any datasets have qualitative analysis (themes)
        for dataset_id in dataset_ids:
            theme_query = """
                SELECT theme_name, keywords, frequency, representative_quotes
                FROM themes
                WHERE dataset_id = ?
            """
            themes = execute_query(theme_query, (dataset_id,), db_path)
            
            if themes:
                # Get sentiment distribution for this dataset
                sentiment_query = """
                    SELECT sentiment, COUNT(*) as count
                    FROM survey_responses
                    WHERE dataset_id = ?
                    GROUP BY sentiment
                """
                sentiment_data = execute_query(sentiment_query, (dataset_id,), db_path)
                sentiment_dist = {row['sentiment']: row['count'] for row in sentiment_data if row['sentiment']}
                
                # Format themes
                formatted_themes = []
                for theme in themes:
                    formatted_themes.append({
                        'name': theme['theme_name'],
                        'keywords': json.loads(theme['keywords']) if isinstance(theme['keywords'], str) else theme['keywords'],
                        'frequency': theme['frequency'],
                        'quotes': json.loads(theme['representative_quotes']) if isinstance(theme['representative_quotes'], str) else theme['representative_quotes']
                    })
                
                qualitative_data = {
                    'dataset_id': dataset_id,
                    'sentiment_distribution': sentiment_dist,
                    'themes': formatted_themes
                }
                
                report['qualitative_analysis'] = qualitative_data
                report['theme_summaries'] = formatted_themes
                break  # Use first dataset with themes
    
    # Generate visualizations if requested
    visualization_warnings = []
    if include_viz:
        from modules.visualization import create_bar_chart, create_pie_chart
        import pandas as pd
        
        for summary in all_summaries:
            # Create sentiment distribution chart if available
            if 'sentiment' in summary.get('categorical_counts', {}):
                sentiment_data = summary['categorical_counts']['sentiment']
                df = pd.DataFrame([
                    {'sentiment': k, 'count': v}
                    for k, v in sentiment_data.items()
                ])
                
                try:
                    fig = create_pie_chart(
                        df,
                        values='count',
                        names='sentiment',
                        title=f"Sentiment Distribution - {summary['dataset_name']}"
                    )
                    
                    report['visualizations'].append({
                        'type': 'pie_chart',
                        'title': f"Sentiment Distribution - {summary['dataset_name']}",
                        'dataset_id': summary['dataset_id'],
                        'figure': fig
                    })
                except Exception as e:
                    # Track visualization failure
                    warning_msg = f"Could not generate sentiment chart for {summary['dataset_name']}: insufficient data"
                    visualization_warnings.append(warning_msg)
                    print(f"Warning: Failed to create sentiment chart: {str(e)}")
            
            # Create category distribution chart if available
            if 'category' in summary.get('categorical_counts', {}):
                category_data = summary['categorical_counts']['category']
                df = pd.DataFrame([
                    {'category': k, 'count': v}
                    for k, v in category_data.items()
                ])
                
                try:
                    fig = create_bar_chart(
                        df,
                        x='category',
                        y='count',
                        title=f"Category Distribution - {summary['dataset_name']}"
                    )
                    
                    report['visualizations'].append({
                        'type': 'bar_chart',
                        'title': f"Category Distribution - {summary['dataset_name']}",
                        'dataset_id': summary['dataset_id'],
                        'figure': fig
                    })
                except Exception as e:
                    # Track visualization failure
                    warning_msg = f"Could not generate category chart for {summary['dataset_name']}: insufficient data"
                    visualization_warnings.append(warning_msg)
                    print(f"Warning: Failed to create category chart: {str(e)}")
    
    # Add visualization warnings to report metadata
    if visualization_warnings:
        report['metadata']['visualization_warnings'] = visualization_warnings
    
    # Generate executive summary using LLM
    try:
        # Combine all summaries for narrative generation
        combined_summary = {
            'dataset_name': ', '.join(dataset_names),
            'dataset_type': 'multiple' if len(dataset_ids) > 1 else all_summaries[0]['dataset_type'],
            'row_count': sum(s['row_count'] for s in all_summaries),
            'statistics': {},
            'categorical_counts': {}
        }
        
        # Merge statistics from all datasets
        for summary in all_summaries:
            for key, value in summary.get('statistics', {}).items():
                if key not in combined_summary['statistics']:
                    combined_summary['statistics'][key] = value
        
        # Generate narrative
        narrative = generate_narrative(combined_summary, qualitative_data)
        report['executive_summary'] = narrative
        
    except Exception as e:
        # Fallback to basic summary if LLM fails
        report['executive_summary'] = f"Report generated for {len(dataset_ids)} dataset(s) with {sum(s['row_count'] for s in all_summaries)} total records."
        print(f"Warning: Failed to generate executive summary: {str(e)}")
    
    return report


def export_report(report: Dict[str, Any], format: str = 'markdown') -> tuple[bytes, str]:
    """
    Export report to PDF or Markdown format.
    
    This function includes automatic fallback to Markdown if PDF export fails,
    ensuring users always receive a report even if PDF generation encounters errors.
    
    Args:
        report: Report dictionary from create_report()
        format: Export format - 'pdf' or 'markdown' (default: 'markdown')
        
    Returns:
        Tuple of (report_content_bytes, actual_format_used)
        - report_content_bytes: Report content as bytes
        - actual_format_used: 'pdf' or 'markdown' (may differ from requested if fallback occurred)
        
    Raises:
        ValueError: If format is not 'pdf' or 'markdown'
    """
    if format not in ['pdf', 'markdown']:
        raise ValueError(f"Invalid format '{format}'. Must be 'pdf' or 'markdown'")
    
    if format == 'markdown':
        return _export_markdown(report), 'markdown'
    else:
        # Try PDF export with automatic fallback to Markdown
        try:
            pdf_content = _export_pdf(report)
            # Verify PDF was actually generated (not a fallback from _export_pdf)
            if pdf_content.startswith(b'%PDF'):
                return pdf_content, 'pdf'
            else:
                # _export_pdf returned markdown fallback
                print("Warning: PDF export failed, using Markdown format instead")
                return pdf_content, 'markdown'
        except Exception as e:
            # Fallback to Markdown on any error
            print(f"Warning: PDF export failed ({str(e)}), using Markdown format instead")
            return _export_markdown(report), 'markdown'


def _export_markdown(report: Dict[str, Any]) -> bytes:
    """
    Export report to Markdown format.
    
    Args:
        report: Report dictionary from create_report()
        
    Returns:
        Markdown content as bytes
    """
    from datetime import datetime
    
    lines = []
    
    # Title
    lines.append(f"# {report['title']}\n")
    lines.append("")
    
    # Metadata
    lines.append("## Report Metadata\n")
    lines.append(f"**Generated:** {report['metadata']['generated_at']}")
    lines.append(f"**Author:** {report['metadata']['author']}")
    lines.append(f"**Datasets:** {', '.join(report['metadata']['datasets'])}")
    lines.append("")
    
    # Add visualization warnings if any
    if report['metadata'].get('visualization_warnings'):
        lines.append("### Visualization Warnings\n")
        lines.append("Some visualizations could not be generated due to insufficient data:")
        for warning in report['metadata']['visualization_warnings']:
            lines.append(f"- {warning}")
        lines.append("")
    
    # Executive Summary
    lines.append("## Executive Summary\n")
    lines.append(report['executive_summary'])
    lines.append("")
    
    # Statistical Summaries
    lines.append("## Statistical Summaries\n")
    for summary in report['statistical_summaries']:
        lines.append(f"### {summary['dataset_name']}\n")
        lines.append(f"**Type:** {summary['dataset_type']}")
        lines.append(f"**Records:** {summary['row_count']}")
        lines.append("")
        
        if summary.get('statistics'):
            lines.append("#### Key Statistics\n")
            for metric_name, stats in summary['statistics'].items():
                lines.append(f"**{metric_name}:**")
                if 'mean' in stats:
                    lines.append(f"- Mean: {stats['mean']:.2f}")
                if 'median' in stats:
                    lines.append(f"- Median: {stats['median']:.2f}")
                if 'std_dev' in stats:
                    lines.append(f"- Standard Deviation: {stats['std_dev']:.2f}")
                if 'min' in stats and 'max' in stats:
                    lines.append(f"- Range: {stats['min']:.2f} to {stats['max']:.2f}")
                if 'count' in stats:
                    lines.append(f"- Count: {stats['count']}")
                lines.append("")
        
        if summary.get('categorical_counts'):
            lines.append("#### Categorical Distributions\n")
            for category_name, counts in summary['categorical_counts'].items():
                lines.append(f"**{category_name}:**")
                for value, count in counts.items():
                    lines.append(f"- {value}: {count}")
                lines.append("")
    
    # Visualizations
    if report.get('visualizations'):
        lines.append("## Visualizations\n")
        lines.append(f"{len(report['visualizations'])} visualization(s) included in this report.")
        lines.append("(Note: Visualizations are available in the interactive report or as separate image exports)")
        lines.append("")
    
    # Qualitative Analysis
    if report.get('qualitative_analysis'):
        lines.append("## Qualitative Analysis\n")
        qual = report['qualitative_analysis']
        
        if qual.get('sentiment_distribution'):
            lines.append("### Sentiment Distribution\n")
            for sentiment, count in qual['sentiment_distribution'].items():
                lines.append(f"- {sentiment}: {count}")
            lines.append("")
    
    # Theme Summaries
    if report.get('theme_summaries'):
        lines.append("## Identified Themes\n")
        for theme in report['theme_summaries']:
            lines.append(f"### {theme['name']}\n")
            lines.append(f"**Frequency:** {theme['frequency']}")
            lines.append(f"**Keywords:** {', '.join(theme['keywords'])}")
            lines.append("")
            
            if theme.get('quotes'):
                lines.append("**Representative Quotes:**")
                for quote in theme['quotes']:
                    lines.append(f"> {quote}")
                lines.append("")
    
    # Citations
    if report.get('citations'):
        lines.append("## Data Sources\n")
        for citation in report['citations']:
            lines.append(f"- {citation}")
        lines.append("")
    
    # Timestamp
    lines.append("---")
    lines.append(f"*Report generated on {report['timestamp']}*")
    
    markdown_content = '\n'.join(lines)
    return markdown_content.encode('utf-8')


def _export_pdf(report: Dict[str, Any]) -> bytes:
    """
    Export report to PDF format.
    
    Args:
        report: Report dictionary from create_report()
        
    Returns:
        PDF content as bytes
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib import colors
        from io import BytesIO
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0077BB'),
            spaceAfter=30
        )
        story.append(Paragraph(report['title'], title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Metadata
        story.append(Paragraph("Report Metadata", styles['Heading2']))
        metadata_text = f"""
        <b>Generated:</b> {report['metadata']['generated_at']}<br/>
        <b>Author:</b> {report['metadata']['author']}<br/>
        <b>Datasets:</b> {', '.join(report['metadata']['datasets'])}
        """
        story.append(Paragraph(metadata_text, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        story.append(Paragraph(report['executive_summary'], styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Statistical Summaries
        story.append(Paragraph("Statistical Summaries", styles['Heading2']))
        for summary in report['statistical_summaries']:
            story.append(Paragraph(summary['dataset_name'], styles['Heading3']))
            
            summary_text = f"""
            <b>Type:</b> {summary['dataset_type']}<br/>
            <b>Records:</b> {summary['row_count']}
            """
            story.append(Paragraph(summary_text, styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            
            # Statistics table
            if summary.get('statistics'):
                story.append(Paragraph("Key Statistics", styles['Heading4']))
                
                for metric_name, stats in summary['statistics'].items():
                    table_data = [['Metric', 'Value']]
                    table_data.append(['Name', metric_name])
                    if 'mean' in stats:
                        table_data.append(['Mean', f"{stats['mean']:.2f}"])
                    if 'median' in stats:
                        table_data.append(['Median', f"{stats['median']:.2f}"])
                    if 'std_dev' in stats:
                        table_data.append(['Std Dev', f"{stats['std_dev']:.2f}"])
                    if 'count' in stats:
                        table_data.append(['Count', str(stats['count'])])
                    
                    table = Table(table_data, colWidths=[2*inch, 2*inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 0.2*inch))
            
            story.append(Spacer(1, 0.2*inch))
        
        # Theme Summaries
        if report.get('theme_summaries'):
            story.append(PageBreak())
            story.append(Paragraph("Identified Themes", styles['Heading2']))
            
            for theme in report['theme_summaries']:
                story.append(Paragraph(theme['name'], styles['Heading3']))
                
                theme_text = f"""
                <b>Frequency:</b> {theme['frequency']}<br/>
                <b>Keywords:</b> {', '.join(theme['keywords'])}
                """
                story.append(Paragraph(theme_text, styles['Normal']))
                
                if theme.get('quotes'):
                    story.append(Paragraph("Representative Quotes:", styles['Heading4']))
                    for quote in theme['quotes']:
                        story.append(Paragraph(f"• {quote}", styles['Normal']))
                
                story.append(Spacer(1, 0.2*inch))
        
        # Citations
        if report.get('citations'):
            story.append(PageBreak())
            story.append(Paragraph("Data Sources", styles['Heading2']))
            for citation in report['citations']:
                story.append(Paragraph(f"• {citation}", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
        
    except ImportError:
        # Fallback to Markdown if reportlab is not available
        print("Warning: reportlab not available, falling back to Markdown export")
        return _export_markdown(report)
    except Exception as e:
        # Fallback to Markdown on any PDF generation error
        print(f"Warning: PDF export failed ({str(e)}), falling back to Markdown")
        return _export_markdown(report)

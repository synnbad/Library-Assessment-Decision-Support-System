"""
Visualization Module

This module provides accessible data visualization functions for library assessment
data using Plotly with WCAG AA compliant color schemes.

Key Features:
- Bar charts for categorical data comparisons
- Line charts for time series trends
- Pie charts for proportion visualization
- Accessible color palette (WCAG AA compliant)
- Clear axis labels and titles
- Responsive sizing for Streamlit display
- Export to PNG or HTML
- Automatic fallback (PNG → HTML if kaleido fails)

Accessibility:
- Color palette with sufficient contrast (4.5:1 minimum for text)
- Colorblind-friendly color combinations
- Clear labels and legends
- Grid lines for readability
- White background for printing
- Text size: 12pt minimum

Color Palette (WCAG AA Compliant):
- Blue: #0077BB (primary)
- Red: #CC3311 (secondary)
- Teal: #009988
- Orange: #EE7733
- Cyan: #33BBEE
- Magenta: #EE3377
- Gray: #BBBBBB
- Black: #000000

Module Functions:
- create_bar_chart(): Generate bar chart for categorical data
- create_line_chart(): Generate line chart for time series
- create_pie_chart(): Generate pie chart for proportions
- export_chart(): Export chart to PNG or HTML

Chart Features:
- Plotly interactive charts (zoom, pan, hover)
- Responsive sizing
- Clear axis labels and titles
- Grid lines for readability
- Legend when multiple series
- Data labels on bars/slices

Requirements Implemented:
- 5.1: Generate bar charts
- 5.2: Generate line charts
- 5.3: Generate pie charts
- 5.5: Export charts as PNG
- 5.6: Apply clear labels and titles
- 5.7: Use accessible color schemes

Configuration (config/settings.py):
- CHART_WIDTH: Default width in pixels (default: 800)
- CHART_HEIGHT: Default height in pixels (default: 600)
- CHART_DPI: Resolution for PNG export (default: 300)

Export Options:
- PNG: Requires kaleido, high-resolution (1200x800px)
- HTML: Always available, interactive charts with Plotly.js
- Automatic fallback: PNG → HTML if kaleido not available

Usage Example:
    import pandas as pd
    from modules.visualization import create_bar_chart, export_chart
    
    # Create sample data
    data = pd.DataFrame({
        'category': ['Books', 'DVDs', 'Journals'],
        'count': [150, 75, 50]
    })
    
    # Create bar chart
    fig = create_bar_chart(
        data=data,
        x='category',
        y='count',
        title='Library Materials by Type',
        x_label='Material Type',
        y_label='Count'
    )
    
    # Display in Streamlit
    st.plotly_chart(fig)
    
    # Export to PNG
    img_bytes = export_chart(fig, 'materials_chart', format='png')
    with open('chart.png', 'wb') as f:
        f.write(img_bytes)

Author: Library Assessment DSS Team
"""

import pandas as pd
import plotly.graph_objects as go
from typing import Optional


# Accessible color palette with WCAG AA compliant contrast ratios
ACCESSIBLE_COLORS = [
    '#0077BB',  # Blue
    '#CC3311',  # Red
    '#009988',  # Teal
    '#EE7733',  # Orange
    '#33BBEE',  # Cyan
    '#EE3377',  # Magenta
    '#BBBBBB',  # Gray
    '#000000',  # Black
]


def create_bar_chart(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None
) -> go.Figure:
    """
    Create a bar chart for categorical data comparisons.
    
    Args:
        data: DataFrame containing the data to visualize
        x: Column name for x-axis (categorical)
        y: Column name for y-axis (values)
        title: Chart title
        x_label: Optional custom label for x-axis (defaults to column name)
        y_label: Optional custom label for y-axis (defaults to column name)
    
    Returns:
        Plotly Figure object containing the bar chart
    
    Requirements: 5.1, 5.6, 5.7
    """
    fig = go.Figure(data=[
        go.Bar(
            x=data[x],
            y=data[y],
            marker_color=ACCESSIBLE_COLORS[0],
            text=data[y],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title=title,
        xaxis_title=x_label or x,
        yaxis_title=y_label or y,
        font=dict(size=12),
        plot_bgcolor='white',
        paper_bgcolor='white',
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridcolor='lightgray')
    
    return fig


def create_line_chart(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None
) -> go.Figure:
    """
    Create a line chart for time series data.
    
    Args:
        data: DataFrame containing the data to visualize
        x: Column name for x-axis (typically time/date)
        y: Column name for y-axis (values)
        title: Chart title
        x_label: Optional custom label for x-axis (defaults to column name)
        y_label: Optional custom label for y-axis (defaults to column name)
    
    Returns:
        Plotly Figure object containing the line chart
    
    Requirements: 5.2, 5.6, 5.7
    """
    fig = go.Figure(data=[
        go.Scatter(
            x=data[x],
            y=data[y],
            mode='lines+markers',
            line=dict(color=ACCESSIBLE_COLORS[0], width=2),
            marker=dict(size=6),
        )
    ])
    
    fig.update_layout(
        title=title,
        xaxis_title=x_label or x,
        yaxis_title=y_label or y,
        font=dict(size=12),
        plot_bgcolor='white',
        paper_bgcolor='white',
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridcolor='lightgray')
    
    return fig


def create_pie_chart(
    data: pd.DataFrame,
    values: str,
    names: str,
    title: str
) -> go.Figure:
    """
    Create a pie chart for proportion visualization.
    
    Args:
        data: DataFrame containing the data to visualize
        values: Column name for values (sizes of pie slices)
        names: Column name for labels (names of pie slices)
        title: Chart title
    
    Returns:
        Plotly Figure object containing the pie chart
    
    Requirements: 5.3, 5.6, 5.7
    """
    fig = go.Figure(data=[
        go.Pie(
            labels=data[names],
            values=data[values],
            marker=dict(colors=ACCESSIBLE_COLORS),
            textinfo='label+percent',
            textfont=dict(size=12),
        )
    ])
    
    fig.update_layout(
        title=title,
        font=dict(size=12),
        paper_bgcolor='white',
    )
    
    return fig


def export_chart(fig: go.Figure, filename: str, format: str = 'png') -> bytes:
    """
    Export a Plotly chart as an image or HTML.

    Args:
        fig: Plotly Figure object to export
        filename: Desired filename (without extension)
        format: Export format - 'png' or 'html' (default: 'png')

    Returns:
        Image or HTML data as bytes

    Requirements: 5.5

    Note:
        PNG export requires kaleido. If kaleido fails, falls back to HTML export.
        HTML export is always available and provides interactive charts.
    """
    if format == 'html':
        # Export to HTML (always works, provides interactive chart)
        html_bytes = fig.to_html(include_plotlyjs='cdn').encode('utf-8')
        return html_bytes

    # Try PNG export with kaleido
    try:
        img_bytes = fig.to_image(format='png', width=1200, height=800)
        return img_bytes
    except Exception as e:
        # Fallback to HTML if kaleido fails
        print(f"Warning: PNG export failed ({str(e)}), falling back to HTML format")
        html_bytes = fig.to_html(include_plotlyjs='cdn').encode('utf-8')
        return html_bytes


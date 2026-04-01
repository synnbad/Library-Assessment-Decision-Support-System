"""
Unit tests for visualization module

Tests the chart generation and export functions.
"""

import pytest
import pandas as pd
import plotly.graph_objects as go
from modules.visualization import (
    create_bar_chart,
    create_line_chart,
    create_pie_chart,
    export_chart
)


class TestChartGeneration:
    """Test chart generation functions"""
    
    def test_create_bar_chart(self):
        """Test bar chart creation with valid data"""
        data = pd.DataFrame({
            'category': ['A', 'B', 'C'],
            'value': [10, 20, 15]
        })
        
        fig = create_bar_chart(data, 'category', 'value', 'Test Bar Chart')
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == 'Test Bar Chart'
        assert fig.layout.xaxis.title.text == 'category'
        assert fig.layout.yaxis.title.text == 'value'
    
    def test_create_line_chart(self):
        """Test line chart creation with valid data"""
        data = pd.DataFrame({
            'date': ['2024-01', '2024-02', '2024-03'],
            'value': [100, 150, 120]
        })
        
        fig = create_line_chart(data, 'date', 'value', 'Test Line Chart')
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == 'Test Line Chart'
        assert fig.layout.xaxis.title.text == 'date'
        assert fig.layout.yaxis.title.text == 'value'
    
    def test_create_pie_chart(self):
        """Test pie chart creation with valid data"""
        data = pd.DataFrame({
            'category': ['A', 'B', 'C'],
            'value': [30, 50, 20]
        })
        
        fig = create_pie_chart(data, 'value', 'category', 'Test Pie Chart')
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == 'Test Pie Chart'


class TestChartExport:
    """Test chart export functionality"""
    
    def test_export_chart_returns_bytes(self):
        """Test that export_chart returns bytes (PNG or HTML fallback)"""
        # Create a simple chart
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [1, 2, 3]
        })
        fig = create_bar_chart(data, 'x', 'y', 'Test Chart')
        
        # Export (may be PNG or HTML depending on kaleido availability)
        img_bytes = export_chart(fig, 'test_chart')
        
        # Verify it returns bytes
        assert isinstance(img_bytes, bytes)
        assert len(img_bytes) > 0
        
        # Check if it's PNG or HTML
        png_signature = b'\x89PNG\r\n\x1a\n'
        is_png = img_bytes[:8] == png_signature
        
        # Check for HTML content (Plotly HTML starts with <html> or contains plotly)
        try:
            content_str = img_bytes.decode('utf-8', errors='ignore')
            is_html = '<html>' in content_str or 'plotly' in content_str.lower()
        except:
            is_html = False
        
        # Should be either PNG or HTML
        assert is_png or is_html, "Export should produce either PNG or HTML"
    
    def test_export_chart_with_different_chart_types(self):
        """Test export works with different chart types"""
        data = pd.DataFrame({
            'category': ['A', 'B', 'C'],
            'value': [10, 20, 15]
        })
        
        # Test with bar chart
        bar_fig = create_bar_chart(data, 'category', 'value', 'Bar Chart')
        bar_bytes = export_chart(bar_fig, 'bar_chart')
        assert isinstance(bar_bytes, bytes)
        assert len(bar_bytes) > 0
        
        # Test with line chart
        line_fig = create_line_chart(data, 'category', 'value', 'Line Chart')
        line_bytes = export_chart(line_fig, 'line_chart')
        assert isinstance(line_bytes, bytes)
        assert len(line_bytes) > 0
        
        # Test with pie chart
        pie_fig = create_pie_chart(data, 'value', 'category', 'Pie Chart')
        pie_bytes = export_chart(pie_fig, 'pie_chart')
        assert isinstance(pie_bytes, bytes)
        assert len(pie_bytes) > 0
    
    def test_export_chart_html_format(self):
        """Test explicit HTML export"""
        data = pd.DataFrame({
            'x': ['A', 'B', 'C'],
            'y': [1, 2, 3]
        })
        fig = create_bar_chart(data, 'x', 'y', 'Test Chart')
        
        # Export to HTML explicitly
        html_bytes = export_chart(fig, 'test_chart', format='html')
        
        # Verify it returns HTML bytes
        assert isinstance(html_bytes, bytes)
        assert len(html_bytes) > 0
        assert b'<!DOCTYPE html>' in html_bytes or b'<html>' in html_bytes

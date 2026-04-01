"""
Unit tests for report generation error handling.

Tests Requirements 4.4:
- Handle missing visualizations gracefully
- Provide fallback options when PDF export fails
- Display user-friendly error messages
"""

import pytest
import tempfile
import os
from modules.report_generator import create_report, export_report
from modules.database import init_database, execute_update


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Initialize database
    init_database(db_path)
    
    yield db_path
    
    # Cleanup
    os.unlink(db_path)


class TestMissingVisualizationHandling:
    """Test handling of missing or failed visualizations."""
    
    def test_report_generation_continues_when_visualization_fails(self, test_db, monkeypatch):
        """Test that report generation continues even if visualization creation fails."""
        # Insert test dataset
        dataset_id = execute_update(
            """INSERT INTO datasets (name, dataset_type, row_count, column_names)
               VALUES (?, ?, ?, ?)""",
            ('test_viz_fail', 'survey', 2, '["question", "response_text"]'),
            test_db
        )
        
        # Insert survey responses with sentiment
        execute_update(
            """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
               VALUES (?, ?, ?, ?, ?)""",
            (dataset_id, 'Q1', 'Good', 'positive', 0.5),
            test_db
        )
        execute_update(
            """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
               VALUES (?, ?, ?, ?, ?)""",
            (dataset_id, 'Q2', 'Bad', 'negative', -0.5),
            test_db
        )
        
        # Mock visualization functions to raise exceptions
        from modules import visualization
        
        def mock_create_pie_chart(*args, **kwargs):
            raise Exception("Visualization library error")
        
        def mock_create_bar_chart(*args, **kwargs):
            raise Exception("Visualization library error")
        
        monkeypatch.setattr(visualization, 'create_pie_chart', mock_create_pie_chart)
        monkeypatch.setattr(visualization, 'create_bar_chart', mock_create_bar_chart)
        
        # Create report with visualizations enabled
        report = create_report([dataset_id], include_viz=True, db_path=test_db)
        
        # Report should still be generated
        assert report is not None
        assert 'title' in report
        assert 'statistical_summaries' in report
        
        # Visualizations list should be empty or have warnings
        assert 'visualizations' in report
        
        # Should have visualization warnings in metadata
        assert 'visualization_warnings' in report['metadata']
        assert len(report['metadata']['visualization_warnings']) > 0
    
    def test_visualization_warnings_include_dataset_name(self, test_db, monkeypatch):
        """Test that visualization warnings include the dataset name."""
        # Insert test dataset
        dataset_id = execute_update(
            """INSERT INTO datasets (name, dataset_type, row_count, column_names)
               VALUES (?, ?, ?, ?)""",
            ('specific_dataset_name', 'survey', 1, '["question", "response_text"]'),
            test_db
        )
        
        # Insert survey response with sentiment
        execute_update(
            """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
               VALUES (?, ?, ?, ?, ?)""",
            (dataset_id, 'Q1', 'Good', 'positive', 0.5),
            test_db
        )
        
        # Mock visualization to fail
        from modules import visualization
        
        def mock_create_pie_chart(*args, **kwargs):
            raise Exception("Mock error")
        
        monkeypatch.setattr(visualization, 'create_pie_chart', mock_create_pie_chart)
        
        # Create report
        report = create_report([dataset_id], include_viz=True, db_path=test_db)
        
        # Check warnings include dataset name
        assert 'visualization_warnings' in report['metadata']
        warnings = report['metadata']['visualization_warnings']
        assert any('specific_dataset_name' in w for w in warnings)
    
    def test_report_without_visualizations_has_no_warnings(self, test_db):
        """Test that reports without visualizations don't have warnings."""
        # Insert test dataset
        dataset_id = execute_update(
            """INSERT INTO datasets (name, dataset_type, row_count, column_names)
               VALUES (?, ?, ?, ?)""",
            ('test_no_viz', 'survey', 1, '["question", "response_text"]'),
            test_db
        )
        
        execute_update(
            """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
               VALUES (?, ?, ?, ?, ?)""",
            (dataset_id, 'Q1', 'Good', 'positive', 0.5),
            test_db
        )
        
        # Create report without visualizations
        report = create_report([dataset_id], include_viz=False, db_path=test_db)
        
        # Should not have visualization warnings
        assert 'visualization_warnings' not in report['metadata']
    
    def test_partial_visualization_failure(self, test_db, monkeypatch):
        """Test handling when some visualizations succeed and others fail."""
        # Insert test dataset with both sentiment and category data
        dataset_id = execute_update(
            """INSERT INTO datasets (name, dataset_type, row_count, column_names)
               VALUES (?, ?, ?, ?)""",
            ('test_partial', 'usage', 2, '["date", "metric_name", "metric_value"]'),
            test_db
        )
        
        # Insert usage data with categories
        execute_update(
            """INSERT INTO usage_statistics (dataset_id, date, metric_name, metric_value, category)
               VALUES (?, ?, ?, ?, ?)""",
            (dataset_id, '2024-01-01', 'visits', 100, 'library'),
            test_db
        )
        execute_update(
            """INSERT INTO usage_statistics (dataset_id, date, metric_name, metric_value, category)
               VALUES (?, ?, ?, ?, ?)""",
            (dataset_id, '2024-01-02', 'visits', 150, 'online'),
            test_db
        )
        
        # Mock only bar chart to fail
        from modules import visualization
        original_create_bar = visualization.create_bar_chart
        
        def mock_create_bar_chart(*args, **kwargs):
            raise Exception("Bar chart error")
        
        monkeypatch.setattr(visualization, 'create_bar_chart', mock_create_bar_chart)
        
        # Create report
        report = create_report([dataset_id], include_viz=True, db_path=test_db)
        
        # Should have warnings for failed visualizations
        assert 'visualization_warnings' in report['metadata']
        assert len(report['metadata']['visualization_warnings']) > 0
    
    def test_insufficient_data_for_visualization(self, test_db):
        """Test handling when dataset has insufficient data for visualizations."""
        # Insert dataset with no categorical data
        dataset_id = execute_update(
            """INSERT INTO datasets (name, dataset_type, row_count, column_names)
               VALUES (?, ?, ?, ?)""",
            ('test_insufficient', 'survey', 1, '["question", "response_text"]'),
            test_db
        )
        
        # Insert response without sentiment
        execute_update(
            """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
               VALUES (?, ?, ?, ?, ?)""",
            (dataset_id, 'Q1', 'Response', None, None),
            test_db
        )
        
        # Create report with visualizations
        report = create_report([dataset_id], include_viz=True, db_path=test_db)
        
        # Report should be generated without visualizations
        assert report is not None
        assert len(report['visualizations']) == 0


class TestPDFExportFallback:
    """Test PDF export failure handling and Markdown fallback."""
    
    def test_pdf_export_fallback_to_markdown(self, test_db, monkeypatch):
        """Test that PDF export automatically falls back to Markdown on failure."""
        # Insert test dataset
        dataset_id = execute_update(
            """INSERT INTO datasets (name, dataset_type, row_count, column_names)
               VALUES (?, ?, ?, ?)""",
            ('test_pdf_fallback', 'survey', 1, '["question", "response_text"]'),
            test_db
        )
        
        execute_update(
            """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
               VALUES (?, ?, ?, ?, ?)""",
            (dataset_id, 'Q1', 'Good', 'positive', 0.5),
            test_db
        )
        
        # Create report
        report = create_report([dataset_id], include_viz=False, db_path=test_db)
        
        # Mock PDF export to fail
        from modules import report_generator
        
        def mock_export_pdf(report_dict):
            raise Exception("PDF library not available")
        
        monkeypatch.setattr(report_generator, '_export_pdf', mock_export_pdf)
        
        # Try to export as PDF
        content, actual_format = export_report(report, format='pdf')
        
        # Should fallback to Markdown
        assert actual_format == 'markdown'
        assert isinstance(content, bytes)
        
        # Content should be valid Markdown
        markdown_text = content.decode('utf-8')
        assert '# Assessment Report' in markdown_text
    
    def test_markdown_export_always_succeeds(self, test_db):
        """Test that Markdown export always succeeds."""
        # Insert test dataset
        dataset_id = execute_update(
            """INSERT INTO datasets (name, dataset_type, row_count, column_names)
               VALUES (?, ?, ?, ?)""",
            ('test_markdown', 'survey', 1, '["question", "response_text"]'),
            test_db
        )
        
        execute_update(
            """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
               VALUES (?, ?, ?, ?, ?)""",
            (dataset_id, 'Q1', 'Good', 'positive', 0.5),
            test_db
        )
        
        # Create report
        report = create_report([dataset_id], include_viz=False, db_path=test_db)
        
        # Export as Markdown
        content, actual_format = export_report(report, format='markdown')
        
        # Should succeed
        assert actual_format == 'markdown'
        assert isinstance(content, bytes)
        assert len(content) > 0
    
    def test_export_report_returns_format_used(self, test_db):
        """Test that export_report returns the actual format used."""
        # Insert test dataset
        dataset_id = execute_update(
            """INSERT INTO datasets (name, dataset_type, row_count, column_names)
               VALUES (?, ?, ?, ?)""",
            ('test_format_return', 'survey', 1, '["question", "response_text"]'),
            test_db
        )
        
        execute_update(
            """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
               VALUES (?, ?, ?, ?, ?)""",
            (dataset_id, 'Q1', 'Good', 'positive', 0.5),
            test_db
        )
        
        # Create report
        report = create_report([dataset_id], include_viz=False, db_path=test_db)
        
        # Export as Markdown
        content, actual_format = export_report(report, format='markdown')
        assert actual_format == 'markdown'
        
        # Export as PDF (may fallback)
        content, actual_format = export_report(report, format='pdf')
        assert actual_format in ['pdf', 'markdown']
    
    def test_pdf_export_with_reportlab_unavailable(self, test_db, monkeypatch):
        """Test PDF export when reportlab is not installed."""
        # Insert test dataset
        dataset_id = execute_update(
            """INSERT INTO datasets (name, dataset_type, row_count, column_names)
               VALUES (?, ?, ?, ?)""",
            ('test_no_reportlab', 'survey', 1, '["question", "response_text"]'),
            test_db
        )
        
        execute_update(
            """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
               VALUES (?, ?, ?, ?, ?)""",
            (dataset_id, 'Q1', 'Good', 'positive', 0.5),
            test_db
        )
        
        # Create report
        report = create_report([dataset_id], include_viz=False, db_path=test_db)
        
        # Mock _export_pdf to simulate ImportError
        from modules import report_generator
        
        def mock_export_pdf_import_error(report_dict):
            raise ImportError("No module named 'reportlab'")
        
        monkeypatch.setattr(report_generator, '_export_pdf', mock_export_pdf_import_error)
        
        # Try to export as PDF
        content, actual_format = export_report(report, format='pdf')
        
        # Should fallback to Markdown
        assert actual_format == 'markdown'
        markdown_text = content.decode('utf-8')
        assert '# Assessment Report' in markdown_text


class TestVisualizationWarningsInExport:
    """Test that visualization warnings are included in exported reports."""
    
    def test_markdown_export_includes_visualization_warnings(self, test_db, monkeypatch):
        """Test that Markdown export includes visualization warnings."""
        # Insert test dataset
        dataset_id = execute_update(
            """INSERT INTO datasets (name, dataset_type, row_count, column_names)
               VALUES (?, ?, ?, ?)""",
            ('test_warnings_export', 'survey', 1, '["question", "response_text"]'),
            test_db
        )
        
        execute_update(
            """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
               VALUES (?, ?, ?, ?, ?)""",
            (dataset_id, 'Q1', 'Good', 'positive', 0.5),
            test_db
        )
        
        # Mock visualization to fail
        from modules import visualization
        
        def mock_create_pie_chart(*args, **kwargs):
            raise Exception("Mock error")
        
        monkeypatch.setattr(visualization, 'create_pie_chart', mock_create_pie_chart)
        
        # Create report with visualizations
        report = create_report([dataset_id], include_viz=True, db_path=test_db)
        
        # Export to Markdown
        content, _ = export_report(report, format='markdown')
        markdown_text = content.decode('utf-8')
        
        # Should include warnings section
        assert 'Visualization Warnings' in markdown_text
        assert 'insufficient data' in markdown_text
        assert 'test_warnings_export' in markdown_text
    
    def test_markdown_export_without_warnings_has_no_section(self, test_db):
        """Test that Markdown export without warnings doesn't have warnings section."""
        # Insert test dataset
        dataset_id = execute_update(
            """INSERT INTO datasets (name, dataset_type, row_count, column_names)
               VALUES (?, ?, ?, ?)""",
            ('test_no_warnings', 'survey', 1, '["question", "response_text"]'),
            test_db
        )
        
        execute_update(
            """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
               VALUES (?, ?, ?, ?, ?)""",
            (dataset_id, 'Q1', 'Good', 'positive', 0.5),
            test_db
        )
        
        # Create report without visualizations
        report = create_report([dataset_id], include_viz=False, db_path=test_db)
        
        # Export to Markdown
        content, _ = export_report(report, format='markdown')
        markdown_text = content.decode('utf-8')
        
        # Should not include warnings section
        assert 'Visualization Warnings' not in markdown_text


class TestErrorMessageQuality:
    """Test that error messages are user-friendly and actionable."""
    
    def test_visualization_warning_messages_are_clear(self, test_db, monkeypatch):
        """Test that visualization warning messages are user-friendly."""
        # Insert test dataset
        dataset_id = execute_update(
            """INSERT INTO datasets (name, dataset_type, row_count, column_names)
               VALUES (?, ?, ?, ?)""",
            ('test_clear_messages', 'survey', 1, '["question", "response_text"]'),
            test_db
        )
        
        execute_update(
            """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
               VALUES (?, ?, ?, ?, ?)""",
            (dataset_id, 'Q1', 'Good', 'positive', 0.5),
            test_db
        )
        
        # Mock visualization to fail
        from modules import visualization
        
        def mock_create_pie_chart(*args, **kwargs):
            raise Exception("Technical error: NoneType object has no attribute 'values'")
        
        monkeypatch.setattr(visualization, 'create_pie_chart', mock_create_pie_chart)
        
        # Create report
        report = create_report([dataset_id], include_viz=True, db_path=test_db)
        
        # Check warning messages
        warnings = report['metadata'].get('visualization_warnings', [])
        assert len(warnings) > 0
        
        # Messages should be user-friendly
        for warning in warnings:
            # Should not contain technical jargon
            assert 'NoneType' not in warning
            assert 'Exception' not in warning
            assert 'Traceback' not in warning
            
            # Should mention insufficient data
            assert 'insufficient data' in warning.lower()
    
    def test_invalid_export_format_error_is_clear(self, test_db):
        """Test that invalid format error is clear."""
        # Insert test dataset
        dataset_id = execute_update(
            """INSERT INTO datasets (name, dataset_type, row_count, column_names)
               VALUES (?, ?, ?, ?)""",
            ('test_invalid_format', 'survey', 1, '["question", "response_text"]'),
            test_db
        )
        
        # Create report
        report = create_report([dataset_id], include_viz=False, db_path=test_db)
        
        # Try invalid format
        with pytest.raises(ValueError) as exc_info:
            export_report(report, format='invalid')
        
        # Error message should be clear
        error_msg = str(exc_info.value)
        assert 'invalid' in error_msg.lower()
        assert 'pdf' in error_msg.lower()
        assert 'markdown' in error_msg.lower()


class TestReportGenerationRobustness:
    """Test that report generation is robust to various error conditions."""
    
    def test_report_generation_with_all_visualizations_failing(self, test_db, monkeypatch):
        """Test report generation when all visualizations fail."""
        # Insert test dataset
        dataset_id = execute_update(
            """INSERT INTO datasets (name, dataset_type, row_count, column_names)
               VALUES (?, ?, ?, ?)""",
            ('test_all_viz_fail', 'survey', 2, '["question", "response_text"]'),
            test_db
        )
        
        execute_update(
            """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
               VALUES (?, ?, ?, ?, ?)""",
            (dataset_id, 'Q1', 'Good', 'positive', 0.5),
            test_db
        )
        execute_update(
            """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
               VALUES (?, ?, ?, ?, ?)""",
            (dataset_id, 'Q2', 'Bad', 'negative', -0.5),
            test_db
        )
        
        # Mock all visualization functions to fail
        from modules import visualization
        
        def mock_fail(*args, **kwargs):
            raise Exception("All visualizations fail")
        
        monkeypatch.setattr(visualization, 'create_pie_chart', mock_fail)
        monkeypatch.setattr(visualization, 'create_bar_chart', mock_fail)
        monkeypatch.setattr(visualization, 'create_line_chart', mock_fail)
        
        # Create report
        report = create_report([dataset_id], include_viz=True, db_path=test_db)
        
        # Report should still be complete
        assert report is not None
        assert 'title' in report
        assert 'statistical_summaries' in report
        assert len(report['statistical_summaries']) > 0
        
        # Should have warnings
        assert 'visualization_warnings' in report['metadata']
        
        # Should be exportable
        content, format_used = export_report(report, format='markdown')
        assert len(content) > 0
    
    def test_report_export_with_missing_metadata_fields(self, test_db):
        """Test that report export handles missing metadata fields gracefully."""
        # Insert test dataset
        dataset_id = execute_update(
            """INSERT INTO datasets (name, dataset_type, row_count, column_names)
               VALUES (?, ?, ?, ?)""",
            ('test_missing_meta', 'survey', 1, '["question", "response_text"]'),
            test_db
        )
        
        execute_update(
            """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
               VALUES (?, ?, ?, ?, ?)""",
            (dataset_id, 'Q1', 'Good', 'positive', 0.5),
            test_db
        )
        
        # Create report
        report = create_report([dataset_id], include_viz=False, db_path=test_db)
        
        # Remove some metadata fields
        if 'visualization_warnings' in report['metadata']:
            del report['metadata']['visualization_warnings']
        
        # Should still export successfully
        content, format_used = export_report(report, format='markdown')
        assert len(content) > 0
        
        markdown_text = content.decode('utf-8')
        assert '# Assessment Report' in markdown_text

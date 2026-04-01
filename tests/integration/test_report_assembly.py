"""
Integration test for report assembly and export functions.
Tests Requirements 4.3, 4.4, 4.5, 4.7
"""

import pytest
import tempfile
import os
import json
from modules.report_generator import create_report, export_report
from modules.database import init_database, execute_update


@pytest.fixture
def test_db():
    """Create a temporary test database with sample data."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Initialize database
    init_database(db_path)
    
    # Insert test dataset
    dataset_id = execute_update(
        """INSERT INTO datasets (name, dataset_type, row_count, column_names)
           VALUES (?, ?, ?, ?)""",
        ('Integration Test Survey', 'survey', 3, '["question", "response_text"]'),
        db_path
    )
    
    # Insert survey responses with sentiment
    execute_update(
        """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, 'How satisfied?', 'Very satisfied with the library', 'positive', 0.8),
        db_path
    )
    execute_update(
        """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, 'How satisfied?', 'Neutral experience', 'neutral', 0.1),
        db_path
    )
    execute_update(
        """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, 'How satisfied?', 'Not satisfied at all', 'negative', -0.6),
        db_path
    )
    
    # Insert themes for qualitative analysis
    execute_update(
        """INSERT INTO themes (dataset_id, theme_name, keywords, frequency, representative_quotes)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, 'Theme 1: Satisfaction', 
         json.dumps(['satisfied', 'experience']), 
         3, 
         json.dumps(['Very satisfied with the library', 'Neutral experience', 'Not satisfied at all'])),
        db_path
    )
    
    yield db_path, dataset_id
    
    # Cleanup
    os.unlink(db_path)


def test_report_assembly_complete_structure(test_db):
    """
    Test that create_report() assembles complete report structure.
    Requirement 4.3, 4.5, 4.7
    """
    db_path, dataset_id = test_db
    
    # Create report with all features
    report = create_report(
        [dataset_id], 
        include_viz=True, 
        include_qualitative=True,
        db_path=db_path
    )
    
    # Verify all required components are present
    assert 'title' in report, "Report must include title"
    assert 'metadata' in report, "Report must include metadata"
    assert 'executive_summary' in report, "Report must include executive summary"
    assert 'statistical_summaries' in report, "Report must include statistical summaries"
    assert 'visualizations' in report, "Report must include visualizations"
    assert 'qualitative_analysis' in report, "Report must include qualitative analysis"
    assert 'theme_summaries' in report, "Report must include theme summaries"
    assert 'citations' in report, "Report must include citations"
    assert 'timestamp' in report, "Report must include timestamp"
    
    # Verify metadata structure
    assert 'generated_at' in report['metadata']
    assert 'author' in report['metadata']
    assert 'datasets' in report['metadata']
    assert 'dataset_ids' in report['metadata']
    
    # Verify title is meaningful
    assert 'Integration Test Survey' in report['title']
    
    # Verify executive summary is generated
    assert isinstance(report['executive_summary'], str)
    assert len(report['executive_summary']) > 0
    
    # Verify statistical summaries
    assert len(report['statistical_summaries']) == 1
    assert report['statistical_summaries'][0]['dataset_name'] == 'Integration Test Survey'
    
    # Requirement 4.3: Verify visualizations are included
    assert len(report['visualizations']) > 0, "Report must include data visualizations (Req 4.3)"
    for viz in report['visualizations']:
        assert 'type' in viz
        assert 'title' in viz
        assert 'figure' in viz
    
    # Requirement 4.7: Verify theme summaries when qualitative analysis performed
    assert report['qualitative_analysis'] is not None, "Qualitative analysis should be included"
    assert len(report['theme_summaries']) > 0, "Report must include theme summaries when qualitative analysis performed (Req 4.7)"
    assert report['theme_summaries'][0]['name'] == 'Theme 1: Satisfaction'
    assert 'keywords' in report['theme_summaries'][0]
    assert 'quotes' in report['theme_summaries'][0]
    
    # Requirement 4.5: Verify citations for all data sources
    assert len(report['citations']) > 0, "Report must include citations for all data sources (Req 4.5)"
    assert 'Integration Test Survey' in report['citations'][0]
    assert 'ID:' in report['citations'][0]
    assert 'Type:' in report['citations'][0]
    assert 'Records:' in report['citations'][0]


def test_export_report_markdown_format(test_db):
    """
    Test that export_report() exports to Markdown format.
    Requirement 4.4
    """
    db_path, dataset_id = test_db
    
    # Create report
    report = create_report([dataset_id], include_viz=False, db_path=db_path)
    
    # Export to Markdown
    markdown_bytes, actual_format = export_report(report, format='markdown')
    
    # Verify output is bytes and format is correct
    assert isinstance(markdown_bytes, bytes), "Export must return bytes"
    assert actual_format == 'markdown', "Format should be markdown"
    
    # Decode and verify content
    markdown_text = markdown_bytes.decode('utf-8')
    
    # Verify Markdown structure
    assert '# Assessment Report' in markdown_text, "Markdown must have title header"
    assert '## Report Metadata' in markdown_text, "Markdown must have metadata section"
    assert '## Executive Summary' in markdown_text, "Markdown must have executive summary"
    assert '## Statistical Summaries' in markdown_text, "Markdown must have statistics section"
    assert '## Data Sources' in markdown_text, "Markdown must have citations section"
    
    # Verify content is present
    assert 'Integration Test Survey' in markdown_text
    assert 'survey' in markdown_text


def test_export_report_pdf_format(test_db):
    """
    Test that export_report() exports to PDF format.
    Requirement 4.4
    """
    db_path, dataset_id = test_db
    
    # Create report
    report = create_report([dataset_id], include_viz=False, db_path=db_path)
    
    # Export to PDF
    pdf_bytes, actual_format = export_report(report, format='pdf')
    
    # Verify output is bytes
    assert isinstance(pdf_bytes, bytes), "Export must return bytes"
    assert len(pdf_bytes) > 0, "PDF export must produce content"
    assert actual_format in ['pdf', 'markdown'], "Format should be pdf or markdown (fallback)"
    
    # PDF should start with %PDF header (if reportlab is available)
    # or fall back to Markdown
    assert pdf_bytes.startswith(b'%PDF') or b'# Assessment Report' in pdf_bytes


def test_report_with_multiple_datasets(test_db):
    """
    Test report creation with multiple datasets includes all citations.
    Requirement 4.5
    """
    db_path, dataset_id1 = test_db
    
    # Insert second dataset
    dataset_id2 = execute_update(
        """INSERT INTO datasets (name, dataset_type, row_count, column_names)
           VALUES (?, ?, ?, ?)""",
        ('Second Survey', 'survey', 1, '["question", "response_text"]'),
        db_path
    )
    execute_update(
        """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id2, 'Q1', 'Good', 'positive', 0.5),
        db_path
    )
    
    # Create report with both datasets
    report = create_report([dataset_id1, dataset_id2], include_viz=False, db_path=db_path)
    
    # Verify citations for all data sources (Requirement 4.5)
    assert len(report['citations']) == 2, "Must have citations for all datasets"
    assert any('Integration Test Survey' in c for c in report['citations'])
    assert any('Second Survey' in c for c in report['citations'])
    
    # Verify both datasets in metadata
    assert len(report['metadata']['datasets']) == 2
    assert 'Integration Test Survey' in report['metadata']['datasets']
    assert 'Second Survey' in report['metadata']['datasets']


def test_theme_summaries_only_when_qualitative_analysis(test_db):
    """
    Test that theme summaries are only included when qualitative analysis is performed.
    Requirement 4.7
    """
    db_path, dataset_id = test_db
    
    # Create report WITHOUT qualitative analysis
    report_no_qual = create_report(
        [dataset_id], 
        include_viz=False, 
        include_qualitative=False,
        db_path=db_path
    )
    
    # Verify no theme summaries when qualitative analysis not performed
    assert report_no_qual['qualitative_analysis'] is None
    assert len(report_no_qual['theme_summaries']) == 0
    
    # Create report WITH qualitative analysis
    report_with_qual = create_report(
        [dataset_id], 
        include_viz=False, 
        include_qualitative=True,
        db_path=db_path
    )
    
    # Verify theme summaries included when qualitative analysis performed (Req 4.7)
    assert report_with_qual['qualitative_analysis'] is not None
    assert len(report_with_qual['theme_summaries']) > 0
    assert 'name' in report_with_qual['theme_summaries'][0]
    assert 'keywords' in report_with_qual['theme_summaries'][0]
    assert 'quotes' in report_with_qual['theme_summaries'][0]


def test_markdown_export_includes_all_sections(test_db):
    """
    Test that Markdown export includes all report sections.
    Requirements 4.3, 4.5, 4.7
    """
    db_path, dataset_id = test_db
    
    # Create comprehensive report
    report = create_report(
        [dataset_id], 
        include_viz=True, 
        include_qualitative=True,
        db_path=db_path
    )
    
    # Export to Markdown
    markdown_bytes, actual_format = export_report(report, format='markdown')
    markdown_text = markdown_bytes.decode('utf-8')
    
    # Verify all sections present
    assert '## Report Metadata' in markdown_text
    assert '## Executive Summary' in markdown_text
    assert '## Statistical Summaries' in markdown_text
    
    # Requirement 4.3: Visualizations section
    assert '## Visualizations' in markdown_text
    assert 'visualization(s) included' in markdown_text
    
    # Requirement 4.7: Theme summaries section
    assert '## Identified Themes' in markdown_text
    assert 'Theme 1: Satisfaction' in markdown_text
    
    # Requirement 4.5: Data sources section
    assert '## Data Sources' in markdown_text
    assert 'Integration Test Survey' in markdown_text

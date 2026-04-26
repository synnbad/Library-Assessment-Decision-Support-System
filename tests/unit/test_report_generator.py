"""
Unit tests for report generator module.
"""

import pytest
import tempfile
import os
from modules.report_generator import generate_statistical_summary
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


def test_generate_statistical_summary_survey_dataset(test_db):
    """Test statistical summary generation for survey dataset."""
    # Insert test dataset
    dataset_id = execute_update(
        """INSERT INTO datasets (name, dataset_type, row_count, column_names)
           VALUES (?, ?, ?, ?)""",
        ('test_survey', 'survey', 3, '["question", "response_text"]'),
        test_db
    )
    
    # Insert test survey responses
    execute_update(
        """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, 'How satisfied are you?', 'Very satisfied', 'positive', 0.8),
        test_db
    )
    execute_update(
        """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, 'How satisfied are you?', 'Somewhat satisfied', 'neutral', 0.2),
        test_db
    )
    execute_update(
        """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, 'How satisfied are you?', 'Not satisfied', 'negative', -0.5),
        test_db
    )
    
    # Generate statistical summary
    summary = generate_statistical_summary(dataset_id, test_db)
    
    # Verify basic metadata
    assert summary['dataset_id'] == dataset_id
    assert summary['dataset_name'] == 'test_survey'
    assert summary['dataset_type'] == 'survey'
    assert summary['row_count'] == 3
    
    # Verify sentiment score statistics
    assert 'sentiment_score' in summary['statistics']
    stats = summary['statistics']['sentiment_score']
    assert stats['count'] == 3
    assert stats['mean'] == pytest.approx(0.1667, rel=0.01)
    assert stats['median'] == 0.2
    assert stats['min'] == -0.5
    assert stats['max'] == 0.8
    assert stats['std_dev'] > 0
    
    # Verify categorical counts
    assert 'sentiment' in summary['categorical_counts']
    sentiment_counts = summary['categorical_counts']['sentiment']
    assert sentiment_counts['positive'] == 1
    assert sentiment_counts['neutral'] == 1
    assert sentiment_counts['negative'] == 1


def test_generate_statistical_summary_usage_dataset(test_db):
    """Test statistical summary generation for usage dataset."""
    # Insert test dataset
    dataset_id = execute_update(
        """INSERT INTO datasets (name, dataset_type, row_count, column_names)
           VALUES (?, ?, ?, ?)""",
        ('test_usage', 'usage', 4, '["date", "metric_name", "metric_value"]'),
        test_db
    )
    
    # Insert test usage statistics
    execute_update(
        """INSERT INTO usage_statistics (dataset_id, date, metric_name, metric_value, category)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, '2024-01-01', 'visits', 100, 'library'),
        test_db
    )
    execute_update(
        """INSERT INTO usage_statistics (dataset_id, date, metric_name, metric_value, category)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, '2024-01-02', 'visits', 150, 'library'),
        test_db
    )
    execute_update(
        """INSERT INTO usage_statistics (dataset_id, date, metric_name, metric_value, category)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, '2024-01-03', 'checkouts', 50, 'circulation'),
        test_db
    )
    execute_update(
        """INSERT INTO usage_statistics (dataset_id, date, metric_name, metric_value, category)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, '2024-01-04', 'checkouts', 75, 'circulation'),
        test_db
    )
    
    # Generate statistical summary
    summary = generate_statistical_summary(dataset_id, test_db)
    
    # Verify basic metadata
    assert summary['dataset_id'] == dataset_id
    assert summary['dataset_name'] == 'test_usage'
    assert summary['dataset_type'] == 'usage'
    assert summary['row_count'] == 4
    
    # Verify visits statistics
    assert 'visits' in summary['statistics']
    visits_stats = summary['statistics']['visits']
    assert visits_stats['count'] == 2
    assert visits_stats['mean'] == 125.0
    assert visits_stats['median'] == 125.0
    assert visits_stats['min'] == 100
    assert visits_stats['max'] == 150
    
    # Verify checkouts statistics
    assert 'checkouts' in summary['statistics']
    checkouts_stats = summary['statistics']['checkouts']
    assert checkouts_stats['count'] == 2
    assert checkouts_stats['mean'] == 62.5
    assert checkouts_stats['median'] == 62.5
    assert checkouts_stats['min'] == 50
    assert checkouts_stats['max'] == 75
    
    # Verify category counts
    assert 'category' in summary['categorical_counts']
    category_counts = summary['categorical_counts']['category']
    assert category_counts['library'] == 2
    assert category_counts['circulation'] == 2


def test_generate_statistical_summary_nonexistent_dataset(test_db):
    """Test that ValueError is raised for nonexistent dataset."""
    with pytest.raises(ValueError, match="Dataset with id 999 not found"):
        generate_statistical_summary(999, test_db)


def test_generate_statistical_summary_empty_dataset(test_db):
    """Test statistical summary for dataset with no data."""
    # Insert test dataset with no associated data
    dataset_id = execute_update(
        """INSERT INTO datasets (name, dataset_type, row_count, column_names)
           VALUES (?, ?, ?, ?)""",
        ('empty_survey', 'survey', 0, '["question", "response_text"]'),
        test_db
    )
    
    # Generate statistical summary
    summary = generate_statistical_summary(dataset_id, test_db)
    
    # Verify basic metadata
    assert summary['dataset_id'] == dataset_id
    assert summary['dataset_name'] == 'empty_survey'
    assert summary['dataset_type'] == 'survey'
    assert summary['row_count'] == 0
    
    # Verify no statistics are calculated for empty dataset
    assert len(summary['statistics']) == 0
    assert len(summary['categorical_counts']) == 0


def test_create_report_includes_pinned_insights(monkeypatch, test_db):
    """Pinned query insights should be included in report structure and markdown export."""
    from modules import report_generator

    dataset_id = execute_update(
        """INSERT INTO datasets (name, dataset_type, row_count, column_names)
           VALUES (?, ?, ?, ?)""",
        ('test_usage', 'usage', 1, '["date", "metric_name", "metric_value"]'),
        test_db
    )
    execute_update(
        """INSERT INTO usage_statistics (dataset_id, date, metric_name, metric_value, category)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, '2024-01-01', 'visits', 100, 'library'),
        test_db
    )
    monkeypatch.setattr(
        report_generator,
        "generate_narrative",
        lambda summary, analysis=None: "Generated summary.",
    )

    report = report_generator.create_report(
        [dataset_id],
        include_viz=False,
        pinned_insights=[
            {
                "question": "What should the report emphasize?",
                "answer": "Visits are a major signal.",
            }
        ],
        db_path=test_db,
    )
    markdown, actual_format = report_generator.export_report(report, format="markdown")
    markdown_text = markdown.decode("utf-8")

    assert actual_format == "markdown"
    assert report["pinned_insights"][0]["question"] == "What should the report emphasize?"
    assert "Pinned Query Insights" in markdown_text
    assert "Visits are a major signal." in markdown_text


def test_create_report_redacts_pii_from_pinned_insights(monkeypatch, test_db):
    """Pinned insights should not leak PII into generated reports."""
    from modules import report_generator

    dataset_id = execute_update(
        """INSERT INTO datasets (name, dataset_type, row_count, column_names)
           VALUES (?, ?, ?, ?)""",
        ('test_usage', 'usage', 1, '["date", "metric_name", "metric_value"]'),
        test_db
    )
    execute_update(
        """INSERT INTO usage_statistics (dataset_id, date, metric_name, metric_value, category)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, '2024-01-01', 'visits', 100, 'library'),
        test_db
    )
    monkeypatch.setattr(
        report_generator,
        "generate_narrative",
        lambda summary, analysis=None: "Generated summary.",
    )

    report = report_generator.create_report(
        [dataset_id],
        include_viz=False,
        pinned_insights=[
            {
                "question": "Who responded?",
                "answer": "Contact jane.doe@example.com or 555-123-4567.",
            }
        ],
        db_path=test_db,
    )
    markdown, _ = report_generator.export_report(report, format="markdown")
    markdown_text = markdown.decode("utf-8")

    assert "jane.doe@example.com" not in markdown_text
    assert "555-123-4567" not in markdown_text
    assert "[EMAIL]" in markdown_text
    assert "[PHONE]" in markdown_text



def test_generate_narrative_with_summary_only(monkeypatch):
    """Test narrative generation with statistical summary only."""
    from modules.report_generator import generate_narrative
    
    # Mock ollama.generate
    def mock_generate(model, prompt):
        return {
            'response': 'This is a test narrative about the survey data. The analysis shows positive trends.'
        }
    
    import ollama
    monkeypatch.setattr(ollama, 'generate', mock_generate)
    
    # Create test summary
    summary = {
        'dataset_id': 1,
        'dataset_name': 'test_survey',
        'dataset_type': 'survey',
        'row_count': 100,
        'statistics': {
            'sentiment_score': {
                'mean': 0.5,
                'median': 0.6,
                'std_dev': 0.2,
                'count': 100,
                'min': -0.5,
                'max': 1.0
            }
        },
        'categorical_counts': {
            'sentiment': {
                'positive': 60,
                'neutral': 30,
                'negative': 10
            }
        }
    }
    
    # Generate narrative
    narrative = generate_narrative(summary)
    
    # Verify narrative is returned
    assert isinstance(narrative, str)
    assert len(narrative) > 0
    assert 'test narrative' in narrative.lower()


def test_generate_narrative_with_analysis(monkeypatch):
    """Test narrative generation with both summary and qualitative analysis."""
    from modules.report_generator import generate_narrative
    
    # Mock ollama.generate
    def mock_generate(model, prompt):
        # Verify prompt includes both summary and analysis
        assert 'Statistical Summary' in prompt
        assert 'Qualitative Analysis' in prompt
        return {
            'response': 'Comprehensive narrative including themes and sentiment analysis.'
        }
    
    import ollama
    monkeypatch.setattr(ollama, 'generate', mock_generate)
    
    # Create test summary
    summary = {
        'dataset_id': 1,
        'dataset_name': 'test_survey',
        'dataset_type': 'survey',
        'row_count': 100,
        'statistics': {
            'sentiment_score': {
                'mean': 0.5,
                'median': 0.6,
                'std_dev': 0.2,
                'count': 100
            }
        },
        'categorical_counts': {}
    }
    
    # Create test analysis
    analysis = {
        'sentiment_distribution': {
            'positive': 60,
            'neutral': 30,
            'negative': 10
        },
        'themes': [
            {
                'name': 'Customer Service',
                'frequency': 45,
                'keywords': ['helpful', 'friendly', 'staff']
            },
            {
                'name': 'Facilities',
                'frequency': 30,
                'keywords': ['clean', 'space', 'comfortable']
            }
        ]
    }
    
    # Generate narrative
    narrative = generate_narrative(summary, analysis)
    
    # Verify narrative is returned
    assert isinstance(narrative, str)
    assert len(narrative) > 0
    assert 'comprehensive' in narrative.lower()


def test_generate_narrative_ollama_failure(monkeypatch):
    """Test that RuntimeError is raised when Ollama fails."""
    from modules.report_generator import generate_narrative
    
    # Mock ollama.generate to raise exception
    def mock_generate(model, prompt):
        raise Exception("Connection refused")
    
    import ollama
    monkeypatch.setattr(ollama, 'generate', mock_generate)
    
    # Create minimal summary
    summary = {
        'dataset_id': 1,
        'dataset_name': 'test',
        'dataset_type': 'survey',
        'row_count': 10,
        'statistics': {},
        'categorical_counts': {}
    }
    
    # Verify RuntimeError is raised
    with pytest.raises(RuntimeError, match="Failed to generate narrative using Ollama"):
        generate_narrative(summary)


def test_generate_narrative_uses_correct_model(monkeypatch):
    """Test that generate_narrative uses the configured Ollama model."""
    from modules.report_generator import generate_narrative
    from config.settings import Settings
    
    # Track which model was used
    used_model = None
    
    def mock_generate(model, prompt):
        nonlocal used_model
        used_model = model
        return {'response': 'Test narrative'}
    
    import ollama
    monkeypatch.setattr(ollama, 'generate', mock_generate)
    
    # Create minimal summary
    summary = {
        'dataset_id': 1,
        'dataset_name': 'test',
        'dataset_type': 'survey',
        'row_count': 10,
        'statistics': {},
        'categorical_counts': {}
    }
    
    # Generate narrative
    generate_narrative(summary)
    
    # Verify correct model was used
    assert used_model == Settings.OLLAMA_MODEL


def test_generate_narrative_empty_summary(monkeypatch):
    """Test narrative generation with minimal/empty summary data."""
    from modules.report_generator import generate_narrative
    
    # Mock ollama.generate
    def mock_generate(model, prompt):
        return {'response': 'Minimal data narrative.'}
    
    import ollama
    monkeypatch.setattr(ollama, 'generate', mock_generate)
    
    # Create minimal summary with no statistics
    summary = {
        'dataset_id': 1,
        'dataset_name': 'empty_dataset',
        'dataset_type': 'survey',
        'row_count': 0,
        'statistics': {},
        'categorical_counts': {}
    }
    
    # Generate narrative
    narrative = generate_narrative(summary)
    
    # Verify narrative is still generated
    assert isinstance(narrative, str)
    assert len(narrative) > 0



def test_create_report_single_dataset(test_db):
    """Test report creation with a single dataset."""
    from modules.report_generator import create_report
    
    # Insert test dataset
    dataset_id = execute_update(
        """INSERT INTO datasets (name, dataset_type, row_count, column_names)
           VALUES (?, ?, ?, ?)""",
        ('test_survey', 'survey', 2, '["question", "response_text"]'),
        test_db
    )
    
    # Insert test survey responses
    execute_update(
        """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, 'How satisfied?', 'Very satisfied', 'positive', 0.8),
        test_db
    )
    execute_update(
        """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, 'How satisfied?', 'Not satisfied', 'negative', -0.5),
        test_db
    )
    
    # Create report without visualizations to avoid dependencies
    report = create_report([dataset_id], include_viz=False, db_path=test_db)
    
    # Verify report structure
    assert 'title' in report
    assert 'metadata' in report
    assert 'executive_summary' in report
    assert 'statistical_summaries' in report
    assert 'visualizations' in report
    assert 'qualitative_analysis' in report
    assert 'theme_summaries' in report
    assert 'citations' in report
    assert 'timestamp' in report
    
    # Verify metadata
    assert report['metadata']['datasets'] == ['test_survey']
    assert report['metadata']['dataset_ids'] == [dataset_id]
    assert 'generated_at' in report['metadata']
    assert 'author' in report['metadata']
    
    # Verify statistical summaries
    assert len(report['statistical_summaries']) == 1
    assert report['statistical_summaries'][0]['dataset_name'] == 'test_survey'
    
    # Verify citations
    assert len(report['citations']) == 1
    assert 'test_survey' in report['citations'][0]
    
    # Verify title
    assert 'test_survey' in report['title']


def test_create_report_multiple_datasets(test_db):
    """Test report creation with multiple datasets."""
    from modules.report_generator import create_report
    
    # Insert first dataset
    dataset_id1 = execute_update(
        """INSERT INTO datasets (name, dataset_type, row_count, column_names)
           VALUES (?, ?, ?, ?)""",
        ('survey_1', 'survey', 1, '["question", "response_text"]'),
        test_db
    )
    execute_update(
        """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id1, 'Q1', 'Good', 'positive', 0.5),
        test_db
    )
    
    # Insert second dataset
    dataset_id2 = execute_update(
        """INSERT INTO datasets (name, dataset_type, row_count, column_names)
           VALUES (?, ?, ?, ?)""",
        ('survey_2', 'survey', 1, '["question", "response_text"]'),
        test_db
    )
    execute_update(
        """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id2, 'Q2', 'Bad', 'negative', -0.5),
        test_db
    )
    
    # Create report
    report = create_report([dataset_id1, dataset_id2], include_viz=False, db_path=test_db)
    
    # Verify multiple datasets
    assert len(report['metadata']['datasets']) == 2
    assert 'survey_1' in report['metadata']['datasets']
    assert 'survey_2' in report['metadata']['datasets']
    
    # Verify multiple summaries
    assert len(report['statistical_summaries']) == 2
    
    # Verify multiple citations
    assert len(report['citations']) == 2


def test_create_report_with_themes(test_db):
    """Test report creation with qualitative analysis and themes."""
    from modules.report_generator import create_report
    import json
    
    # Insert test dataset
    dataset_id = execute_update(
        """INSERT INTO datasets (name, dataset_type, row_count, column_names)
           VALUES (?, ?, ?, ?)""",
        ('survey_with_themes', 'survey', 2, '["question", "response_text"]'),
        test_db
    )
    
    # Insert survey responses
    execute_update(
        """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, 'Q1', 'Great service', 'positive', 0.8),
        test_db
    )
    execute_update(
        """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, 'Q2', 'Poor service', 'negative', -0.5),
        test_db
    )
    
    # Insert themes
    execute_update(
        """INSERT INTO themes (dataset_id, theme_name, keywords, frequency, representative_quotes)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, 'Theme 1: service', json.dumps(['service', 'staff']), 2, json.dumps(['Great service', 'Poor service'])),
        test_db
    )
    
    # Create report with qualitative analysis
    report = create_report([dataset_id], include_viz=False, include_qualitative=True, db_path=test_db)
    
    # Verify qualitative analysis is included
    assert report['qualitative_analysis'] is not None
    assert 'sentiment_distribution' in report['qualitative_analysis']
    assert 'themes' in report['qualitative_analysis']
    
    # Verify theme summaries
    assert len(report['theme_summaries']) > 0
    assert report['theme_summaries'][0]['name'] == 'Theme 1: service'
    assert report['theme_summaries'][0]['frequency'] == 2


def test_create_report_empty_dataset_list(test_db):
    """Test that ValueError is raised for empty dataset list."""
    from modules.report_generator import create_report
    
    with pytest.raises(ValueError, match="At least one dataset_id must be provided"):
        create_report([], db_path=test_db)


def test_create_report_invalid_dataset_id(test_db):
    """Test that ValueError is raised for invalid dataset ID."""
    from modules.report_generator import create_report
    
    with pytest.raises(ValueError, match="Invalid dataset_id 999"):
        create_report([999], db_path=test_db)


def test_export_report_markdown(test_db):
    """Test report export to Markdown format."""
    from modules.report_generator import create_report, export_report
    
    # Insert test dataset
    dataset_id = execute_update(
        """INSERT INTO datasets (name, dataset_type, row_count, column_names)
           VALUES (?, ?, ?, ?)""",
        ('test_export', 'survey', 1, '["question", "response_text"]'),
        test_db
    )
    execute_update(
        """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, 'Q1', 'Good', 'positive', 0.5),
        test_db
    )
    
    # Create and export report
    report = create_report([dataset_id], include_viz=False, db_path=test_db)
    markdown_bytes, actual_format = export_report(report, format='markdown')
    
    # Verify output
    assert isinstance(markdown_bytes, bytes)
    assert actual_format == 'markdown'
    markdown_text = markdown_bytes.decode('utf-8')
    
    # Verify markdown content
    assert '# Assessment Report' in markdown_text
    assert '## Report Metadata' in markdown_text
    assert '## Executive Summary' in markdown_text
    assert '## Statistical Summaries' in markdown_text
    assert '## Data Sources' in markdown_text
    assert 'test_export' in markdown_text


def test_export_report_pdf(test_db):
    """Test report export to PDF format."""
    from modules.report_generator import create_report, export_report
    
    # Insert test dataset
    dataset_id = execute_update(
        """INSERT INTO datasets (name, dataset_type, row_count, column_names)
           VALUES (?, ?, ?, ?)""",
        ('test_pdf', 'survey', 1, '["question", "response_text"]'),
        test_db
    )
    execute_update(
        """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, 'Q1', 'Good', 'positive', 0.5),
        test_db
    )
    
    # Create and export report
    report = create_report([dataset_id], include_viz=False, db_path=test_db)
    pdf_bytes, actual_format = export_report(report, format='pdf')
    
    # Verify output
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert actual_format in ['pdf', 'markdown']
    
    # PDF should start with %PDF header or be markdown fallback
    assert pdf_bytes.startswith(b'%PDF') or b'# Assessment Report' in pdf_bytes


def test_export_report_invalid_format(test_db):
    """Test that ValueError is raised for invalid export format."""
    from modules.report_generator import create_report, export_report
    
    # Insert test dataset
    dataset_id = execute_update(
        """INSERT INTO datasets (name, dataset_type, row_count, column_names)
           VALUES (?, ?, ?, ?)""",
        ('test_invalid', 'survey', 1, '["question", "response_text"]'),
        test_db
    )
    
    # Create report
    report = create_report([dataset_id], include_viz=False, db_path=test_db)
    
    # Try invalid format
    with pytest.raises(ValueError, match="Invalid format 'invalid'"):
        export_report(report, format='invalid')


def test_create_report_with_visualizations(test_db):
    """Test report creation with visualizations enabled."""
    from modules.report_generator import create_report
    
    # Insert test dataset
    dataset_id = execute_update(
        """INSERT INTO datasets (name, dataset_type, row_count, column_names)
           VALUES (?, ?, ?, ?)""",
        ('test_viz', 'survey', 2, '["question", "response_text"]'),
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
    
    # Create report with visualizations
    report = create_report([dataset_id], include_viz=True, db_path=test_db)
    
    # Verify visualizations are included
    assert 'visualizations' in report
    # Should have at least sentiment distribution chart
    assert len(report['visualizations']) >= 1
    
    # Verify visualization structure
    if report['visualizations']:
        viz = report['visualizations'][0]
        assert 'type' in viz
        assert 'title' in viz
        assert 'dataset_id' in viz
        assert 'figure' in viz


def test_export_markdown_with_themes(test_db):
    """Test Markdown export includes theme summaries."""
    from modules.report_generator import create_report, export_report
    import json
    
    # Insert test dataset
    dataset_id = execute_update(
        """INSERT INTO datasets (name, dataset_type, row_count, column_names)
           VALUES (?, ?, ?, ?)""",
        ('test_themes_export', 'survey', 1, '["question", "response_text"]'),
        test_db
    )
    
    # Insert survey response
    execute_update(
        """INSERT INTO survey_responses (dataset_id, question, response_text, sentiment, sentiment_score)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, 'Q1', 'Great', 'positive', 0.8),
        test_db
    )
    
    # Insert theme
    execute_update(
        """INSERT INTO themes (dataset_id, theme_name, keywords, frequency, representative_quotes)
           VALUES (?, ?, ?, ?, ?)""",
        (dataset_id, 'Theme 1: quality', json.dumps(['great', 'quality']), 1, json.dumps(['Great'])),
        test_db
    )
    
    # Create report with qualitative analysis
    report = create_report([dataset_id], include_viz=False, include_qualitative=True, db_path=test_db)
    markdown_bytes, actual_format = export_report(report, format='markdown')
    markdown_text = markdown_bytes.decode('utf-8')
    
    # Verify theme content in markdown
    assert '## Identified Themes' in markdown_text
    assert 'Theme 1: quality' in markdown_text
    assert 'great' in markdown_text or 'quality' in markdown_text

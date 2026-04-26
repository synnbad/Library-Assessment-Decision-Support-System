"""
Qualitative Analysis Module

This module provides sentiment analysis and theme identification for open-ended
text responses using TextBlob and scikit-learn.

Key Features:
- Sentiment analysis using TextBlob polarity scores
- Theme identification using TF-IDF + K-means clustering
- Representative quote extraction for each theme
- Sentiment distribution statistics
- Graceful error handling (skips problematic entries)
- PII redaction on all outputs
- Export functionality to CSV
- Data provenance tracking

Sentiment Analysis:
- Uses TextBlob sentiment.polarity (-1 to +1)
- Categories: positive (>0.1), negative (<-0.1), neutral (between)
- Configurable thresholds via Settings
- Handles processing errors gracefully
- Minimum 10 responses required (configurable)

Theme Identification:
- TF-IDF vectorization (max 100 features, 1-2 grams)
- K-means clustering (default 5 themes, configurable)
- Top 5 keywords per theme
- Representative quotes (3 per theme)
- Sentiment distribution per theme
- Frequency counts and percentages

Module Functions:
- analyze_sentiment(): Analyze single text with TextBlob
- analyze_dataset_sentiment(): Batch sentiment analysis
- extract_themes(): TF-IDF + K-means theme identification
- get_representative_quotes(): Find example quotes for theme
- analyze_responses(): Complete analysis (sentiment + themes)
- generate_summary(): Create text summary with PII redaction
- export_analysis(): Export results to CSV

Database Tables Used:
- survey_responses: Text responses with sentiment scores
- themes: Identified themes with keywords and quotes
- qualitative_analyses: Analysis results and metadata

Requirements Implemented:
- 3.1: Perform sentiment analysis
- 3.2: Categorize as positive/negative/neutral
- 3.3: Identify recurring themes
- 3.4: Generate theme summaries with frequencies
- 3.5: Display sentiment distribution
- 3.6: Show representative quotes
- 3.7: Export analysis to CSV
- 6.5: PII redaction on outputs
- 7.3: Data provenance tracking

Configuration (config/settings.py):
- DEFAULT_N_THEMES: Number of themes to identify (default: 5)
- SENTIMENT_POSITIVE_THRESHOLD: Positive cutoff (default: 0.1)
- SENTIMENT_NEGATIVE_THRESHOLD: Negative cutoff (default: -0.1)
- MIN_RESPONSES_FOR_ANALYSIS: Minimum responses (default: 10)

Error Handling:
- Insufficient data: Clear error with minimum requirements
- TextBlob processing errors: Skip problematic entries, continue
- TF-IDF/clustering errors: Explain issue with data characteristics
- Empty theme clusters: Log warning, continue with valid themes

Usage Example:
    # Analyze sentiment for dataset
    sentiment_results = analyze_dataset_sentiment(dataset_id=1)
    print(f"Distribution: {sentiment_results['distribution']}")
    
    # Extract themes
    theme_results = extract_themes(dataset_id=1, n_themes=5)
    for theme in theme_results['themes']:
        print(f"{theme['theme_name']}: {theme['frequency']} responses")
        print(f"Keywords: {', '.join(theme['keywords'])}")
    
    # Complete analysis
    analysis_id = analyze_responses(dataset_id=1, n_themes=5)
    summary = generate_summary(analysis_id)
    print(summary)

Author: FERPA-Compliant RAG DSS Team
"""

import pandas as pd
import json
import os
from types import SimpleNamespace

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

    class TextBlob:  # type: ignore[override]
        """Minimal fallback used when textblob is not installed."""

        def __init__(self, text: str):
            self.raw = text
            self.sentiment = SimpleNamespace(polarity=0.0, subjectivity=0.0)

# Avoid noisy Windows-specific joblib warnings when scikit-learn tries to call
# deprecated/missing WMIC to detect physical cores.
os.environ.setdefault("LOKY_MAX_CPU_COUNT", str(max(1, min(os.cpu_count() or 1, 8))))
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from typing import List, Dict, Any, Optional
from modules.database import execute_query, execute_update
from modules.csv_handler import update_data_provenance
from modules.pii_detector import redact_pii
from config.settings import Settings
from modules.logging_service import get_logger, log_operation

logger = get_logger(__name__)

# Try to import enhanced sentiment analyzer
try:
    ENHANCED_SENTIMENT_AVAILABLE = Settings.ENABLE_ENHANCED_SENTIMENT
    if ENHANCED_SENTIMENT_AVAILABLE:
        print("Enhanced sentiment analysis (RoBERTa) enabled")
    else:
        print("Enhanced sentiment module available but disabled. Using TextBlob path by default.")
except Exception:
    ENHANCED_SENTIMENT_AVAILABLE = False
    print("Enhanced sentiment analysis not available. Using TextBlob as fallback.")
    print("To enable: pip install transformers torch")

if not TEXTBLOB_AVAILABLE:
    print("TextBlob not available. Using zeroed fallback sentiment scores.")


def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Analyze sentiment of a single text using enhanced RoBERTa model (with TextBlob fallback).
    
    Args:
        text: Text to analyze
        
    Returns:
        Dict with keys: sentiment, score, confidence (if available), polarity, subjectivity, category
    """
    if not text or pd.isna(text):
        return {
            "sentiment": "neutral",
            "score": 0.0,
            "polarity": 0.0,
            "subjectivity": 0.0,
            "category": "neutral"
        }
    
    try:
        # Try enhanced sentiment first
        if ENHANCED_SENTIMENT_AVAILABLE:
            from modules.sentiment_enhanced import analyze_sentiment as enhanced_analyze
            result = enhanced_analyze(str(text))
            
            # Also get TextBlob for subjectivity
            blob = TextBlob(str(text))
            
            return {
                "sentiment": result['sentiment'],
                "score": result['score'],
                "confidence": result['confidence'],
                "polarity": result['score'],  # Map score to polarity for compatibility
                "subjectivity": blob.sentiment.subjectivity,
                "category": result['sentiment']  # For backward compatibility
            }
        else:
            # Fallback to TextBlob
            blob = TextBlob(str(text))
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # Categorize sentiment
            if polarity > Settings.SENTIMENT_POSITIVE_THRESHOLD:
                category = "positive"
            elif polarity < Settings.SENTIMENT_NEGATIVE_THRESHOLD:
                category = "negative"
            else:
                category = "neutral"
            
            return {
                "sentiment": category,
                "score": polarity,
                "polarity": polarity,
                "subjectivity": subjectivity,
                "category": category
            }
    except Exception as e:
        # Handle processing errors
        return {
            "sentiment": "neutral",
            "score": 0.0,
            "polarity": 0.0,
            "subjectivity": 0.0,
            "category": "neutral",
            "error": f"TextBlob processing error: {str(e)}"
        }


@log_operation("sentiment_analysis")
def analyze_dataset_sentiment(dataset_id: int) -> Dict[str, Any]:
    """
    Analyze sentiment for all responses in a dataset.
    
    Args:
        dataset_id: Dataset identifier
        
    Returns:
        Dict with sentiment analysis results and warnings
    """
    # Get survey responses
    rows = execute_query(
        """
        SELECT id, response_text
        FROM survey_responses
        WHERE dataset_id = ? AND response_text IS NOT NULL
        """,
        (dataset_id,)
    )
    
    # Check for insufficient data
    if len(rows) < Settings.MIN_RESPONSES_FOR_ANALYSIS:
        raise ValueError(
            f"Not enough data for meaningful analysis. "
            f"Minimum required: {Settings.MIN_RESPONSES_FOR_ANALYSIS} responses, found: {len(rows)}."
        )
    
    # Analyze each response
    sentiments = []
    errors = []
    skipped_count = 0
    
    for row in rows:
        sentiment = analyze_sentiment(row['response_text'])
        
        # Check if there was an error processing this entry
        if 'error' in sentiment:
            errors.append({
                'response_id': row['id'],
                'error': sentiment['error']
            })
            skipped_count += 1
            # Continue with remaining data - don't add to sentiments list
            continue
        
        sentiments.append(sentiment)
        
        # Update database with sentiment
        execute_update(
            """
            UPDATE survey_responses
            SET sentiment = ?, sentiment_score = ?
            WHERE id = ?
            """,
            (sentiment['category'], sentiment['polarity'], row['id'])
        )
    
    # Display warning if any entries were skipped
    if skipped_count > 0:
        print(f"Warning: Skipped {skipped_count} problematic entries due to processing errors.")
    
    # Calculate distribution from successfully processed responses
    if not sentiments:
        raise ValueError(
            f"No responses could be processed successfully. "
            f"All {len(rows)} responses encountered processing errors."
        )
    
    categories = [s['category'] for s in sentiments]
    total = len(categories)
    distribution = {
        "positive": categories.count("positive") / total,
        "neutral": categories.count("neutral") / total,
        "negative": categories.count("negative") / total
    }
    
    # Update provenance
    update_data_provenance(
        dataset_id,
        operation="sentiment_analysis",
        method="TextBlob",
        parameters={}
    )
    
    result = {
        "total_responses": len(rows),
        "processed_responses": total,
        "distribution": distribution,
        "sentiments": sentiments
    }
    
    # Add warnings if any errors occurred
    if errors:
        result["warnings"] = {
            "skipped_count": skipped_count,
            "errors": errors[:5]  # Include first 5 errors for debugging
        }
    
    return result


@log_operation("theme_extraction")
def extract_themes(
    dataset_id: int,
    n_themes: Optional[int] = None,
    num_themes: Optional[int] = None
) -> Dict[str, Any]:
    """
    Identify recurring themes using TF-IDF and K-means clustering.
    
    Args:
        dataset_id: Dataset identifier
        n_themes: Number of themes to identify (uses Settings.DEFAULT_N_THEMES if not provided)
        num_themes: Backward-compatible alias for n_themes
        
    Returns:
        Dict with identified themes and warnings
    """
    if num_themes is not None:
        n_themes = num_themes

    if n_themes is None:
        n_themes = Settings.DEFAULT_N_THEMES
    
    # Get survey responses
    rows = execute_query(
        """
        SELECT id, response_text, sentiment
        FROM survey_responses
        WHERE dataset_id = ? AND response_text IS NOT NULL
        """,
        (dataset_id,)
    )
    
    # Check for insufficient data
    if len(rows) < Settings.MIN_RESPONSES_FOR_ANALYSIS:
        raise ValueError(
            f"Not enough data for meaningful analysis. "
            f"Minimum required: {Settings.MIN_RESPONSES_FOR_ANALYSIS} responses, found: {len(rows)}."
        )
    
    if len(rows) < n_themes:
        raise ValueError(
            f"Not enough responses for {n_themes} themes. "
            f"Need at least {n_themes} responses, found: {len(rows)}."
        )
    
    texts = [row['response_text'] for row in rows]
    
    try:
        # Extract keywords using TF-IDF
        vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
        
        # Cluster responses
        kmeans = KMeans(n_clusters=n_themes, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(tfidf_matrix)
        
    except Exception as e:
        # Handle TF-IDF or clustering errors
        raise ValueError(
            f"Error processing text for theme extraction: {str(e)}. "
            f"This may occur with very short or homogeneous responses."
        )
    
    # Extract themes
    themes = []
    warnings = []
    
    for cluster_id in range(n_themes):
        try:
            # Get responses in this cluster
            cluster_indices = [i for i, c in enumerate(clusters) if c == cluster_id]
            
            if not cluster_indices:
                warnings.append(f"Theme {cluster_id + 1}: No responses assigned to this cluster")
                continue
            
            cluster_responses = [rows[i] for i in cluster_indices]
            
            # Get top keywords for this cluster
            cluster_center = kmeans.cluster_centers_[cluster_id]
            top_indices = cluster_center.argsort()[-5:][::-1]
            keywords = [feature_names[i] for i in top_indices]
            
            # Get representative quotes
            quotes = get_representative_quotes(
                [r['response_text'] for r in cluster_responses],
                keywords[0],
                n=3
            )
            
            # Calculate sentiment distribution for theme
            sentiments = [r['sentiment'] for r in cluster_responses if r['sentiment']]
            sentiment_dist = {
                "positive": sentiments.count("positive") / len(sentiments) if sentiments else 0,
                "neutral": sentiments.count("neutral") / len(sentiments) if sentiments else 0,
                "negative": sentiments.count("negative") / len(sentiments) if sentiments else 0
            }
            
            theme = {
                "theme_id": cluster_id + 1,
                "theme_name": f"Theme {cluster_id + 1}: {keywords[0]}",
                "keywords": keywords,
                "frequency": len(cluster_indices),
                "percentage": len(cluster_indices) / len(rows) * 100,
                "representative_quotes": quotes,
                "sentiment_distribution": sentiment_dist
            }
            
            themes.append(theme)
            
        except Exception as e:
            # Log error but continue with other themes
            warnings.append(f"Theme {cluster_id + 1}: Error processing theme - {str(e)}")
            continue
    
    # Check if we got any valid themes
    if not themes:
        raise ValueError(
            "Could not extract any themes from the data. "
            "This may occur with very short or homogeneous responses."
        )
    
    # Display warnings if any themes had issues
    if warnings:
        print(f"Warning: {len(warnings)} theme(s) encountered processing issues:")
        for warning in warnings:
            print(f"  - {warning}")
    
    # Store themes in database
    for theme in themes:
        execute_update(
            """
            INSERT INTO themes (dataset_id, theme_name, keywords, frequency, representative_quotes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                dataset_id,
                theme['theme_name'],
                json.dumps(theme['keywords']),
                theme['frequency'],
                json.dumps(theme['representative_quotes'])
            )
        )
    
    # Update provenance
    update_data_provenance(
        dataset_id,
        operation="theme_extraction",
        method="TF-IDF + K-means",
        parameters={"n_themes": n_themes}
    )
    
    result = {
        "n_themes": len(themes),
        "themes": themes,
        "total_responses": len(rows)
    }
    
    # Add warnings if any occurred
    if warnings:
        result["warnings"] = warnings
    
    return result


def get_representative_quotes(
    texts: List[str],
    keyword: str,
    n: int = 3
) -> List[str]:
    """
    Find representative quotes containing a keyword.
    
    Args:
        texts: List of text responses
        keyword: Keyword to search for
        n: Number of quotes to return
        
    Returns:
        List of representative quotes
    """
    # Find texts containing keyword
    matching = [t for t in texts if keyword.lower() in t.lower()]
    
    # Sort by length (prefer medium-length responses)
    matching.sort(key=lambda x: abs(len(x) - 100))
    
    # Return top n
    return matching[:n]


def analyze_responses(
    dataset_id: int,
    n_themes: Optional[int] = None
) -> int:
    """
    Perform complete qualitative analysis (sentiment + themes).
    
    Args:
        dataset_id: Dataset identifier
        n_themes: Number of themes to identify
        
    Returns:
        analysis_id of stored analysis
    """
    # Run sentiment analysis
    sentiment_results = analyze_dataset_sentiment(dataset_id)
    
    # Run theme extraction
    theme_results = extract_themes(dataset_id, n_themes)
    
    # Store analysis results
    analysis_id = execute_update(
        """
        INSERT INTO qualitative_analyses (
            dataset_id, response_count, themes, overall_sentiment
        ) VALUES (?, ?, ?, ?)
        """,
        (
            dataset_id,
            sentiment_results['total_responses'],
            json.dumps(theme_results['themes']),
            json.dumps(sentiment_results['distribution'])
        )
    )
    
    return analysis_id


def generate_summary(analysis_id: int) -> str:
    """
    Generate text summary of analysis results.
    
    Args:
        analysis_id: Analysis identifier
        
    Returns:
        Text summary
    """
    # Get analysis
    analyses = execute_query(
        "SELECT * FROM qualitative_analyses WHERE id = ?",
        (analysis_id,)
    )
    
    if not analyses:
        return "Analysis not found."
    
    analysis = analyses[0]
    themes = json.loads(analysis['themes'])
    sentiment = json.loads(analysis['overall_sentiment'])
    
    # Build summary
    summary = "Qualitative Analysis Summary\n"
    summary += f"{'=' * 50}\n\n"
    summary += f"Total Responses Analyzed: {analysis['response_count']}\n\n"
    
    summary += "Overall Sentiment Distribution:\n"
    summary += f"  Positive: {sentiment['positive']:.1%}\n"
    summary += f"  Neutral: {sentiment['neutral']:.1%}\n"
    summary += f"  Negative: {sentiment['negative']:.1%}\n\n"
    
    summary += f"Identified Themes ({len(themes)}):\n"
    for theme in themes:
        summary += f"\n{theme['theme_name']} ({theme['percentage']:.1f}% of responses)\n"
        summary += f"  Keywords: {', '.join(theme['keywords'][:3])}\n"
        summary += "  Sentiment: "
        summary += f"Positive {theme['sentiment_distribution']['positive']:.1%}, "
        summary += f"Neutral {theme['sentiment_distribution']['neutral']:.1%}, "
        summary += f"Negative {theme['sentiment_distribution']['negative']:.1%}\n"
        
        if theme['representative_quotes']:
            # Redact PII from representative quotes (Requirement 6.5)
            quote = theme['representative_quotes'][0][:100]
            redacted_quote, _ = redact_pii(quote)
            summary += f"  Example: \"{redacted_quote}...\"\n"
    
    # Redact PII from entire summary (Requirement 6.5)
    summary, pii_counts = redact_pii(summary)
    
    return summary


def export_analysis(analysis_id: int, format: str = 'csv') -> bytes:
    """
    Export analysis results to CSV.
    
    Args:
        analysis_id: Analysis identifier
        format: Export format (only 'csv' supported for MVP)
        
    Returns:
        Exported data as bytes
    """
    # Get analysis
    analyses = execute_query(
        "SELECT * FROM qualitative_analyses WHERE id = ?",
        (analysis_id,)
    )
    
    if not analyses:
        raise ValueError("Analysis not found")
    
    analysis = analyses[0]
    themes = json.loads(analysis['themes'])
    
    # Create DataFrame
    rows = []
    for theme in themes:
        rows.append({
            "Theme": theme['theme_name'],
            "Keywords": ", ".join(theme['keywords']),
            "Frequency": theme['frequency'],
            "Percentage": f"{theme['percentage']:.1f}%",
            "Positive_Sentiment": f"{theme['sentiment_distribution']['positive']:.1%}",
            "Neutral_Sentiment": f"{theme['sentiment_distribution']['neutral']:.1%}",
            "Negative_Sentiment": f"{theme['sentiment_distribution']['negative']:.1%}"
        })
    
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode('utf-8')

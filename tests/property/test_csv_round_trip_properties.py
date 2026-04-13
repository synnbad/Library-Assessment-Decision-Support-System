"""
Property-Based Tests for CSV Round-Trip Validation

Feature: repo-rehabilitation
Property 1: CSV Round-Trip Preservation

For any valid DataFrame with survey, usage, or circulation schema,
serializing to CSV then parsing back SHALL produce an equivalent DataFrame
with the same data values, column names, and data types.

Validates: Requirements 7.4, 7.5, 7.6, 7.7
"""

import pandas as pd
import numpy as np
from hypothesis import given, settings, strategies as st
from modules.csv_handler import (
    serialize_to_csv,
    parse_from_csv,
    dataframes_equivalent,
    validate_round_trip
)


# ============================================================================
# Hypothesis Strategies for DataFrame Generation
# ============================================================================

@st.composite
def survey_dataframe(draw):
    """Generate random DataFrame with survey schema."""
    n_rows = draw(st.integers(min_value=1, max_value=100))
    
    # Generate survey data
    response_dates = [f"2024-{draw(st.integers(1, 12)):02d}-{draw(st.integers(1, 28)):02d}" 
                      for _ in range(n_rows)]
    questions = [draw(st.text(min_size=5, max_size=100)) for _ in range(n_rows)]
    responses = [draw(st.text(min_size=1, max_size=500)) for _ in range(n_rows)]
    sentiments = [draw(st.floats(min_value=-1.0, max_value=1.0, allow_nan=False)) 
                  for _ in range(n_rows)]
    
    return pd.DataFrame({
        'response_date': response_dates,
        'question': questions,
        'response_text': responses,
        'sentiment': sentiments
    })


@st.composite
def usage_dataframe(draw):
    """Generate random DataFrame with usage schema."""
    n_rows = draw(st.integers(min_value=1, max_value=100))
    
    # Generate usage data
    dates = [f"2024-{draw(st.integers(1, 12)):02d}-{draw(st.integers(1, 28)):02d}" 
             for _ in range(n_rows)]
    metric_names = [draw(st.sampled_from(['visits', 'sessions', 'downloads', 'checkouts'])) 
                    for _ in range(n_rows)]
    metric_values = [draw(st.integers(min_value=0, max_value=10000)) for _ in range(n_rows)]
    
    return pd.DataFrame({
        'date': dates,
        'metric_name': metric_names,
        'metric_value': metric_values
    })


@st.composite
def circulation_dataframe(draw):
    """Generate random DataFrame with circulation schema."""
    n_rows = draw(st.integers(min_value=1, max_value=100))
    
    # Generate circulation data
    checkout_dates = [f"2024-{draw(st.integers(1, 12)):02d}-{draw(st.integers(1, 28)):02d}" 
                      for _ in range(n_rows)]
    material_types = [draw(st.sampled_from(['book', 'ebook', 'journal', 'dvd', 'audiobook'])) 
                      for _ in range(n_rows)]
    patron_types = [draw(st.sampled_from(['student', 'faculty', 'staff', 'community'])) 
                    for _ in range(n_rows)]
    
    return pd.DataFrame({
        'checkout_date': checkout_dates,
        'material_type': material_types,
        'patron_type': patron_types
    })


# ============================================================================
# Property Tests
# ============================================================================

@settings(max_examples=100)
@given(df=survey_dataframe())
def test_csv_round_trip_survey(df):
    """
    Feature: repo-rehabilitation, Property 1: CSV round-trip preservation
    
    Test that survey DataFrames can round-trip through CSV serialization.
    """
    # Serialize to CSV
    csv_string = serialize_to_csv(df)
    
    # Parse back to DataFrame
    df_restored = parse_from_csv(csv_string)
    
    # Verify equivalence
    assert dataframes_equivalent(df, df_restored), \
        "Survey DataFrame not equivalent after round-trip"


@settings(max_examples=100)
@given(df=usage_dataframe())
def test_csv_round_trip_usage(df):
    """
    Feature: repo-rehabilitation, Property 1: CSV round-trip preservation
    
    Test that usage DataFrames can round-trip through CSV serialization.
    """
    # Serialize to CSV
    csv_string = serialize_to_csv(df)
    
    # Parse back to DataFrame
    df_restored = parse_from_csv(csv_string)
    
    # Verify equivalence
    assert dataframes_equivalent(df, df_restored), \
        "Usage DataFrame not equivalent after round-trip"


@settings(max_examples=100)
@given(df=circulation_dataframe())
def test_csv_round_trip_circulation(df):
    """
    Feature: repo-rehabilitation, Property 1: CSV round-trip preservation
    
    Test that circulation DataFrames can round-trip through CSV serialization.
    """
    # Serialize to CSV
    csv_string = serialize_to_csv(df)
    
    # Parse back to DataFrame
    df_restored = parse_from_csv(csv_string)
    
    # Verify equivalence
    assert dataframes_equivalent(df, df_restored), \
        "Circulation DataFrame not equivalent after round-trip"


@settings(max_examples=100)
@given(df=survey_dataframe())
def test_validate_round_trip_survey(df):
    """
    Feature: repo-rehabilitation, Property 1: CSV round-trip preservation
    
    Test validate_round_trip function with survey data.
    """
    is_valid, error_msg = validate_round_trip(df, 'survey')
    assert is_valid, f"Round-trip validation failed: {error_msg}"


@settings(max_examples=100)
@given(df=usage_dataframe())
def test_validate_round_trip_usage(df):
    """
    Feature: repo-rehabilitation, Property 1: CSV round-trip preservation
    
    Test validate_round_trip function with usage data.
    """
    is_valid, error_msg = validate_round_trip(df, 'usage')
    assert is_valid, f"Round-trip validation failed: {error_msg}"


@settings(max_examples=100)
@given(df=circulation_dataframe())
def test_validate_round_trip_circulation(df):
    """
    Feature: repo-rehabilitation, Property 1: CSV round-trip preservation
    
    Test validate_round_trip function with circulation data.
    """
    is_valid, error_msg = validate_round_trip(df, 'circulation')
    assert is_valid, f"Round-trip validation failed: {error_msg}"


# ============================================================================
# Edge Case Tests
# ============================================================================

@settings(max_examples=100)
@given(
    df=survey_dataframe(),
    special_char=st.sampled_from([',', '"', '\n', '\r', '\t', '\\'])
)
def test_round_trip_with_special_characters(df, special_char):
    """
    Feature: repo-rehabilitation, Property 1: CSV round-trip preservation
    
    Test round-trip with special CSV characters.
    """
    # Add special character to text columns
    if len(df) > 0:
        df.loc[0, 'response_text'] = f"Text with {special_char} character"
    
    csv_string = serialize_to_csv(df)
    df_restored = parse_from_csv(csv_string)
    
    assert dataframes_equivalent(df, df_restored), \
        f"DataFrame with special character '{special_char}' not equivalent after round-trip"


@settings(max_examples=100)
@given(df=survey_dataframe())
def test_round_trip_with_empty_strings(df):
    """
    Feature: repo-rehabilitation, Property 1: CSV round-trip preservation
    
    Test round-trip with empty strings.
    """
    # Add empty strings
    if len(df) > 0:
        df.loc[0, 'response_text'] = ""
    
    csv_string = serialize_to_csv(df)
    df_restored = parse_from_csv(csv_string)
    
    assert dataframes_equivalent(df, df_restored), \
        "DataFrame with empty strings not equivalent after round-trip"


@settings(max_examples=100)
@given(
    df=usage_dataframe(),
    precision=st.integers(min_value=0, max_value=10)
)
def test_round_trip_numeric_precision(df, precision):
    """
    Feature: repo-rehabilitation, Property 1: CSV round-trip preservation
    
    Test round-trip preserves numeric precision.
    """
    # Add floating point column with specific precision
    df['float_value'] = [round(np.random.random(), precision) for _ in range(len(df))]
    
    csv_string = serialize_to_csv(df)
    df_restored = parse_from_csv(csv_string)
    
    assert dataframes_equivalent(df, df_restored), \
        f"DataFrame with {precision} decimal precision not equivalent after round-trip"

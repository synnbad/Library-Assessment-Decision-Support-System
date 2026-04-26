from io import BytesIO

import pandas as pd

from modules import data_importer


def test_parse_json_reference_log_detects_reference_type():
    payload = b"""
    [
      {"timestamp": "2026-01-01", "question_text": "Where is printing?", "channel": "chat"},
      {"timestamp": "2026-01-02", "question_text": "How do I find articles?", "channel": "desk"}
    ]
    """

    result = data_importer.parse_assessment_file(BytesIO(payload), "libanswers_reference.json")

    assert result.detected_type == "reference"
    assert "response_text" in result.dataframe.columns
    assert result.data_dictionary[0]["column"]


def test_counter_wide_report_normalizes_to_metric_rows():
    csv = (
        "Title,Metric Type,Jan 2026,Feb 2026\n"
        "Database A,Total Item Requests,10,15\n"
        "Database B,Searches,5,9\n"
    ).encode()

    result = data_importer.parse_assessment_file(BytesIO(csv), "counter_database_report.csv")

    assert result.detected_type == "e_resource"
    assert set(["date", "metric_name", "metric_value", "category"]).issubset(result.dataframe.columns)
    assert len(result.dataframe) == 4


def test_metadata_suggestions_include_dictionary_and_keywords():
    df = pd.DataFrame(
        {
            "Date": ["2026-01-01"],
            "Room": ["Room A"],
            "Bookings": [12],
        }
    )

    metadata = data_importer.build_metadata_suggestions(df, "spaces", "libcal_room_bookings.xlsx")

    assert metadata["source"] == "LibCal"
    assert "spaces" in metadata["keywords"]
    assert metadata["data_dictionary"][0]["role"] == "date/time"

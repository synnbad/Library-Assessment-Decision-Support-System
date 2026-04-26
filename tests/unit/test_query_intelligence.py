import pandas as pd

from modules import query_intelligence as qi


def test_build_dataset_profile_detects_survey_strengths():
    df = pd.DataFrame(
        {
            "response_date": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "question": ["What worked?", "What did not?", "Other comments?"],
            "response_text": [
                "The staff were helpful and the study rooms were quiet.",
                "The computers were slow and printing was confusing.",
                "I liked the collection, but evening hours were too short.",
            ],
            "language": ["en", "en", "es"],
            "expected_sentiment": ["positive", "negative", "neutral"],
        }
    )

    profile = qi.build_dataset_profile(df, "survey", "Feedback")

    assert profile.is_text_ready
    assert "response_text" in profile.text_columns
    assert "response_date" not in profile.text_columns
    assert "response_date" in profile.date_columns
    assert "en" in profile.languages
    assert "positive" in profile.sentiment_labels
    assert any("qualitative" in strength for strength in profile.strengths)


def test_build_dataset_profile_warns_about_coded_missing_values():
    df = pd.DataFrame(
        {
            "date": ["2023-12-31", "2023-12-31"],
            "metric_name": ["VISITS", "TOTCIR"],
            "metric_value": [100, -666],
            "state": ["NY", "-888"],
        }
    )

    profile = qi.build_dataset_profile(df, "usage", "PLS")

    assert profile.is_numeric_ready
    assert "metric_value" in profile.numeric_columns
    assert profile.coded_missing_columns
    assert profile.coded_missing_rates["metric_value"] == 0.5
    assert any("Coded missing values" in warning for warning in profile.warnings)


def test_suggest_questions_uses_dataset_shape():
    survey = qi.build_dataset_profile(
        pd.DataFrame(
            {
                "response_text": ["The room was noisy but the staff helped."],
                "language": ["en"],
                "label": ["negative"],
            }
        ),
        "survey",
        "Survey",
    )

    questions = qi.suggest_questions(survey)

    assert any("main themes" in question for question in questions)
    assert any("language" in question for question in questions)
    assert any("report" in question for question in questions)


def test_classify_and_rewrite_query_for_qualitative_intent():
    profile = qi.build_dataset_profile(
        pd.DataFrame({"response_text": ["The computers were slow and frustrating."]}),
        "survey",
        "Feedback",
    )

    classification = qi.classify_query("What are people mad about?", [profile])
    rewritten = qi.rewrite_query("What are people mad about?", [profile], classification["intent"])

    assert classification["intent"] == "qualitative"
    assert "sentiment" in rewritten
    assert "Feedback" in rewritten


def test_followups_reflect_quantitative_intent():
    profile = qi.build_dataset_profile(
        pd.DataFrame(
            {
                "date": ["2023-01-01", "2023-02-01"],
                "metric_name": ["visits", "visits"],
                "metric_value": [10, 20],
            }
        ),
        "usage",
        "Usage",
    )

    followups = qi.suggest_followups("Which metric is highest?", "Visits are highest.", [profile])

    assert any("top and bottom" in followup for followup in followups)
    assert any("trends" in followup for followup in followups)


def test_report_section_suggestions_reflect_profile_capabilities():
    from ui import smart_guidance

    text_profile = qi.build_dataset_profile(
        pd.DataFrame({"response_text": ["A useful but noisy study room."]}),
        "survey",
        "Survey",
    )
    metric_profile = qi.build_dataset_profile(
        pd.DataFrame(
            {
                "date": ["2023-01-01"],
                "metric_name": ["visits"],
                "metric_value": [42],
            }
        ),
        "usage",
        "Usage",
    )

    sections = smart_guidance.report_section_suggestions([text_profile, metric_profile])

    assert "Theme summary" in sections
    assert "Metric summary" in sections
    assert "Trend analysis" in sections


def test_quantitative_questions_include_category_comparison():
    from ui import smart_guidance

    profile = qi.build_dataset_profile(
        pd.DataFrame(
            {
                "metric_value": [1, 2],
                "state": ["NY", "CA"],
            }
        ),
        "usage",
        "Usage",
    )

    questions = smart_guidance.quantitative_next_questions("Usage", profile)

    assert any("Compare Usage by state" in question for question in questions)


def test_empty_dataframe_profile_is_safe_and_warns_by_type():
    profile = qi.build_dataset_profile(pd.DataFrame(columns=["response_text"]), "survey", "Empty")

    assert profile.row_count == 0
    assert profile.columns == ["response_text"]
    assert profile.is_text_ready
    assert any("small" in warning for warning in profile.warnings)


def test_all_missing_dataframe_profile_does_not_crash():
    profile = qi.build_dataset_profile(
        pd.DataFrame({"metric_value": [None, None], "state": ["", ""]}),
        "usage",
        "Missing Usage",
    )

    assert "metric_value" in profile.missing_columns
    assert "state" in profile.missing_columns
    assert any("fully missing" in warning for warning in profile.warnings)


def test_rewrite_query_without_profiles_has_safe_context():
    rewritten = qi.rewrite_query("Summarize this", [], intent="reporting")

    assert "no uploaded dataset profile is available" in rewritten
    assert "report section" in rewritten


def test_data_inventory_query_is_profile_native():
    profile = qi.build_dataset_profile(
        pd.DataFrame({"response_text": ["Helpful staff and good spaces."]}),
        "survey",
        "Survey Data",
    )

    classification = qi.classify_query("What data do I have available?", [profile])
    answer = qi.answer_from_profiles("What data do I have available?", [profile], classification["intent"])

    assert classification["intent"] == "data_inventory"
    assert "Survey Data" in answer
    assert "rows" in answer


def test_data_quality_query_mentions_profile_warnings():
    profile = qi.build_dataset_profile(
        pd.DataFrame({"metric_value": [None, None]}),
        "usage",
        "Usage Data",
    )

    classification = qi.classify_query("What limitations should I document?", [profile])
    answer = qi.answer_from_profiles("What limitations should I document?", [profile], classification["intent"])

    assert classification["intent"] == "data_quality"
    assert "Usage Data" in answer
    assert "limitations" in answer.lower() or "missing" in answer.lower()


def test_evidence_assessment_for_profile_answer_is_high():
    profile = qi.build_dataset_profile(pd.DataFrame({"response_text": ["A useful comment."]}), "survey", "Survey")

    evidence = qi.assess_evidence(0.0, 0, "data_inventory", "What data do I have?", [profile])

    assert evidence["label"] == "High"
    assert evidence["score"] == 1.0
    assert "dataset profiles" in evidence["reason"]


def test_evidence_assessment_explains_broad_low_retrieval():
    evidence = qi.assess_evidence(
        0.2,
        2,
        "retrieval",
        "Give me an overview of available data",
        [],
    )

    assert evidence["label"] == "Low"
    assert "Broad" in evidence["reason"]


def test_suggestions_are_deduped_and_limited_for_sparse_profile():
    profile = qi.build_dataset_profile(
        pd.DataFrame({"metric_value": [1], "value": [2]}),
        "usage",
        "Sparse",
    )

    questions = qi.suggest_questions(profile, limit=3)

    assert len(questions) == 3
    assert len(questions) == len(set(questions))

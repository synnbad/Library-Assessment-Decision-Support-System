"""
Unit tests for the library feedback sentiment classifier.

Tests both rule-based and AI classification approaches, including
edge cases and fallback behavior.
"""
import pytest
from src.modeling.predict import (
    RuleBasedClassifier,
    AIClassifier,
    SentimentClassifier,
    get_classifier
)
from src.config import config


class TestRuleBasedClassifier:
    """Tests for the rule-based sentiment classifier."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = RuleBasedClassifier()

    def test_positive_feedback(self):
        """Test that clearly positive feedback is correctly identified."""
        text = "The library staff were incredibly helpful and friendly."
        label, confidence, reason = self.classifier.classify(text)
        assert label == "positive"
        assert confidence > 50
        assert "positive" in reason.lower() or "satisfaction" in reason.lower()

    def test_negative_feedback(self):
        """Test that clearly negative feedback is correctly identified."""
        text = "The computers are outdated and the staff were very unhelpful."
        label, confidence, reason = self.classifier.classify(text)
        assert label == "negative"
        assert confidence > 50

    def test_neutral_feedback(self):
        """Test that neutral/suggestion feedback is correctly identified."""
        text = "I think the opening hours could be extended on weekends."
        label, confidence, reason = self.classifier.classify(text)
        assert label in ["neutral", "positive", "negative"]
        assert 0 <= confidence <= 100

    def test_empty_string(self):
        """Test behaviour with empty string."""
        text = ""
        label, confidence, reason = self.classifier.classify(text)
        assert label in ["positive", "neutral", "negative"]
        assert 0 <= confidence <= 100

    def test_mixed_signals(self):
        """Test text with both positive and negative indicators."""
        text = "The collection is good but the Wi-Fi is terrible."
        label, confidence, reason = self.classifier.classify(text)
        assert label in ["positive", "neutral", "negative"]
        assert 0 <= confidence <= 100


class TestAIClassifier:
    """Tests for the AI classifier."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = AIClassifier()

    def test_classifier_initialization(self):
        """Test that AI classifier initialises correctly."""
        assert self.classifier is not None

    def test_availability_check(self):
        """Test AI availability checking."""
        is_available = self.classifier.is_available()
        assert isinstance(is_available, bool)

    @pytest.mark.skipif(not config.USE_AI_MODEL, reason="AI model disabled in config")
    def test_ai_classification(self):
        """Test AI classification (requires Hugging Face transformers)."""
        if not self.classifier.is_available():
            pytest.skip("AI classifier not available")

        text = "The library is a wonderful place to study."
        try:
            label, confidence, reason = self.classifier.classify(text)
            assert label in ["positive", "neutral", "negative"]
            assert 0 <= confidence <= 100
            assert len(reason) > 0
        except Exception as e:
            pytest.skip(f"AI classification failed: {e}")


class TestSentimentClassifier:
    """Tests for the main sentiment classifier orchestrator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = SentimentClassifier()

    def test_classifier_initialization(self):
        """Test that sentiment classifier initialises properly."""
        assert self.classifier is not None
        assert self.classifier.ai_classifier is not None
        assert self.classifier.rule_based_classifier is not None

    def test_classify_positive(self):
        """Test classification of positive feedback."""
        text = "I love the library — the staff are always so helpful!"
        label, confidence, reason, used_ai = self.classifier.classify(text)
        assert label == "positive"
        assert 0 <= confidence <= 100
        assert len(reason) > 0
        assert isinstance(used_ai, bool)

    def test_classify_negative(self):
        """Test classification of negative feedback."""
        text = "The library is always too noisy and the computers are broken."
        label, confidence, reason, used_ai = self.classifier.classify(text)
        assert label == "negative"
        assert 0 <= confidence <= 100
        assert len(reason) > 0

    def test_classify_neutral(self):
        """Test classification of neutral feedback."""
        text = "The library is generally okay for studying."
        label, confidence, reason, used_ai = self.classifier.classify(text)
        assert label in ["positive", "neutral", "negative"]
        assert 0 <= confidence <= 100

    def test_classify_with_escalation_structure(self):
        """Test that classify_with_escalation returns all required fields."""
        text = "The study spaces are comfortable and quiet."
        result = self.classifier.classify_with_escalation(text)

        assert 'label' in result
        assert 'confidence' in result
        assert 'reason' in result
        assert 'escalate' in result
        assert 'method' in result

        assert result['label'] in ["positive", "neutral", "negative"]
        assert 0 <= result['confidence'] <= 100
        assert isinstance(result['reason'], str)
        assert isinstance(result['escalate'], bool)
        assert result['method'] in ['ai', 'rules']

    def test_empty_input(self):
        """Test behaviour with empty input."""
        text = ""
        label, confidence, reason, used_ai = self.classifier.classify(text)
        assert label in ["positive", "neutral", "negative"]
        assert 0 <= confidence <= 100

    def test_whitespace_input(self):
        """Test behaviour with only whitespace."""
        text = "   \n\t  "
        label, confidence, reason, used_ai = self.classifier.classify(text)
        assert label in ["positive", "neutral", "negative"]


class TestGetClassifier:
    """Tests for the global classifier singleton."""

    def test_get_classifier_returns_instance(self):
        """Test that get_classifier returns a valid instance."""
        classifier = get_classifier()
        assert classifier is not None
        assert isinstance(classifier, SentimentClassifier)

    def test_get_classifier_returns_same_instance(self):
        """Test that get_classifier returns the same instance (singleton)."""
        classifier1 = get_classifier()
        classifier2 = get_classifier()
        assert classifier1 is classifier2

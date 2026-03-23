"""
Sentiment classification engine for student library feedback.

Provides both AI-powered and rule-based classification to determine
if student feedback is positive, neutral, or negative.
"""
import re
import logging
from typing import Tuple, Dict
from src.config import config

logger = logging.getLogger(__name__)


class RuleBasedClassifier:
    """Rule-based classifier using keyword scoring tuned for library feedback."""

    POSITIVE_WORDS = [
        'great', 'good', 'excellent', 'amazing', 'wonderful', 'fantastic',
        'awesome', 'love', 'loved', 'like', 'enjoy', 'enjoyed', 'helpful',
        'useful', 'appreciate', 'appreciated', 'thanks', 'thank you', 'perfect',
        'impressed', 'happy', 'pleased', 'nice', 'brilliant', 'outstanding',
        'friendly', 'welcoming', 'comfortable', 'clean', 'quiet', 'spacious',
        'organised', 'organized', 'efficient', 'knowledgeable', 'supportive',
        'convenient', 'accessible', 'satisfied', 'recommend', 'best',
        'very helpful', 'well maintained', 'easy to find', 'easy to use',
        'great selection', 'wide range', 'good collection', 'fast', 'quick',
    ]

    NEGATIVE_WORDS = [
        'terrible', 'awful', 'horrible', 'worst', 'bad', 'broken', 'useless',
        'disappointed', 'disappointing', 'frustrating', 'frustrated', 'angry',
        'upset', 'unacceptable', 'poor', 'unhappy', 'hate', 'ridiculous',
        'pathetic', 'disgusted', 'waste', 'noisy', 'dirty', 'crowded',
        'outdated', 'limited', 'insufficient', 'unavailable', 'slow', 'rude',
        'unhelpful', 'unfriendly', 'disorganised', 'disorganized', 'confusing',
        'hard to find', 'not enough', 'never available', 'always full',
        'not working', 'out of date', 'missing', 'damaged', 'uncomfortable',
        'overcrowded', 'understaffed', 'ignored', 'long wait', 'restricted',
    ]

    def __init__(self):
        logger.info("Initialized rule-based classifier")

    def classify(self, text: str) -> Tuple[str, float, str]:
        text_lower = text.lower().strip()
        pos = self._positive_score(text_lower)
        neg = self._negative_score(text_lower)
        neu = self._neutral_score(text_lower, pos, neg)
        scores = {'positive': pos, 'neutral': neu, 'negative': neg}
        label = max(scores, key=lambda k: scores[k])
        return label, scores[label], self._reason(label, text_lower)

    def _positive_score(self, text: str) -> float:
        score = min(sum(20.0 for w in self.POSITIVE_WORDS if w in text), 70.0)
        strong = [
            'very helpful', 'really helpful', 'great service', 'excellent service',
            'love the library', 'best library', 'highly recommend', 'always helpful',
        ]
        score += sum(20.0 for p in strong if p in text)
        if '!' in text and any(w in text for w in self.POSITIVE_WORDS):
            score += 10.0
        return min(score, 100.0)

    def _negative_score(self, text: str) -> float:
        score = min(sum(20.0 for w in self.NEGATIVE_WORDS if w in text), 70.0)
        strong = [
            'not enough', 'never available', 'always full', 'not working',
            'very disappointed', 'very frustrated', 'not helpful', 'really bad',
        ]
        score += sum(20.0 for p in strong if p in text)
        if re.search(r"\b(not|never|no|isn't|wasn't|aren't|don't|doesn't)\b", text):
            score += 15.0
        if '!' in text and any(w in text for w in self.NEGATIVE_WORDS):
            score += 10.0
        return min(score, 100.0)

    def _neutral_score(self, text: str, pos: float, neg: float) -> float:
        score = 40.0 - (20.0 if pos > 50 or neg > 50 else 0.0)
        patterns = [
            r'\bi (think|suggest|feel|believe|noticed|found)\b',
            r'\bit would be (nice|good|better|helpful)\b',
            r'\bcould (be|use|do with)\b',
            r'\bperhaps\b', r'\bmaybe\b', r'\bsometimes\b',
            r'\bgenerally\b', r'\boverall\b',
        ]
        score += sum(10.0 for p in patterns if re.search(p, text))
        return min(max(score, 0.0), 100.0)

    def _reason(self, label: str, text: str) -> str:
        if label == 'positive':
            found = [w for w in self.POSITIVE_WORDS if w in text]
            return (f"Expresses satisfaction with library services ('{found[0]}')"
                    if found else "Overall positive tone toward library services")
        if label == 'negative':
            found = [w for w in self.NEGATIVE_WORDS if w in text]
            return (f"Expresses dissatisfaction with library services ('{found[0]}')"
                    if found else "Overall negative tone or complaint about library services")
        return "Neutral observation, suggestion, or factual feedback about library services"


class AIClassifier:
    """
    AI classifier using Hugging Face DistilBERT (local, no API key needed).
    Maps binary POSITIVE/NEGATIVE output to positive/neutral/negative.
    """

    def __init__(self):
        self.pipeline = None
        self._load()

    def _load(self):
        try:
            from transformers import pipeline as hf_pipeline
            logger.info("Loading DistilBERT sentiment model...")
            self.pipeline = hf_pipeline(
                "text-classification",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=-1,
            )
            logger.info("DistilBERT loaded successfully")
        except ImportError:
            logger.warning("transformers not installed - AI unavailable")
            self.pipeline = None
        except Exception as e:
            logger.error("Could not load model: %s", e)
            self.pipeline = None

    def is_available(self) -> bool:
        return self.pipeline is not None

    def classify(self, text: str) -> Tuple[str, float, str]:
        if not self.is_available():
            raise RuntimeError("AI classifier not available")

        result = self.pipeline(text, truncation=True, max_length=512)[0]
        sentiment = result['label']
        score = result['score']
        confidence = round(score * 100, 1)

        if sentiment == 'POSITIVE' and score >= 0.75:
            return (
                'positive',
                confidence,
                f"Positive sentiment detected toward library services (model confidence: {score:.2f})",
            )

        if sentiment == 'NEGATIVE' and score >= 0.75:
            return (
                'negative',
                confidence,
                f"Negative sentiment detected toward library services (model confidence: {score:.2f})",
            )

        neutral_conf = min(round((1.0 - score) * 100 + 40, 1), 80.0)
        return (
            'neutral',
            neutral_conf,
            f"Mixed or neutral sentiment detected (model confidence: {score:.2f})",
        )


class SentimentClassifier:
    """Orchestrates AI and rule-based classification with automatic fallback."""

    def __init__(self):
        logger.info("Initializing SentimentClassifier")
        self.ai_classifier = AIClassifier()
        self.rule_based_classifier = RuleBasedClassifier()

    def classify(self, text: str) -> Tuple[str, float, str, bool]:
        if not text or not text.strip():
            return 'neutral', 30.0, 'Empty or invalid input', False

        if config.USE_AI_MODEL and self.ai_classifier.is_available():
            try:
                label, confidence, reason = self.ai_classifier.classify(text)
                return label, confidence, reason, True
            except Exception as e:
                logger.warning("AI failed, falling back to rules: %s", e)

        label, confidence, reason = self.rule_based_classifier.classify(text)
        return label, confidence, reason, False

    def classify_with_escalation(self, text: str) -> Dict:
        label, confidence, reason, used_ai = self.classify(text)
        escalate = confidence < config.CONFIDENCE_THRESHOLD
        if escalate:
            logger.info("Escalation flagged: confidence=%.1f < threshold=%d",
                        confidence, config.CONFIDENCE_THRESHOLD)
        return {
            'label': label,
            'confidence': confidence,
            'reason': reason,
            'escalate': escalate,
            'method': 'ai' if used_ai else 'rules',
        }


# Backwards-compatible alias
IntentClassifier = SentimentClassifier

_instance = None


def get_classifier() -> SentimentClassifier:
    """Return the global singleton classifier."""
    global _instance
    if _instance is None:
        _instance = SentimentClassifier()
    return _instance

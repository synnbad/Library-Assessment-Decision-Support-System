"""
Demo script to showcase the library feedback sentiment classifier.

Run this to demonstrate the classifier's capabilities interactively.
"""
from src.modeling.predict import get_classifier
from src.config import config
import time


def print_header():
    """Print demo header."""
    print("\n" + "=" * 80)
    print(" " * 15 + "LIBRARY FEEDBACK SENTIMENT ANALYSIS - DEMO")
    print("=" * 80)
    print("\nWelcome! This demo classifies student library feedback.")
    print("Sentiments: POSITIVE | NEUTRAL | NEGATIVE\n")


def print_classification(text: str, result: dict):
    """Pretty print a classification result."""
    print(f"\nFeedback: \"{text}\"")
    print("-" * 80)

    label_display = result['label'].upper()
    print(f"\nSentiment:  {label_display}")
    print(f"Confidence: {result['confidence']:.1f}%")

    bar_length = int(result['confidence'] / 2)
    bar = "=" * bar_length + "-" * (50 - bar_length)
    print(f"    [{bar}]")

    print(f"Reason: {result['reason']}")

    if result['escalate']:
        print("ESCALATE: Yes - Low confidence, needs human review")
    else:
        print("ESCALATE: No - High confidence")

    print(f"Method: {result['method'].upper()}")
    print("-" * 80)


def run_demo():
    """Run the interactive demo."""
    print_header()

    classifier = get_classifier()

    ai_available = config.USE_AI_MODEL and classifier.ai_classifier.is_available()
    if ai_available:
        print("[SUCCESS] AI Model: ENABLED (Hugging Face DistilBERT)")
    else:
        print("[INFO] AI Model: DISABLED (Using rule-based fallback)")

    print(f"[INFO] Confidence Threshold: {config.CONFIDENCE_THRESHOLD}%")
    print("\n" + "=" * 80)

    examples = {
        "Positive Feedback": [
            "The library staff were incredibly helpful with my research.",
            "I love how quiet and comfortable the study spaces are.",
            "Great selection of academic journals — very impressed.",
        ],
        "Neutral Feedback": [
            "The library is generally okay for studying.",
            "I think the opening hours could be extended on weekends.",
            "The catalogue works fine but could be more intuitive.",
        ],
        "Negative Feedback": [
            "The computers are always broken and extremely slow.",
            "Very disappointed — the book I reserved was not available.",
            "The Wi-Fi keeps disconnecting during important sessions.",
        ],
        "Ambiguous Cases": [
            "The library is okay but could be better.",
            "Sometimes the staff are helpful, sometimes not.",
            "I noticed the periodicals section hasn't been updated.",
        ]
    }

    for category, texts in examples.items():
        print(f"\n{'='*80}")
        print(f"  {category.upper()}")
        print(f"{'='*80}")

        for text in texts:
            time.sleep(0.5)
            result = classifier.classify_with_escalation(text)
            print_classification(text, result)

            if texts.index(text) < len(texts) - 1:
                input("\nPress Enter for next example...")

    print(f"\n{'='*80}")
    print("  INTERACTIVE MODE")
    print(f"{'='*80}")
    print("\nNow try your own library feedback! (Type 'quit' to exit)\n")

    while True:
        try:
            text = input("\nEnter feedback to analyse: ").strip()

            if not text:
                continue

            if text.lower() in ['quit', 'exit', 'q']:
                print("\nThanks for trying the demo!\n")
                break

            result = classifier.classify_with_escalation(text)
            print_classification(text, result)

        except (KeyboardInterrupt, EOFError):
            print("\n\nThanks for trying the demo!\n")
            break

    print("\n" + "=" * 80)
    print("  DEMO SUMMARY")
    print("=" * 80)
    print("\n[SUCCESS] Demonstrated positive, neutral, and negative sentiment classification")
    print("[SUCCESS] Showed confidence scoring and escalation logic")
    print("\nFor more information:")
    print("   - View API docs: http://localhost:8000/docs")
    print("   - Try web demo: http://localhost:8000/static/index.html")
    print("   - Run evaluation: python scripts/evaluate_model.py")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    run_demo()

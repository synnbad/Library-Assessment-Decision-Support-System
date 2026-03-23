"""
Download and prepare public datasets for testing.

This script fetches real-world datasets from the internet and converts them
to our format for testing the library feedback sentiment classifier.
"""
import json
import requests
from pathlib import Path
from typing import List, Dict
from src.dataset import load_dataset, save_dataset


def download_mixed_dataset() -> List[Dict]:
    """
    Create a mixed library feedback dataset from curated examples.

    Returns:
        List of examples in our format with positive/neutral/negative labels.
    """
    print("Creating mixed library feedback dataset...")

    positive_examples = [
        ("The library staff were incredibly helpful when I needed research assistance.", "positive"),
        ("I love how quiet and comfortable the study spaces are.", "positive"),
        ("The online catalogue is easy to use and well organised.", "positive"),
        ("Really appreciate the extended opening hours during exam season.", "positive"),
        ("The librarians are always friendly and knowledgeable.", "positive"),
        ("Great selection of academic journals and e-books available.", "positive"),
        ("The new group study rooms are fantastic — exactly what we needed.", "positive"),
        ("I found all the resources I needed for my dissertation. Very impressed.", "positive"),
        ("The self-checkout system is quick and convenient.", "positive"),
        ("Excellent printing facilities and very affordable rates.", "positive"),
        ("The library is always clean and well maintained.", "positive"),
        ("Staff helped me locate a rare book I needed. Outstanding service.", "positive"),
        ("The interlibrary loan service is brilliant — got my book within two days.", "positive"),
        ("Really enjoy studying here. The atmosphere is perfect for concentration.", "positive"),
        ("The digital resources available are comprehensive and up to date.", "positive"),
    ]

    neutral_examples = [
        ("The library is generally okay for studying.", "neutral"),
        ("I think the opening hours could be extended on weekends.", "neutral"),
        ("The collection is decent but could use more recent editions.", "neutral"),
        ("It would be nice to have more power outlets near the study desks.", "neutral"),
        ("The library is fine for most of my needs.", "neutral"),
        ("Sometimes the Wi-Fi is a bit slow but it usually works.", "neutral"),
        ("I noticed the periodicals section hasn't been updated in a while.", "neutral"),
        ("The booking system for study rooms is straightforward enough.", "neutral"),
        ("Overall the library meets my basic requirements.", "neutral"),
        ("The catalogue could be more intuitive but it gets the job done.", "neutral"),
        ("Maybe more seating options would help during busy periods.", "neutral"),
        ("The library is adequate for undergraduate research.", "neutral"),
        ("I feel the signage could be clearer to help new students navigate.", "neutral"),
        ("The printing service works but the queue can be long at peak times.", "neutral"),
        ("The library is okay, though I wish there were more silent study zones.", "neutral"),
    ]

    negative_examples = [
        ("The library is always too noisy to study in.", "negative"),
        ("Very disappointed — the book I reserved was not available when I arrived.", "negative"),
        ("The computers are outdated and extremely slow.", "negative"),
        ("Staff were unhelpful and dismissive when I asked for assistance.", "negative"),
        ("The library closes too early and I can never finish my work.", "negative"),
        ("Extremely frustrated with the overdue fine system — it is unreasonable.", "negative"),
        ("The Wi-Fi is terrible and keeps disconnecting during important sessions.", "negative"),
        ("There are never enough study spaces during exam period. Very stressful.", "negative"),
        ("The journal collection is badly out of date and missing key titles.", "negative"),
        ("I waited over a week for an interlibrary loan with no updates.", "negative"),
        ("The toilets near the reading room are always dirty and unpleasant.", "negative"),
        ("The self-checkout machines are constantly broken.", "negative"),
        ("Really unhappy with how long it takes to get a response from library support.", "negative"),
        ("The group study rooms are always booked and impossible to access.", "negative"),
        ("The library catalogue is confusing and hard to navigate.", "negative"),
    ]

    all_examples = positive_examples + neutral_examples + negative_examples
    examples = [{'text': text, 'label': label} for text, label in all_examples]

    print(f"Created {len(examples)} examples")
    return examples


def classify_heuristic(text: str) -> str:
    """
    Simple heuristic to classify library feedback when labels aren't provided.

    Args:
        text: Text to classify

    Returns:
        Label: 'positive', 'neutral', or 'negative'
    """
    text_lower = text.lower()

    negative_words = [
        'terrible', 'awful', 'bad', 'worst', 'broken', 'hate',
        'disappointed', 'frustrat', 'noisy', 'dirty', 'slow',
        'unhelpful', 'rude', 'outdated', 'never', 'always broken'
    ]
    if any(word in text_lower for word in negative_words):
        return 'negative'

    positive_words = [
        'great', 'excellent', 'helpful', 'love', 'fantastic', 'wonderful',
        'friendly', 'clean', 'quiet', 'comfortable', 'impressed', 'brilliant'
    ]
    if any(word in text_lower for word in positive_words):
        return 'positive'

    return 'neutral'


def main():
    """Main function to download and save datasets."""
    print("=" * 80)
    print("LIBRARY FEEDBACK DATASET BUILDER")
    print("=" * 80)

    print("\nCreating library feedback dataset...")
    dataset = download_mixed_dataset()

    if dataset:
        save_dataset(dataset, "data/raw/library_feedback.json")

        from src.dataset import get_label_distribution, validate_dataset
        print("\nDataset Statistics:")
        distribution = get_label_distribution(dataset)
        for label, count in distribution.items():
            print(f"   {label.capitalize()}: {count}")

        if validate_dataset(dataset):
            print("\nDataset validated successfully!")
            print(f"\nDataset saved to: data/raw/library_feedback.json")
            print(f"Total examples: {len(dataset)}")

            print("\nSample Examples:")
            for i, example in enumerate(dataset[:3], 1):
                print(f"\n   {i}. [{example['label'].upper()}]")
                print(f"      \"{example['text'][:80]}\"")

            print("\n" + "=" * 80)
            print("Dataset ready for evaluation!")
            print("\nRun: python scripts/evaluate_model.py")
            print("=" * 80)
        else:
            print("\nERROR: Dataset validation failed")
    else:
        print("\nERROR: Failed to create dataset")


if __name__ == "__main__":
    main()

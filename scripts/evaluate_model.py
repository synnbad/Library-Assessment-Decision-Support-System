"""
Evaluation script for testing classifier accuracy on datasets.

This script loads a dataset and evaluates the classifier's performance,
providing detailed accuracy metrics and confusion analysis.
"""
import json
from typing import Dict, List
from collections import defaultdict
from pathlib import Path
from src.modeling.predict import get_classifier


class ClassifierEvaluator:
    """Evaluates classifier performance on test datasets."""
    
    def __init__(self):
        """Initialize the evaluator with classifier."""
        self.classifier = get_classifier()
    
    def load_dataset(self, filepath: str) -> List[Dict]:
        """Load dataset from JSON file."""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def evaluate(self, dataset: List[Dict]) -> Dict:
        """
        Evaluate classifier on a dataset.
        
        Args:
            dataset: List of examples with 'text' and 'label' fields
            
        Returns:
            Dictionary containing evaluation metrics
        """
        results = {
            'total': 0,
            'correct': 0,
            'accuracy': 0.0,
            'by_label': {},
            'confusion_matrix': defaultdict(lambda: defaultdict(int)),
            'escalations': 0,
            'avg_confidence': 0.0,
            'method_stats': {'ai': 0, 'rules': 0}
        }
        
        predictions = []
        total_confidence = 0.0
        
        print("\nEvaluating classifier on dataset...")
        print("=" * 80)
        
        for i, example in enumerate(dataset, 1):
            text = example['text']
            true_label = example['label']
            
            # Classify the text
            classification = self.classifier.classify_with_escalation(text)
            predicted_label = classification['label']
            confidence = classification['confidence']
            method = classification['method']
            
            # Track results
            results['total'] += 1
            results['method_stats'][method] += 1
            total_confidence += confidence
            
            if classification['escalate']:
                results['escalations'] += 1
            
            is_correct = predicted_label == true_label
            if is_correct:
                results['correct'] += 1
            
            # Update confusion matrix
            results['confusion_matrix'][true_label][predicted_label] += 1
            
            # Track per-label accuracy
            if true_label not in results['by_label']:
                results['by_label'][true_label] = {'correct': 0, 'total': 0}
            
            results['by_label'][true_label]['total'] += 1
            if is_correct:
                results['by_label'][true_label]['correct'] += 1
            
            # Store prediction for detailed analysis
            predictions.append({
                'text': text,
                'true_label': true_label,
                'predicted_label': predicted_label,
                'confidence': confidence,
                'correct': is_correct,
                'reason': classification['reason'],
                'method': method
            })
            
            # Print progress
            if i % 10 == 0:
                print(f"Processed {i}/{len(dataset)} examples...")
        
        # Calculate final metrics
        if results['total'] > 0:
            results['accuracy'] = (results['correct'] / results['total']) * 100
            results['avg_confidence'] = total_confidence / results['total']
        
        results['predictions'] = predictions
        
        return results
    
    def print_report(self, results: Dict):
        """
        Print a detailed evaluation report.
        
        Args:
            results: Evaluation results from evaluate()
        """
        print("\n" + "=" * 80)
        print("CLASSIFICATION EVALUATION REPORT")
        print("=" * 80)
        
        # Overall accuracy
        print(f"\n[PERFORMANCE] Overall Performance:")
        print(f"   Total Examples: {results['total']}")
        print(f"   Correct: {results['correct']}")
        print(f"   Accuracy: {results['accuracy']:.2f}%")
        print(f"   Average Confidence: {results['avg_confidence']:.2f}%")
        print(f"   Escalations: {results['escalations']} ({(results['escalations']/results['total']*100):.1f}%)")
        
        # Method breakdown
        print(f"\n[METHOD] Classification Method:")
        print(f"   AI: {results['method_stats']['ai']} ({(results['method_stats']['ai']/results['total']*100):.1f}%)")
        print(f"   Rules: {results['method_stats']['rules']} ({(results['method_stats']['rules']/results['total']*100):.1f}%)")
        
        # Per-label accuracy
        print(f"\n[ACCURACY] Accuracy by Label:")
        for label, stats in results['by_label'].items():
            label_accuracy = (stats['correct'] / stats['total']) * 100
            print(f"   {label.capitalize()}: {stats['correct']}/{stats['total']} ({label_accuracy:.2f}%)")
        
        # Confusion matrix
        print(f"\n[CONFUSION MATRIX] Confusion Matrix:")
        print("   " + " " * 12 + "Predicted →")
        print("   " + " " * 12 + "+       N       -")  # Positive, Neutral, Negative
        labels = ['positive', 'neutral', 'negative']
        label_abbrev = {'positive': '+', 'neutral': 'N', 'negative': '-'}

        for true_label in labels:
            row = f"   True {label_abbrev[true_label]} ({true_label[:4]})  "
            for pred_label in labels:
                count = results['confusion_matrix'][true_label][pred_label]
                row += f"{count:4}    "
            print(row)
        
        # Success criteria
        print(f"\n[SUCCESS CRITERIA] Success Criteria:")
        method = 'AI' if results['method_stats']['ai'] > 0 else 'Rules'
        target = 85 if method == 'AI' else 70
        
        if results['accuracy'] >= target:
            print(f"   [PASS] Met {method} accuracy target ({target}%)")
        else:
            print(f"   [FAIL] Below {method} accuracy target ({target}%)")
            print(f"   Gap: {target - results['accuracy']:.2f}%")
        
        # Show some errors for analysis
        print(f"\n[ERRORS] Sample Misclassifications:")
        errors = [p for p in results['predictions'] if not p['correct']]
        
        if errors:
            for i, error in enumerate(errors[:5], 1):  # Show first 5 errors
                print(f"\n   {i}. Text: \"{error['text'][:60]}...\"")
                print(f"      True: {error['true_label']} | Predicted: {error['predicted_label']}")
                print(f"      Confidence: {error['confidence']:.1f}% | Reason: {error['reason']}")
        else:
            print("   [SUCCESS] No misclassifications! Perfect score!")
        
        print("\n" + "=" * 80)


def main():
    """Main function to run evaluation."""
    print("=" * 80)
    print("LIBRARY FEEDBACK SENTIMENT ANALYSIS - CLASSIFIER EVALUATION")
    print("=" * 80)

    evaluator = ClassifierEvaluator()

    import os
    data_dir = Path("data/raw")
    available_datasets = []

    if data_dir.exists():
        for file in data_dir.glob("*.json"):
            available_datasets.append(file.stem)

    if not available_datasets:
        available_datasets = ["library_feedback"]

    print("\nAvailable datasets:")
    for i, name in enumerate(available_datasets, 1):
        print(f"   {i}. {name}")

    dataset_name = available_datasets[0]
    if len(available_datasets) > 1:
        try:
            choice = input(f"\nSelect dataset (1-{len(available_datasets)}, default=1): ").strip()
            if choice and choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(available_datasets):
                    dataset_name = available_datasets[idx]
        except (KeyboardInterrupt, EOFError):
            print(f"\n[INFO] Using default ({dataset_name})")

    print(f"\nLoading dataset '{dataset_name}'...")
    try:
        dataset_path = f"data/raw/{dataset_name}.json"
        dataset = evaluator.load_dataset(dataset_path)
        print(f"   Loaded {len(dataset)} examples")

        distribution = {}
        for example in dataset:
            label = example.get('label', 'unknown')
            distribution[label] = distribution.get(label, 0) + 1

        print(f"\nDataset Distribution:")
        for label, count in distribution.items():
            print(f"   {label.capitalize()}: {count}")

        print("\n[SUCCESS] Dataset loaded successfully")

    except Exception as e:
        print(f"\n[ERROR] Error loading dataset: {e}")
        return

    try:
        results = evaluator.evaluate(dataset)
        evaluator.print_report(results)

    except Exception as e:
        print(f"\n[ERROR] Error during evaluation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

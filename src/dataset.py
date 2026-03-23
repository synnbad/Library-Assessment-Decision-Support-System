"""
Dataset loading and management utilities.

This module provides functions for loading, downloading, and managing
datasets used for sentiment analysis classification.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def load_dataset(filepath: str) -> List[Dict]:
    """
    Load a dataset from a JSON file.
    
    Args:
        filepath: Path to the JSON dataset file
        
    Returns:
        List of examples, each with 'text' and 'label' keys
        
    Raises:
        FileNotFoundError: If the dataset file doesn't exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    path = Path(filepath)
    
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {filepath}")
    
    logger.info(f"Loading dataset from {filepath}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} examples from dataset")
    
    return data


def save_dataset(data: List[Dict], filepath: str):
    """
    Save a dataset to a JSON file.
    
    Args:
        data: List of examples to save
        filepath: Path where to save the JSON file
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving {len(data)} examples to {filepath}")
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Dataset saved successfully")


def get_label_distribution(dataset: List[Dict]) -> Dict[str, int]:
    """
    Calculate the distribution of labels in a dataset.
    
    Args:
        dataset: List of examples with 'label' key
        
    Returns:
        Dictionary mapping labels to counts
    """
    distribution = {}
    
    for example in dataset:
        label = example.get('label', 'unknown')
        distribution[label] = distribution.get(label, 0) + 1
    
    return distribution


def validate_dataset(dataset: List[Dict]) -> bool:
    """
    Validate that a dataset has the correct format.
    
    Args:
        dataset: List of examples to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(dataset, list):
        logger.error("Dataset must be a list")
        return False
    
    for i, example in enumerate(dataset):
        if not isinstance(example, dict):
            logger.error(f"Example {i} is not a dictionary")
            return False
        
        if 'text' not in example:
            logger.error(f"Example {i} missing 'text' field")
            return False
        
        if 'label' not in example:
            logger.error(f"Example {i} missing 'label' field")
            return False
        
        if example['label'] not in ['positive', 'neutral', 'negative']:
            logger.warning(f"Example {i} has unexpected label: {example['label']}")
    
    logger.info(f"Dataset validation passed: {len(dataset)} examples")
    return True


def create_train_test_split(
    dataset: List[Dict],
    test_size: float = 0.2,
    random_seed: int = 42
) -> tuple[List[Dict], List[Dict]]:
    """
    Split dataset into training and testing sets.
    
    Args:
        dataset: List of examples to split
        test_size: Proportion of dataset to use for testing (0.0 to 1.0)
        random_seed: Random seed for reproducibility
        
    Returns:
        Tuple of (train_data, test_data)
    """
    import random
    
    # Set random seed for reproducibility
    random.seed(random_seed)
    
    # Shuffle dataset
    shuffled = dataset.copy()
    random.shuffle(shuffled)
    
    # Calculate split point
    split_idx = int(len(shuffled) * (1 - test_size))
    
    train_data = shuffled[:split_idx]
    test_data = shuffled[split_idx:]
    
    logger.info(f"Split dataset: {len(train_data)} train, {len(test_data)} test")
    
    return train_data, test_data


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Load a dataset
    try:
        dataset = load_dataset("data/raw/public_mixed.json")
        
        # Show distribution
        distribution = get_label_distribution(dataset)
        print("\nLabel Distribution:")
        for label, count in distribution.items():
            print(f"  {label}: {count}")
        
        # Validate
        is_valid = validate_dataset(dataset)
        print(f"\nDataset valid: {is_valid}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")

"""
PII Detection and Redaction Module

This module provides comprehensive PII detection and redaction capabilities to
maintain FERPA compliance and protect student privacy in all system outputs.

Key Features:
- Regex-based PII detection (email, phone, SSN, student ID)
- Automatic redaction with placeholders
- Batch processing for multiple texts
- PII flagging without redaction
- Safety verification for outputs
- Human-readable PII summaries
- Configurable patterns via Settings

Supported PII Types:
- Email addresses: user@example.com
- Phone numbers: 555-123-4567 (various formats)
- Social Security Numbers: 123-45-6789
- Student IDs: Configurable pattern
- Street addresses: 123 Main Street, 456 Oak Avenue, etc.

Redaction Placeholders:
- [EMAIL] - Replaces email addresses
- [PHONE] - Replaces phone numbers
- [SSN] - Replaces Social Security Numbers
- [STUDENT_ID] - Replaces student identifiers
- [ADDRESS] - Replaces street addresses

Module Functions:
- detect_pii(): Find PII instances in text
- redact_pii(): Replace PII with placeholders
- flag_pii(): Check for PII without redacting
- redact_pii_from_list(): Batch redaction for multiple texts
- is_safe_output(): Verify text contains no PII
- get_pii_summary(): Generate human-readable PII summary

Requirements Implemented:
- 6.5: Detect and redact PII in outputs
- FERPA compliance through privacy protection

Configuration (config/settings.py):
- PII_PATTERNS: Dictionary of regex patterns for each PII type
  - email: Email address pattern
  - phone: Phone number pattern (various formats)
  - ssn: Social Security Number pattern
  - student_id: Configurable student ID pattern

Usage in System:
- Applied to all LLM-generated outputs (RAG answers, narratives)
- Applied to report content before export
- Applied to analysis summaries
- Applied to representative quotes in themes
- Applied to any user-facing text that may contain PII

Usage Example:
    from modules.pii_detector import redact_pii, detect_pii, is_safe_output
    
    # Detect PII
    text = "Contact me at john@example.com or 555-123-4567"
    detected = detect_pii(text)
    print(detected)  # {'email': ['john@example.com'], 'phone': ['555-123-4567']}
    
    # Redact PII
    redacted, counts = redact_pii(text)
    print(redacted)  # "Contact me at [EMAIL] or [PHONE]"
    print(counts)    # {'email': 1, 'phone': 1}
    
    # Check if safe
    safe_text = "This text contains no PII"
    if is_safe_output(safe_text):
        print("Safe to display")
    
    # Batch redaction
    texts = ["Email: user1@test.com", "Phone: 555-0000"]
    redacted_texts, total_counts = redact_pii_from_list(texts)

Regex Patterns:
- Email: \b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b
- Phone: \b\d{3}[-.]?\d{3}[-.]?\d{4}\b
- SSN: \b\d{3}-\d{2}-\d{4}\b

Custom Patterns:
- Patterns can be customized via Settings.PII_PATTERNS
- Pass custom patterns dict to any function
- Useful for institution-specific identifiers

Author: FERPA-Compliant RAG DSS Team
"""

import re
from typing import Dict, List, Tuple
from config.settings import Settings


def detect_pii(text: str, patterns: Dict[str, str] = None) -> Dict[str, List[str]]:
    """
    Detect PII in text using regex patterns.
    
    Args:
        text: Text to scan for PII
        patterns: Optional custom patterns dict. If None, uses Settings.PII_PATTERNS
        
    Returns:
        Dictionary mapping PII type to list of detected instances
        Example: {"email": ["user@example.com"], "phone": ["555-123-4567"]}
    """
    if patterns is None:
        patterns = Settings.PII_PATTERNS
    
    detected = {}
    
    for pii_type, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            detected[pii_type] = matches
    
    return detected


def redact_pii(text: str, patterns: Dict[str, str] = None) -> Tuple[str, Dict[str, int]]:
    """
    Redact PII from text by replacing with placeholders.
    
    Args:
        text: Text to redact PII from
        patterns: Optional custom patterns dict. If None, uses Settings.PII_PATTERNS
        
    Returns:
        Tuple of (redacted_text, pii_counts)
        - redacted_text: Text with PII replaced by placeholders like [EMAIL], [PHONE], [SSN]
        - pii_counts: Dictionary mapping PII type to count of redactions
        
    Example:
        >>> text = "Contact me at john@example.com or 555-123-4567"
        >>> redacted, counts = redact_pii(text)
        >>> print(redacted)
        "Contact me at [EMAIL] or [PHONE]"
        >>> print(counts)
        {"email": 1, "phone": 1}
    """
    if patterns is None:
        patterns = Settings.PII_PATTERNS
    
    redacted_text = text
    pii_counts = {}
    
    # Define placeholder mapping
    placeholders = {
        "email": "[EMAIL]",
        "phone": "[PHONE]",
        "ssn": "[SSN]",
        "student_id": "[STUDENT_ID]",
        "address": "[ADDRESS]"
    }
    
    # Redact each PII type
    for pii_type, pattern in patterns.items():
        matches = re.findall(pattern, redacted_text)
        if matches:
            pii_counts[pii_type] = len(matches)
            placeholder = placeholders.get(pii_type, f"[{pii_type.upper()}]")
            redacted_text = re.sub(pattern, placeholder, redacted_text)
    
    return redacted_text, pii_counts


def flag_pii(text: str, patterns: Dict[str, str] = None) -> Tuple[str, bool, List[str]]:
    """
    Flag text containing PII without redacting.
    
    Args:
        text: Text to check for PII
        patterns: Optional custom patterns dict. If None, uses Settings.PII_PATTERNS
        
    Returns:
        Tuple of (text, has_pii, pii_types)
        - text: Original text unchanged
        - has_pii: Boolean indicating if PII was detected
        - pii_types: List of PII types detected (e.g., ["email", "phone"])
    """
    if patterns is None:
        patterns = Settings.PII_PATTERNS
    
    detected = detect_pii(text, patterns)
    has_pii = len(detected) > 0
    pii_types = list(detected.keys())
    
    return text, has_pii, pii_types


def redact_pii_from_list(texts: List[str], patterns: Dict[str, str] = None) -> Tuple[List[str], Dict[str, int]]:
    """
    Redact PII from a list of texts.
    
    Args:
        texts: List of texts to redact PII from
        patterns: Optional custom patterns dict. If None, uses Settings.PII_PATTERNS
        
    Returns:
        Tuple of (redacted_texts, total_pii_counts)
        - redacted_texts: List of texts with PII redacted
        - total_pii_counts: Dictionary mapping PII type to total count across all texts
    """
    redacted_texts = []
    total_counts = {}
    
    for text in texts:
        redacted, counts = redact_pii(text, patterns)
        redacted_texts.append(redacted)
        
        # Aggregate counts
        for pii_type, count in counts.items():
            total_counts[pii_type] = total_counts.get(pii_type, 0) + count
    
    return redacted_texts, total_counts


def is_safe_output(text: str, patterns: Dict[str, str] = None) -> bool:
    """
    Check if text is safe to display (contains no PII).
    
    Args:
        text: Text to check
        patterns: Optional custom patterns dict. If None, uses Settings.PII_PATTERNS
        
    Returns:
        True if text contains no PII, False otherwise
    """
    detected = detect_pii(text, patterns)
    return len(detected) == 0


def get_pii_summary(text: str, patterns: Dict[str, str] = None) -> str:
    """
    Generate a human-readable summary of PII detected in text.
    
    Args:
        text: Text to analyze
        patterns: Optional custom patterns dict. If None, uses Settings.PII_PATTERNS
        
    Returns:
        Human-readable summary string
        
    Example:
        "PII detected: 2 email addresses, 1 phone number"
    """
    detected = detect_pii(text, patterns)
    
    if not detected:
        return "No PII detected"
    
    summary_parts = []
    for pii_type, matches in detected.items():
        count = len(matches)
        type_name = pii_type.replace("_", " ")
        if pii_type == "email":
            plural = "s" if count > 1 else ""
        else:
            plural = "s" if count > 1 else ""
        summary_parts.append(f"{count} {type_name}{plural}")
    
    return f"PII detected: {', '.join(summary_parts)}"

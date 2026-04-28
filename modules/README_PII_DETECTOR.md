# PII Detection and Redaction Module

## Overview

The `pii_detector.py` module provides comprehensive PII (Personally Identifiable Information) detection and redaction capabilities to support privacy-conscious local processing and protect student privacy in the Library Assessment Decision Support System.

## Features

- **Email Detection**: Detects email addresses in various formats
- **Phone Number Detection**: Detects phone numbers with dashes, dots, or no separators
- **SSN Detection**: Detects Social Security Numbers in XXX-XX-XXXX format
- **Extensible Patterns**: Support for custom PII patterns (e.g., student IDs)
- **Batch Processing**: Process multiple texts efficiently
- **Safety Checking**: Verify if text is safe to display

## Functions

### `detect_pii(text, patterns=None)`

Detect PII in text using regex patterns.

**Parameters:**
- `text` (str): Text to scan for PII
- `patterns` (dict, optional): Custom patterns dict. Defaults to Settings.PII_PATTERNS

**Returns:**
- dict: Mapping of PII type to list of detected instances

**Example:**
```python
from modules.pii_detector import detect_pii

text = "Contact me at john@example.com or 555-123-4567"
detected = detect_pii(text)
# Returns: {"email": ["john@example.com"], "phone": ["555-123-4567"]}
```

### `redact_pii(text, patterns=None)`

Redact PII from text by replacing with placeholders.

**Parameters:**
- `text` (str): Text to redact PII from
- `patterns` (dict, optional): Custom patterns dict

**Returns:**
- tuple: (redacted_text, pii_counts)
  - `redacted_text` (str): Text with PII replaced by placeholders
  - `pii_counts` (dict): Count of redactions by type

**Example:**
```python
from modules.pii_detector import redact_pii

text = "Contact me at john@example.com or 555-123-4567"
redacted, counts = redact_pii(text)
# redacted: "Contact me at [EMAIL] or [PHONE]"
# counts: {"email": 1, "phone": 1}
```

### `flag_pii(text, patterns=None)`

Flag text containing PII without redacting.

**Parameters:**
- `text` (str): Text to check for PII
- `patterns` (dict, optional): Custom patterns dict

**Returns:**
- tuple: (text, has_pii, pii_types)
  - `text` (str): Original text unchanged
  - `has_pii` (bool): Whether PII was detected
  - `pii_types` (list): List of PII types detected

**Example:**
```python
from modules.pii_detector import flag_pii

text = "Contact john@example.com"
original, has_pii, types = flag_pii(text)
# has_pii: True
# types: ["email"]
```

### `redact_pii_from_list(texts, patterns=None)`

Redact PII from a list of texts.

**Parameters:**
- `texts` (list): List of texts to redact
- `patterns` (dict, optional): Custom patterns dict

**Returns:**
- tuple: (redacted_texts, total_pii_counts)
  - `redacted_texts` (list): List of redacted texts
  - `total_pii_counts` (dict): Aggregated counts across all texts

**Example:**
```python
from modules.pii_detector import redact_pii_from_list

texts = [
    "Email alice@test.com",
    "Call 555-123-4567"
]
redacted_list, counts = redact_pii_from_list(texts)
# redacted_list: ["Email [EMAIL]", "Call [PHONE]"]
# counts: {"email": 1, "phone": 1}
```

### `is_safe_output(text, patterns=None)`

Check if text is safe to display (contains no PII).

**Parameters:**
- `text` (str): Text to check
- `patterns` (dict, optional): Custom patterns dict

**Returns:**
- bool: True if text contains no PII, False otherwise

**Example:**
```python
from modules.pii_detector import is_safe_output

safe_text = "The library is open today"
unsafe_text = "Email john@example.com"

is_safe_output(safe_text)    # Returns: True
is_safe_output(unsafe_text)  # Returns: False
```

### `get_pii_summary(text, patterns=None)`

Generate a human-readable summary of PII detected.

**Parameters:**
- `text` (str): Text to analyze
- `patterns` (dict, optional): Custom patterns dict

**Returns:**
- str: Human-readable summary

**Example:**
```python
from modules.pii_detector import get_pii_summary

text = "Email john@example.com or call 555-123-4567"
summary = get_pii_summary(text)
# Returns: "PII detected: 1 email, 1 phone"
```

## Configuration

PII patterns are configured in `config/settings.py`:

```python
PII_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b'
}
```

### Custom Patterns

You can add custom patterns for institution-specific identifiers:

```python
custom_patterns = {
    "student_id": r'\bSTU\d{6}\b',
    "employee_id": r'\bEMP\d{5}\b'
}

detected = detect_pii(text, patterns=custom_patterns)
```

## Placeholders

The following placeholders are used for redaction:

- `[EMAIL]` - Email addresses
- `[PHONE]` - Phone numbers
- `[SSN]` - Social Security Numbers
- `[STUDENT_ID]` - Student IDs (if custom pattern added)

## Edge Cases

### False Positives

The module may detect some non-PII as PII (e.g., reference numbers that look like SSNs). This is intentional - it's better to over-redact than under-redact for privacy protection.

### Unicode Support

The module handles unicode characters in text, though PII patterns are designed for ASCII formats.

### Multiline Text

PII detection works across multiple lines and handles various text formats.

## Testing

Comprehensive unit tests are available in `tests/unit/test_pii_detector.py`:

```bash
python -m pytest tests/unit/test_pii_detector.py -v
```

## Demo

Run the demo script to see all features in action:

```bash
python examples/pii_detection_demo.py
```

## Integration

The PII detector is designed to integrate with:

- Query interface (redact PII in answers)
- Report generation (redact PII in reports)
- Analysis summaries (redact PII in qualitative analysis)

See task 12.2 for integration details.

## Requirements

Validates Requirement 6.5:
> IF PII is detected in outputs, THEN THE Assessment_Assistant SHALL redact or flag it before display

## License

Part of the Library Assessment Decision Support System.

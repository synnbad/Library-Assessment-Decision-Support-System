"""
PII Detection and Redaction Demo

This script demonstrates the PII detection and redaction capabilities
of the Library Assessment Decision Support System.
"""

from modules.pii_detector import (
    detect_pii,
    redact_pii,
    flag_pii,
    is_safe_output,
    get_pii_summary
)


def demo_basic_detection():
    """Demonstrate basic PII detection."""
    print("=" * 60)
    print("DEMO 1: Basic PII Detection")
    print("=" * 60)
    
    text = """
    Student feedback: "I really enjoyed the library workshop!
    If you have questions, email me at student123@university.edu
    or call my cell at 555-867-5309. My SSN is 123-45-6789."
    """
    
    print("\nOriginal text:")
    print(text)
    
    detected = detect_pii(text)
    print("\nDetected PII:")
    for pii_type, instances in detected.items():
        print(f"  {pii_type}: {instances}")
    
    print("\nSummary:", get_pii_summary(text))


def demo_redaction():
    """Demonstrate PII redaction."""
    print("\n" + "=" * 60)
    print("DEMO 2: PII Redaction")
    print("=" * 60)
    
    text = "Contact the librarian at help@library.edu or call 555-123-4567"
    
    print("\nOriginal text:")
    print(f"  {text}")
    
    redacted, counts = redact_pii(text)
    
    print("\nRedacted text:")
    print(f"  {redacted}")
    
    print("\nRedaction counts:")
    for pii_type, count in counts.items():
        print(f"  {pii_type}: {count}")


def demo_safety_check():
    """Demonstrate safety checking."""
    print("\n" + "=" * 60)
    print("DEMO 3: Safety Checking")
    print("=" * 60)
    
    safe_text = "The library is open Monday through Friday."
    unsafe_text = "Email me at john@example.com for details."
    
    print("\nChecking safe text:")
    print(f"  Text: {safe_text}")
    print(f"  Is safe: {is_safe_output(safe_text)}")
    
    print("\nChecking unsafe text:")
    print(f"  Text: {unsafe_text}")
    print(f"  Is safe: {is_safe_output(unsafe_text)}")


def demo_flagging():
    """Demonstrate PII flagging."""
    print("\n" + "=" * 60)
    print("DEMO 4: PII Flagging")
    print("=" * 60)
    
    text = "Student survey response: Contact me at student@edu.org"
    
    original, has_pii, pii_types = flag_pii(text)
    
    print(f"\nText: {original}")
    print(f"Contains PII: {has_pii}")
    if has_pii:
        print(f"PII types detected: {', '.join(pii_types)}")


def demo_batch_processing():
    """Demonstrate batch processing of multiple texts."""
    print("\n" + "=" * 60)
    print("DEMO 5: Batch Processing")
    print("=" * 60)
    
    from modules.pii_detector import redact_pii_from_list
    
    survey_responses = [
        "Great service! Email me at alice@test.com",
        "Call me at 555-111-2222 for follow-up",
        "The library hours are perfect for my schedule",
        "Contact: bob@example.org or 555-333-4444"
    ]
    
    print("\nOriginal responses:")
    for i, response in enumerate(survey_responses, 1):
        print(f"  {i}. {response}")
    
    redacted_responses, total_counts = redact_pii_from_list(survey_responses)
    
    print("\nRedacted responses:")
    for i, response in enumerate(redacted_responses, 1):
        print(f"  {i}. {response}")
    
    print("\nTotal PII redacted:")
    for pii_type, count in total_counts.items():
        print(f"  {pii_type}: {count}")


def main():
    """Run all demos."""
    print("\n")
    print("=" * 60)
    print(" " * 10 + "PII Detection & Redaction Demo")
    print(" " * 5 + "Library Assessment Decision Support System")
    print("=" * 60)
    
    demo_basic_detection()
    demo_redaction()
    demo_safety_check()
    demo_flagging()
    demo_batch_processing()
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

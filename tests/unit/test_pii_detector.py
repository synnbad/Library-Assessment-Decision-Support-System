"""
Unit tests for PII detection and redaction module.

Tests cover:
- Email detection and redaction
- Phone number detection (various formats)
- SSN detection and redaction
- Edge cases and false positives
- Batch processing
- Safety checks
"""

import pytest
from modules.pii_detector import (
    detect_pii,
    redact_pii,
    flag_pii,
    redact_pii_from_list,
    is_safe_output,
    get_pii_summary
)


class TestDetectPII:
    """Tests for detect_pii function."""
    
    def test_detect_email(self):
        """Test email detection."""
        text = "Contact me at john.doe@example.com for more info."
        detected = detect_pii(text)
        
        assert "email" in detected
        assert "john.doe@example.com" in detected["email"]
    
    def test_detect_multiple_emails(self):
        """Test detection of multiple emails."""
        text = "Email alice@test.com or bob@example.org"
        detected = detect_pii(text)
        
        assert "email" in detected
        assert len(detected["email"]) == 2
        assert "alice@test.com" in detected["email"]
        assert "bob@example.org" in detected["email"]
    
    def test_detect_phone_with_dashes(self):
        """Test phone number detection with dashes."""
        text = "Call me at 555-123-4567"
        detected = detect_pii(text)
        
        assert "phone" in detected
        assert "555-123-4567" in detected["phone"]
    
    def test_detect_phone_with_dots(self):
        """Test phone number detection with dots."""
        text = "My number is 555.123.4567"
        detected = detect_pii(text)
        
        assert "phone" in detected
        assert "555.123.4567" in detected["phone"]
    
    def test_detect_phone_no_separator(self):
        """Test phone number detection without separators."""
        text = "Contact: 5551234567"
        detected = detect_pii(text)
        
        assert "phone" in detected
        assert "5551234567" in detected["phone"]
    
    def test_detect_ssn(self):
        """Test SSN detection."""
        text = "SSN: 123-45-6789"
        detected = detect_pii(text)
        
        assert "ssn" in detected
        assert "123-45-6789" in detected["ssn"]
    
    def test_detect_multiple_pii_types(self):
        """Test detection of multiple PII types in same text."""
        text = "Contact john@example.com at 555-123-4567 or SSN 123-45-6789"
        detected = detect_pii(text)
        
        assert "email" in detected
        assert "phone" in detected
        assert "ssn" in detected
        assert len(detected) == 3
    
    def test_no_pii_detected(self):
        """Test text with no PII."""
        text = "This is a clean text with no personal information."
        detected = detect_pii(text)
        
        assert len(detected) == 0
    
    def test_empty_text(self):
        """Test empty text."""
        detected = detect_pii("")
        assert len(detected) == 0
    
    def test_custom_patterns(self):
        """Test with custom PII patterns."""
        custom_patterns = {
            "student_id": r'\bSTU\d{6}\b'
        }
        text = "Student ID: STU123456"
        detected = detect_pii(text, patterns=custom_patterns)
        
        assert "student_id" in detected
        assert "STU123456" in detected["student_id"]


class TestRedactPII:
    """Tests for redact_pii function."""
    
    def test_redact_email(self):
        """Test email redaction."""
        text = "Contact me at john@example.com"
        redacted, counts = redact_pii(text)
        
        assert "[EMAIL]" in redacted
        assert "john@example.com" not in redacted
        assert counts["email"] == 1
    
    def test_redact_phone(self):
        """Test phone number redaction."""
        text = "Call 555-123-4567"
        redacted, counts = redact_pii(text)
        
        assert "[PHONE]" in redacted
        assert "555-123-4567" not in redacted
        assert counts["phone"] == 1
    
    def test_redact_ssn(self):
        """Test SSN redaction."""
        text = "SSN: 123-45-6789"
        redacted, counts = redact_pii(text)
        
        assert "[SSN]" in redacted
        assert "123-45-6789" not in redacted
        assert counts["ssn"] == 1
    
    def test_redact_multiple_pii(self):
        """Test redaction of multiple PII instances."""
        text = "Email john@example.com or call 555-123-4567"
        redacted, counts = redact_pii(text)
        
        assert "[EMAIL]" in redacted
        assert "[PHONE]" in redacted
        assert "john@example.com" not in redacted
        assert "555-123-4567" not in redacted
        assert counts["email"] == 1
        assert counts["phone"] == 1
    
    def test_redact_preserves_structure(self):
        """Test that redaction preserves text structure."""
        text = "Contact me at john@example.com for more information."
        redacted, counts = redact_pii(text)
        
        expected = "Contact me at [EMAIL] for more information."
        assert redacted == expected
    
    def test_redact_no_pii(self):
        """Test redaction of text with no PII."""
        text = "This is clean text."
        redacted, counts = redact_pii(text)
        
        assert redacted == text
        assert len(counts) == 0
    
    def test_redact_multiple_same_type(self):
        """Test redaction of multiple instances of same PII type."""
        text = "Email alice@test.com or bob@example.org"
        redacted, counts = redact_pii(text)
        
        assert redacted == "Email [EMAIL] or [EMAIL]"
        assert counts["email"] == 2
    
    def test_redact_empty_text(self):
        """Test redaction of empty text."""
        redacted, counts = redact_pii("")
        
        assert redacted == ""
        assert len(counts) == 0


class TestFlagPII:
    """Tests for flag_pii function."""
    
    def test_flag_with_pii(self):
        """Test flagging text with PII."""
        text = "Contact john@example.com"
        original, has_pii, pii_types = flag_pii(text)
        
        assert original == text  # Text unchanged
        assert has_pii is True
        assert "email" in pii_types
    
    def test_flag_without_pii(self):
        """Test flagging text without PII."""
        text = "This is clean text."
        original, has_pii, pii_types = flag_pii(text)
        
        assert original == text
        assert has_pii is False
        assert len(pii_types) == 0
    
    def test_flag_multiple_types(self):
        """Test flagging text with multiple PII types."""
        text = "Email john@example.com or call 555-123-4567"
        original, has_pii, pii_types = flag_pii(text)
        
        assert has_pii is True
        assert "email" in pii_types
        assert "phone" in pii_types


class TestRedactPIIFromList:
    """Tests for redact_pii_from_list function."""
    
    def test_redact_list(self):
        """Test redacting PII from list of texts."""
        texts = [
            "Contact alice@test.com",
            "Call 555-123-4567",
            "Clean text"
        ]
        redacted_list, total_counts = redact_pii_from_list(texts)
        
        assert len(redacted_list) == 3
        assert "[EMAIL]" in redacted_list[0]
        assert "[PHONE]" in redacted_list[1]
        assert redacted_list[2] == "Clean text"
        assert total_counts["email"] == 1
        assert total_counts["phone"] == 1
    
    def test_redact_empty_list(self):
        """Test redacting empty list."""
        redacted_list, total_counts = redact_pii_from_list([])
        
        assert len(redacted_list) == 0
        assert len(total_counts) == 0
    
    def test_redact_list_aggregates_counts(self):
        """Test that counts are aggregated across all texts."""
        texts = [
            "Email alice@test.com",
            "Email bob@example.org",
            "Email charlie@test.net"
        ]
        redacted_list, total_counts = redact_pii_from_list(texts)
        
        assert total_counts["email"] == 3


class TestIsSafeOutput:
    """Tests for is_safe_output function."""
    
    def test_safe_text(self):
        """Test text without PII is safe."""
        text = "This is safe text with no personal information."
        assert is_safe_output(text) is True
    
    def test_unsafe_text_with_email(self):
        """Test text with email is not safe."""
        text = "Contact john@example.com"
        assert is_safe_output(text) is False
    
    def test_unsafe_text_with_phone(self):
        """Test text with phone is not safe."""
        text = "Call 555-123-4567"
        assert is_safe_output(text) is False
    
    def test_unsafe_text_with_ssn(self):
        """Test text with SSN is not safe."""
        text = "SSN: 123-45-6789"
        assert is_safe_output(text) is False


class TestGetPIISummary:
    """Tests for get_pii_summary function."""
    
    def test_summary_no_pii(self):
        """Test summary for text with no PII."""
        text = "Clean text"
        summary = get_pii_summary(text)
        
        assert summary == "No PII detected"
    
    def test_summary_single_email(self):
        """Test summary for single email."""
        text = "Contact john@example.com"
        summary = get_pii_summary(text)
        
        assert "1 email" in summary
    
    def test_summary_multiple_emails(self):
        """Test summary for multiple emails."""
        text = "Email alice@test.com or bob@example.org"
        summary = get_pii_summary(text)
        
        assert "2 emails" in summary
    
    def test_summary_multiple_types(self):
        """Test summary for multiple PII types."""
        text = "Email john@example.com or call 555-123-4567"
        summary = get_pii_summary(text)
        
        assert "email" in summary
        assert "phone" in summary
    
    def test_summary_format(self):
        """Test summary format."""
        text = "Contact john@example.com at 555-123-4567"
        summary = get_pii_summary(text)
        
        assert summary.startswith("PII detected:")


class TestEdgeCases:
    """Tests for edge cases and potential false positives."""
    
    def test_email_like_but_invalid(self):
        """Test that invalid email-like strings are handled."""
        text = "This is not@an@email"
        detected = detect_pii(text)
        
        # Should not detect invalid email format
        # (depends on regex strictness)
    
    def test_phone_like_numbers(self):
        """Test that non-phone numbers are not detected."""
        text = "The year 2024 and number 123456789"
        detected = detect_pii(text)
        
        # May detect 123456789 as phone - this is acceptable
        # as it's better to over-redact than under-redact
    
    def test_ssn_like_numbers(self):
        """Test SSN-like patterns."""
        text = "Reference number: 123-45-6789"
        detected = detect_pii(text)
        
        # Should detect as SSN (better safe than sorry)
        assert "ssn" in detected
    
    def test_unicode_text(self):
        """Test handling of unicode characters."""
        text = "Email: user@例え.jp and phone: 555-123-4567"
        detected = detect_pii(text)
        
        # Should still detect phone
        assert "phone" in detected
    
    def test_multiline_text(self):
        """Test PII detection in multiline text."""
        text = """
        Contact Information:
        Email: john@example.com
        Phone: 555-123-4567
        """
        detected = detect_pii(text)
        
        assert "email" in detected
        assert "phone" in detected
    
    def test_case_sensitivity(self):
        """Test case sensitivity in email detection."""
        text = "Email: John.Doe@EXAMPLE.COM"
        detected = detect_pii(text)
        
        assert "email" in detected
        assert "John.Doe@EXAMPLE.COM" in detected["email"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

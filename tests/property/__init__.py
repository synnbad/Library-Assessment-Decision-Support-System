"""
Property-Based Tests

This package contains property-based tests using the Hypothesis framework.
Property tests verify universal correctness properties across all valid inputs.

Test Configuration:
- Minimum 100 iterations per property test
- Each test references its design document property
- Tag format: # Feature: repo-rehabilitation, Property {number}: {property_text}

Properties Tested:
- Property 1: CSV round-trip preservation
- Property 2: Precision@k calculation correctness
- Property 3: Recall@k calculation correctness
- Property 4: MRR calculation correctness
"""

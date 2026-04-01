# Sample Test Data

This directory contains sample CSV files for testing the FERPA-Compliant RAG Decision Support System. These files demonstrate the expected format for each dataset type and include various edge cases to test system robustness.

## Files

### 1. sample_survey_responses.csv

**Dataset Type:** `survey`

**Required Columns:**
- `response_date`: Date of the survey response (YYYY-MM-DD format)
- `question`: The survey question asked
- `response_text`: The respondent's answer

**Data Characteristics:**
- 72 survey responses spanning January-March 2024
- Mix of positive and negative feedback
- Various sentiment types (positive, negative, neutral)
- Realistic library assessment scenarios

**Edge Cases Included:**
- Empty responses (rows 8, 21) - testing handling of missing data
- Very long text responses (row 68) - testing text processing limits
- Special characters and emojis (row 67) - testing character encoding
- HTML/script tags (row 69) - testing input sanitization
- ALL CAPS text (row 71) - testing text normalization
- Punctuation variations (exclamation marks, quotes, apostrophes)
- Multi-sentence responses with complex punctuation

**Themes Present:**
- Study spaces and environment
- Staff helpfulness
- Digital resources and databases
- Hours of operation
- Technology and equipment
- Collections and materials
- Services (ILL, reference, workshops)
- Accessibility and inclusivity
- Facilities (temperature, lighting, seating)

### 2. sample_usage_statistics.csv

**Dataset Type:** `usage`

**Required Columns:**
- `date`: Date of the statistic (YYYY-MM-DD format)
- `metric_name`: Name of the metric being measured
- `metric_value`: Numeric value of the metric

**Optional Columns:**
- `category`: Category grouping for the metric

**Data Characteristics:**
- 324 data points spanning January-February 2024
- Time series data showing daily patterns
- Multiple metrics tracked simultaneously

**Metrics Included:**
- `gate_count`: Daily visitor traffic (shows weekday/weekend patterns)
- `database_sessions`: Digital resource usage
- `reference_questions`: Service desk interactions
- `study_room_bookings`: Space utilization
- `computer_logins`: Technology usage
- `wifi_connections`: Network usage
- `interlibrary_loan_requests`: ILL service demand
- `workshop_attendance`: Instruction program participation (sporadic events)
- `printing_pages`: Print service usage

**Categories:**
- `daily_traffic`: Physical visits
- `digital_resources`: Online resource usage
- `services`: Service desk and support
- `spaces`: Room and space bookings
- `technology`: Computer and network usage
- `instruction`: Educational programs

**Patterns:**
- Weekday vs. weekend differences (lower usage on weekends)
- Gradual increase over time (semester progression)
- Zero values for workshop attendance (events only on specific days)
- Realistic correlations between metrics

### 3. sample_circulation_data.csv

**Dataset Type:** `circulation`

**Required Columns:**
- `checkout_date`: Date of the checkout (YYYY-MM-DD format)
- `material_type`: Type of material checked out
- `patron_type`: Type of patron (user category)

**Data Characteristics:**
- 235 checkout transactions spanning January-March 2024
- Multiple material types and patron categories
- Realistic circulation patterns

**Material Types:**
- `Book`: Traditional print books (most common)
- `DVD`: Video materials
- `Laptop`: Technology lending
- `Tablet`: Mobile device lending
- `E-Reader`: E-book reader lending
- `Calculator`: Equipment lending
- `Journal`: Print periodicals

**Patron Types:**
- `Undergraduate`: Undergraduate students (most frequent users)
- `Graduate`: Graduate students
- `Faculty`: Teaching and research faculty
- `Staff`: University staff members

**Patterns:**
- Books are the most frequently circulated material
- Undergraduates are the most active patron group
- Technology items (laptops, tablets) circulate regularly
- Weekday vs. weekend patterns (fewer checkouts on weekends)
- Multiple checkouts per day showing realistic usage

## Usage Instructions

### Uploading to the System

1. Navigate to the Data Upload page in the Streamlit application
2. Select the appropriate dataset type from the dropdown:
   - Survey → `sample_survey_responses.csv`
   - Usage → `sample_usage_statistics.csv`
   - Circulation → `sample_circulation_data.csv`
3. Upload the CSV file
4. Add FAIR/CARE metadata (optional but recommended):
   - **Title**: Descriptive name (e.g., "Spring 2024 Library User Survey")
   - **Description**: What the data represents
   - **Source**: Where the data came from (e.g., "Qualtrics survey export")
   - **Keywords**: Searchable terms (e.g., "survey, undergraduate, spring 2024")
   - **Usage Notes**: Context for responsible reuse
   - **Ethical Considerations**: Privacy and ethical use notes
5. Review the preview to verify correct parsing
6. Confirm upload

### Testing Scenarios

**CSV Validation Testing:**
- Upload files with correct format → should succeed
- Remove required columns → should fail with specific error message
- Upload empty file → should fail with "empty file" error
- Upload non-CSV file → should fail with "invalid format" error

**Data Processing Testing:**
- Query interface: Ask questions about the uploaded data
- Qualitative analysis: Run sentiment analysis on survey responses
- Visualization: Create charts from usage statistics and circulation data
- Report generation: Generate reports combining multiple datasets

**Edge Case Testing:**
- Empty survey responses should be handled gracefully
- Special characters should display correctly
- HTML tags should be sanitized
- Long text should not break the interface
- Zero values in usage statistics should be processed correctly

**FAIR/CARE Testing:**
- Add metadata to datasets
- Export datasets in CSV and JSON formats
- Generate data manifest
- Update metadata for existing datasets
- Track data provenance through analysis operations

## Expected Analysis Results

### Survey Responses

**Sentiment Distribution:**
- Positive: ~60% (praise for staff, resources, spaces)
- Negative: ~30% (complaints about hours, costs, facilities)
- Neutral: ~10% (factual statements, empty responses)

**Common Themes:**
- Study spaces and environment
- Staff quality and helpfulness
- Hours of operation
- Technology and equipment
- Collections and access
- Costs and budget concerns

### Usage Statistics

**Trends:**
- Increasing usage over time (semester progression)
- Clear weekday/weekend patterns
- Correlation between gate count and other metrics
- Sporadic workshop attendance (event-based)

**Peak Usage:**
- Weekdays show 2-3x higher usage than weekends
- Mid-week (Tuesday-Thursday) typically highest
- Late January/early February shows peak activity

### Circulation Data

**Distribution:**
- Books: ~85% of checkouts
- Technology items: ~8% of checkouts
- Media (DVDs): ~5% of checkouts
- Other materials: ~2% of checkouts

**Patron Patterns:**
- Undergraduates: ~50% of checkouts
- Graduate students: ~25% of checkouts
- Faculty: ~20% of checkouts
- Staff: ~5% of checkouts

## Notes

- All data is synthetic and created for testing purposes
- Dates span January-March 2024 to provide time series data
- Values are realistic but not based on actual library data
- Edge cases are intentionally included to test system robustness
- No personally identifiable information (PII) is included
- Data follows FERPA compliance guidelines (no student identifiers)

## Validation

All sample files have been validated against the system's CSV validation rules:
- ✓ Correct column names for each dataset type
- ✓ Valid date formats (YYYY-MM-DD)
- ✓ Appropriate data types (text, numeric, dates)
- ✓ No completely empty columns
- ✓ Realistic value ranges
- ✓ Edge cases for robustness testing

# Data Cleaning and Processing Capabilities

**Last Updated**: April 13, 2026  
**System**: Library Assessment Decision Support System

## Executive Summary

The system performs **limited, targeted data cleaning** focused on security, encoding, and PII protection. It is **best suited for reasonably clean data** but includes safeguards for common data quality issues.

## What the System DOES Clean/Process

### 1. Encoding Issues ✅
**Location**: `modules/csv_handler.py` → `parse_csv()`

**Automatic handling**:
- Tries multiple encodings: UTF-8, Latin-1, ISO-8859-1, CP1252, UTF-16
- Falls back to UTF-8 with error replacement if all fail
- Prevents encoding-related crashes

**Example**:
```python
# Automatically handles files with mixed encodings
encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
```

### 2. Metadata Sanitization ✅
**Location**: `modules/csv_handler.py` → `validate_and_sanitize_metadata()`

**Security cleaning**:
- Removes null bytes (`\x00`)
- Strips control characters (`\n`, `\r`)
- Detects and removes SQL injection patterns (`--`, `;--`, `/*`, `*/`, `xp_`, `sp_`)
- Truncates overly long strings (max 10,000 characters)
- Limits array sizes (max 100 items)

**Example**:
```python
# Removes dangerous patterns from metadata
suspicious_patterns = ['--', ';--', '/*', '*/', 'xp_', 'sp_', 'exec(', 'execute(']
sanitized_value = value.replace(pattern, '')
```

### 3. PII Detection and Redaction ✅
**Location**: `modules/pii_detector.py`

**Automatic PII handling**:
- Detects: SSN, email, phone, credit cards, names, addresses
- Redacts with placeholders: `[REDACTED_SSN]`, `[REDACTED_EMAIL]`, etc.
- Applied to RAG responses and report narratives
- Preserves data utility while protecting privacy

**Example**:
```python
# Automatically redacts PII from text
text = "Contact John Doe at john@example.com or 555-123-4567"
redacted = "Contact [REDACTED_NAME] at [REDACTED_EMAIL] or [REDACTED_PHONE]"
```

### 4. Flexible Column Mapping ✅
**Location**: `modules/csv_handler.py` → `_store_survey_data()`, `_store_usage_data()`, `_store_circulation_data()`

**Smart column detection**:
- Maps variations to canonical names
- Example: "Date", "date", "response_date", "Date Submitted" → all map to `response_date`
- Handles different naming conventions from various data sources

**Example**:
```python
# Automatically maps flexible column names
if 'date' in col.lower() or 'time' in col.lower():
    col_map.setdefault('response_date', col)
```

### 5. Basic Validation ✅
**Location**: `modules/csv_handler.py` → `validate_csv()`

**Checks performed**:
- Empty file detection
- Duplicate column name detection
- Completely empty column detection
- Basic CSV format validation

## What the System DOES NOT Clean

### ❌ Missing Values
- **Not handled**: Empty cells, NULL values, blank strings
- **Impact**: Missing data passes through as-is
- **Recommendation**: Clean missing values before upload

### ❌ Inconsistent Formatting
- **Not handled**: Date format variations (MM/DD/YYYY vs DD-MM-YYYY)
- **Not handled**: Case inconsistencies (e.g., "Yes" vs "yes" vs "YES")
- **Not handled**: Whitespace variations (leading/trailing spaces)
- **Impact**: May affect analysis accuracy
- **Recommendation**: Standardize formats before upload

### ❌ Outliers and Invalid Values
- **Not handled**: Statistical outliers
- **Not handled**: Out-of-range values (e.g., age = 999)
- **Not handled**: Invalid data types (e.g., text in numeric columns)
- **Impact**: May skew analysis results
- **Recommendation**: Validate data ranges before upload

### ❌ Duplicate Records
- **Not handled**: Duplicate rows in the dataset
- **Impact**: May inflate counts and skew statistics
- **Recommendation**: Deduplicate before upload

### ❌ Text Normalization
- **Not handled**: Spelling corrections
- **Not handled**: Abbreviation expansion
- **Not handled**: Synonym standardization
- **Impact**: May affect text analysis and theme detection
- **Recommendation**: Normalize text before upload if consistency is critical

### ❌ Data Type Coercion
- **Not handled**: Automatic type conversion (strings to numbers, etc.)
- **Impact**: Pandas infers types automatically, which may not match expectations
- **Recommendation**: Ensure correct data types in source CSV

## Recommendations by Data Quality Level

### High-Quality Data (Recommended) ✅
**Characteristics**:
- Consistent formatting
- No missing values or clearly marked as NULL
- Standardized date formats
- No duplicates
- Validated ranges

**System Suitability**: **Excellent** - System will work optimally

### Medium-Quality Data (Acceptable) ⚠️
**Characteristics**:
- Some missing values
- Minor formatting inconsistencies
- Occasional duplicates
- Mixed case/whitespace

**System Suitability**: **Good** - System will work but may require manual review of results

**Pre-processing Recommendations**:
1. Handle missing values (impute or remove)
2. Standardize date formats
3. Remove duplicates
4. Trim whitespace
5. Standardize case

### Low-Quality Data (Not Recommended) ❌
**Characteristics**:
- Extensive missing data (>20%)
- Multiple date formats
- Many duplicates
- Invalid values
- Inconsistent schemas

**System Suitability**: **Poor** - Results will be unreliable

**Required Pre-processing**:
1. Comprehensive data cleaning pipeline
2. Validation and quality checks
3. Standardization across all fields
4. Deduplication
5. Outlier detection and handling

## Data Cleaning Workflow Recommendation

### Before Upload (Your Responsibility)
```
1. Remove duplicates
2. Handle missing values
3. Standardize formats (dates, case, etc.)
4. Validate ranges and data types
5. Trim whitespace
6. Check for outliers
```

### During Upload (System Handles)
```
1. Encoding detection ✅
2. Metadata sanitization ✅
3. Column name mapping ✅
4. Basic validation ✅
5. PII detection ✅
```

### After Upload (System Handles)
```
1. PII redaction in outputs ✅
2. Sentiment analysis
3. Theme detection
4. Statistical analysis
5. Report generation
```

## Example: Good vs Bad Data

### ✅ Good Data (System-Ready)
```csv
response_date,question,response_text,rating
2024-01-15,How satisfied are you?,Very satisfied,5
2024-01-16,How satisfied are you?,Somewhat satisfied,4
2024-01-17,How satisfied are you?,Neutral,3
```

**Why it's good**:
- Consistent date format
- No missing values
- Standardized text
- Valid ratings

### ❌ Bad Data (Needs Cleaning)
```csv
Date,Question,Response,Rating
01/15/24,How satisfied are you?,Very satisfied,5
1-16-2024,How satisfied are you?,,4
2024/01/17,How satisfied are you?,neutral,999
01/15/24,How satisfied are you?,Very satisfied,5
```

**Problems**:
- Inconsistent date formats (3 different formats)
- Missing value in row 2
- Duplicate row (row 1 and 4)
- Invalid rating (999)
- Case inconsistency ("neutral" vs "Neutral")

## Tools for Pre-Processing

If you need to clean data before upload, consider:

1. **Python/Pandas**:
   ```python
   import pandas as pd
   
   # Read CSV
   df = pd.read_csv('data.csv')
   
   # Remove duplicates
   df = df.drop_duplicates()
   
   # Handle missing values
   df = df.fillna('')  # or df.dropna()
   
   # Standardize dates
   df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
   
   # Trim whitespace
   df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
   
   # Save cleaned data
   df.to_csv('data_cleaned.csv', index=False)
   ```

2. **Excel/Google Sheets**:
   - Remove duplicates: Data → Remove Duplicates
   - Find & Replace for standardization
   - Data validation for ranges
   - TRIM() function for whitespace

3. **OpenRefine**: Free tool for data cleaning and transformation

## Conclusion

**The system is best suited for reasonably clean data** with:
- ✅ Consistent formatting
- ✅ Minimal missing values
- ✅ No duplicates
- ✅ Valid data ranges

**The system provides**:
- ✅ Security safeguards (SQL injection prevention)
- ✅ Encoding handling
- ✅ PII protection
- ✅ Flexible column mapping

**You should pre-process**:
- ❌ Missing values
- ❌ Duplicates
- ❌ Format inconsistencies
- ❌ Outliers
- ❌ Invalid values

---

**Questions?** Review the data quality checklist above or consult the USER_GUIDE.md for upload best practices.

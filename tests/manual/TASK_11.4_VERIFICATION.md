# Task 11.4 Verification: Qualitative Analysis Page

## Overview
This document provides manual verification steps for the qualitative analysis page implementation.

## Requirements Validated
- Requirement 3.1: Perform sentiment analysis on open-ended survey responses
- Requirement 3.2: Categorize responses as positive, negative, or neutral
- Requirement 3.3: Identify recurring themes using keyword extraction or clustering
- Requirement 3.4: Generate summary of identified themes with frequency counts
- Requirement 3.5: Display sentiment distribution statistics
- Requirement 3.6: Show representative quotes for each identified theme
- Requirement 3.7: Export analysis results to CSV format

## Prerequisites
1. Streamlit application is running (`streamlit run streamlit_app.py`)
2. User is authenticated and logged in
3. At least one survey dataset with open-ended responses is uploaded
4. Survey dataset has at least 10 responses for analysis

## Test Cases

### TC 11.4.1: Dataset Selector Display
**Steps:**
1. Navigate to "📊 Qualitative Analysis" page
2. Observe the dataset selector dropdown

**Expected Results:**
- ✅ Page displays "Select Dataset" section
- ✅ Dropdown shows only survey-type datasets
- ✅ Each option shows dataset name and ID
- ✅ If no survey datasets exist, shows info message to upload data

### TC 11.4.2: Dataset Information Display
**Steps:**
1. Select a survey dataset from the dropdown
2. Observe the dataset information metrics

**Expected Results:**
- ✅ Displays three metrics: Dataset name, Total Rows, Upload Date
- ✅ Metrics show correct information from the selected dataset
- ✅ Upload date is formatted as YYYY-MM-DD

### TC 11.4.3: Analysis Options
**Steps:**
1. Observe the "Analysis Options" section
2. Interact with the theme slider

**Expected Results:**
- ✅ Slider allows selection from 2 to 10 themes
- ✅ Default value is 5 themes
- ✅ "Run Analysis" button is visible and styled as primary
- ✅ Help text explains the purpose of the slider

### TC 11.4.4: Run Sentiment Analysis
**Steps:**
1. Select a survey dataset with at least 10 responses
2. Click "Run Analysis" button
3. Wait for analysis to complete

**Expected Results:**
- ✅ Shows spinner with "Analyzing responses..." message
- ✅ Analysis completes without errors
- ✅ Shows success message "Analysis completed successfully!"
- ✅ Sentiment distribution section appears

### TC 11.4.5: Sentiment Distribution Display
**Steps:**
1. After successful analysis, observe the sentiment distribution section
2. Review the metrics and chart

**Expected Results:**
- ✅ Displays four metrics: Total Responses, Positive %, Neutral %, Negative %
- ✅ Percentages sum to 100%
- ✅ Bar chart shows sentiment distribution visually
- ✅ Chart has clear labels and title
- ✅ Chart uses accessible colors

### TC 11.4.6: Theme Identification Display
**Steps:**
1. After successful analysis, observe the "Identified Themes" section
2. Review each theme expander

**Expected Results:**
- ✅ Shows correct number of themes (matching slider selection)
- ✅ Displays total responses analyzed
- ✅ Each theme has an expander with name, frequency, and percentage
- ✅ Themes are expanded by default

### TC 11.4.7: Theme Details
**Steps:**
1. Examine the details within each theme expander
2. Verify all information is present

**Expected Results:**
- ✅ Shows keywords associated with the theme
- ✅ Shows frequency count and percentage
- ✅ Shows sentiment distribution (Positive, Neutral, Negative percentages)
- ✅ Shows representative quotes (up to 3)
- ✅ Quotes are formatted with quotation marks and italics

### TC 11.4.8: Theme Frequency Chart
**Steps:**
1. Scroll to the "Theme Frequency Distribution" section
2. Observe the bar chart

**Expected Results:**
- ✅ Bar chart displays all identified themes
- ✅ Chart shows frequency for each theme
- ✅ Chart has clear title, axis labels
- ✅ Chart is interactive (Plotly features work)

### TC 11.4.9: Export Themes to CSV
**Steps:**
1. Click "Export Themes (CSV)" button
2. Open the downloaded CSV file

**Expected Results:**
- ✅ CSV file downloads successfully
- ✅ Filename includes dataset name
- ✅ CSV contains columns: Theme, Keywords, Frequency, Percentage, Positive_Sentiment, Neutral_Sentiment, Negative_Sentiment
- ✅ All themes are included in the export
- ✅ Data is properly formatted

### TC 11.4.10: Export Sentiment Chart
**Steps:**
1. Click "Export Sentiment Chart" button
2. Open the downloaded HTML file in a browser

**Expected Results:**
- ✅ HTML file downloads successfully
- ✅ Filename includes dataset name
- ✅ Chart displays correctly in browser
- ✅ Chart is interactive (hover, zoom, pan work)
- ✅ Chart matches the one displayed in the app

### TC 11.4.11: Export Theme Chart
**Steps:**
1. Click "Export Theme Chart" button
2. Open the downloaded HTML file in a browser

**Expected Results:**
- ✅ HTML file downloads successfully
- ✅ Filename includes dataset name
- ✅ Chart displays correctly in browser
- ✅ Chart is interactive
- ✅ Chart matches the one displayed in the app

### TC 11.4.12: Insufficient Data Handling
**Steps:**
1. Select a survey dataset with fewer than 10 responses
2. Click "Run Analysis" button

**Expected Results:**
- ✅ Shows error message indicating insufficient data
- ✅ Error message specifies minimum required responses
- ✅ Error message shows actual number of responses found
- ✅ No analysis results are displayed

### TC 11.4.13: Theme Count Validation
**Steps:**
1. Select a survey dataset with fewer responses than requested themes
2. Set theme slider to a number greater than available responses
3. Click "Run Analysis" button

**Expected Results:**
- ✅ Shows error message indicating not enough responses for requested themes
- ✅ Error message is clear and actionable
- ✅ No analysis results are displayed

### TC 11.4.14: Analysis Persistence
**Steps:**
1. Run analysis on a dataset
2. Navigate to another page
3. Return to Qualitative Analysis page
4. Select the same dataset

**Expected Results:**
- ✅ Previous analysis results are still displayed
- ✅ Results match the selected dataset
- ✅ No need to re-run analysis

### TC 11.4.15: Different Dataset Selection
**Steps:**
1. Run analysis on Dataset A
2. Select Dataset B from dropdown (without clicking Run Analysis)

**Expected Results:**
- ✅ Analysis results from Dataset A are cleared or hidden
- ✅ User must click "Run Analysis" to see results for Dataset B
- ✅ No confusion between datasets

### TC 11.4.16: Help Section
**Steps:**
1. Scroll to bottom of page
2. Click on "How to use Qualitative Analysis" expander

**Expected Results:**
- ✅ Help section expands to show detailed instructions
- ✅ Instructions cover: Getting Started, Sentiment Analysis, Theme Identification, Minimum Requirements, Export Options
- ✅ Information is clear and helpful
- ✅ Tip is displayed at the bottom

### TC 11.4.17: Access Logging
**Steps:**
1. Run analysis on a dataset
2. Check access logs in the database

**Expected Results:**
- ✅ Access log entry is created
- ✅ Log includes username, action description, and timestamp
- ✅ Action description includes dataset name and ID

### TC 11.4.18: Multiple Theme Counts
**Steps:**
1. Run analysis with 3 themes
2. Observe results
3. Change slider to 7 themes
4. Run analysis again
5. Observe results

**Expected Results:**
- ✅ First analysis shows 3 themes
- ✅ Second analysis shows 7 themes
- ✅ Results update correctly
- ✅ Theme names and keywords differ appropriately

## Edge Cases

### EC 11.4.1: No Survey Datasets
**Steps:**
1. Ensure no survey datasets are uploaded
2. Navigate to Qualitative Analysis page

**Expected Results:**
- ✅ Shows info message: "No survey datasets available"
- ✅ Provides guidance to upload survey data
- ✅ No errors occur

### EC 11.4.2: Empty Responses
**Steps:**
1. Upload survey dataset with some empty/null responses
2. Run analysis

**Expected Results:**
- ✅ Analysis completes successfully
- ✅ Empty responses are skipped
- ✅ Only non-empty responses are analyzed
- ✅ Total count reflects actual analyzed responses

### EC 11.4.3: Special Characters in Responses
**Steps:**
1. Upload survey dataset with special characters (emojis, unicode, etc.)
2. Run analysis

**Expected Results:**
- ✅ Analysis handles special characters gracefully
- ✅ No encoding errors occur
- ✅ Special characters display correctly in quotes

### EC 11.4.4: Very Long Responses
**Steps:**
1. Upload survey dataset with very long text responses
2. Run analysis

**Expected Results:**
- ✅ Analysis completes without timeout
- ✅ Long quotes are displayed (may be truncated in display)
- ✅ Export includes full text

## Performance Validation

### PV 11.4.1: Analysis Speed
**Steps:**
1. Upload dataset with 100 responses
2. Run analysis with 5 themes
3. Measure time to completion

**Expected Results:**
- ✅ Analysis completes in reasonable time (< 30 seconds)
- ✅ UI remains responsive during analysis
- ✅ Spinner provides feedback

### PV 11.4.2: Large Dataset Handling
**Steps:**
1. Upload dataset with 500+ responses
2. Run analysis with 10 themes
3. Observe performance

**Expected Results:**
- ✅ Analysis completes successfully
- ✅ Results display without lag
- ✅ Charts render properly
- ✅ Export functions work correctly

## Integration Validation

### IV 11.4.1: Integration with CSV Handler
**Steps:**
1. Verify dataset selector uses csv_handler.get_datasets()
2. Verify only survey datasets are shown

**Expected Results:**
- ✅ Correctly retrieves datasets from database
- ✅ Filters to show only survey type
- ✅ Displays correct metadata

### IV 11.4.2: Integration with Qualitative Analysis Module
**Steps:**
1. Verify sentiment analysis calls qualitative_analysis.analyze_dataset_sentiment()
2. Verify theme extraction calls qualitative_analysis.extract_themes()

**Expected Results:**
- ✅ Functions are called with correct parameters
- ✅ Results are properly structured
- ✅ Errors are handled gracefully

### IV 11.4.3: Integration with Visualization Module
**Steps:**
1. Verify charts use visualization.create_bar_chart()
2. Verify export uses visualization.export_chart()

**Expected Results:**
- ✅ Charts are created with correct parameters
- ✅ Charts display properly in Streamlit
- ✅ Export produces valid files

### IV 11.4.4: Integration with Auth Module
**Steps:**
1. Verify access logging calls auth.log_access()
2. Check that username is from session state

**Expected Results:**
- ✅ Access is logged correctly
- ✅ Username is captured from session
- ✅ Action description is meaningful

## Verification Checklist

- [ ] All test cases pass
- [ ] All edge cases handled
- [ ] Performance is acceptable
- [ ] All integrations work correctly
- [ ] UI is intuitive and user-friendly
- [ ] Error messages are clear and actionable
- [ ] Export functionality works for all formats
- [ ] Help documentation is comprehensive
- [ ] Access logging is working
- [ ] No console errors or warnings

## Notes
- This is a manual verification document. Automated tests should be created separately.
- Test with various dataset sizes and content types for thorough validation.
- Verify accessibility features (color contrast, keyboard navigation) if possible.

## Sign-off
- [ ] Developer verification complete
- [ ] Code review complete
- [ ] User acceptance testing complete

Date: _______________
Verified by: _______________

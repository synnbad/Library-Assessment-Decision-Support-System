"""
Manual Test Script for Report Generation Page (Task 11.6)

This script provides manual testing instructions for the report generation page.
Run the Streamlit app and follow these test cases to verify functionality.

Test Environment Setup:
1. Ensure Ollama is running: `ollama serve`
2. Ensure the model is available: `ollama pull llama3.2:3b`
3. Start the Streamlit app: `streamlit run streamlit_app.py`
4. Log in with valid credentials
5. Upload at least one dataset (preferably survey data with qualitative analysis)
"""

# Manual Test Cases for Report Generation Page

TEST_CASES = """
=== MANUAL TEST CASES FOR REPORT GENERATION PAGE ===

Prerequisites:
- At least 2 datasets uploaded (mix of survey and usage data recommended)
- At least 1 survey dataset with qualitative analysis performed
- Ollama running and accessible

---
TEST CASE 1: Basic Report Generation with Single Dataset
---
Steps:
1. Navigate to "📄 Report Generation" page
2. Select ONE dataset from the multi-select dropdown
3. Keep "Include Visualizations" checked (default)
4. Keep "Include Qualitative Analysis" unchecked
5. Leave "Custom Report Title" blank
6. Click "📊 Generate Report"

Expected Results:
✓ Progress indicator shows report generation steps
✓ Success message appears: "✅ Report generated successfully!"
✓ Report preview displays with:
  - Auto-generated title (e.g., "Assessment Report: [dataset_name]")
  - Report metadata (generated timestamp, author, dataset list)
  - Executive summary (AI-generated narrative)
  - Statistical summaries section with descriptive statistics
  - Visualizations section (if applicable data exists)
  - Data sources citations
✓ Export buttons appear: "📄 Download as Markdown" and "📕 Download as PDF"

---
TEST CASE 2: Multi-Dataset Report Generation
---
Steps:
1. Navigate to "📄 Report Generation" page
2. Select MULTIPLE datasets (2-3) from the multi-select dropdown
3. Keep "Include Visualizations" checked
4. Keep "Include Qualitative Analysis" unchecked
5. Leave "Custom Report Title" blank
6. Click "📊 Generate Report"

Expected Results:
✓ Progress indicator shows report generation steps
✓ Success message appears
✓ Report preview displays with:
  - Auto-generated title (e.g., "Assessment Report: 3 Datasets")
  - Metadata lists all selected datasets
  - Executive summary combines findings from all datasets
  - Statistical summaries section shows stats for EACH dataset
  - Visualizations from multiple datasets (if applicable)
  - Citations for ALL datasets
✓ Export buttons functional

---
TEST CASE 3: Report with Visualizations
---
Steps:
1. Navigate to "📄 Report Generation" page
2. Select a dataset that has categorical data (e.g., survey with sentiment)
3. CHECK "Include Visualizations"
4. Keep "Include Qualitative Analysis" unchecked
5. Click "📊 Generate Report"

Expected Results:
✓ Report preview includes "## Visualizations" section
✓ Charts are displayed inline (sentiment pie chart, category bar chart, etc.)
✓ Each visualization has a descriptive title
✓ Visualizations use accessible color schemes
✓ Charts are interactive (Plotly charts)

---
TEST CASE 4: Report with Qualitative Analysis
---
Prerequisites:
- At least one survey dataset with qualitative analysis already performed

Steps:
1. Navigate to "📄 Report Generation" page
2. Select a survey dataset that has qualitative analysis
3. Keep "Include Visualizations" checked
4. CHECK "Include Qualitative Analysis"
5. Click "📊 Generate Report"

Expected Results:
✓ Report preview includes "## Qualitative Analysis" section
✓ Sentiment distribution displayed with metrics
✓ Report includes "## Identified Themes" section
✓ Each theme shows:
  - Theme name and frequency
  - Keywords
  - Representative quotes
✓ Executive summary incorporates qualitative findings

---
TEST CASE 5: Custom Report Title
---
Steps:
1. Navigate to "📄 Report Generation" page
2. Select one or more datasets
3. Enter a custom title: "Q4 2024 Library Assessment Report"
4. Click "📊 Generate Report"

Expected Results:
✓ Report preview displays custom title: "Q4 2024 Library Assessment Report"
✓ Custom title appears in report header
✓ Exported files use custom title in filename

---
TEST CASE 6: Report without Visualizations
---
Steps:
1. Navigate to "📄 Report Generation" page
2. Select one or more datasets
3. UNCHECK "Include Visualizations"
4. Click "📊 Generate Report"

Expected Results:
✓ Report generates successfully
✓ No "## Visualizations" section in preview
✓ Report still includes all other sections
✓ Export works correctly

---
TEST CASE 7: Markdown Export
---
Steps:
1. Generate a report (any configuration)
2. Click "📄 Download as Markdown" button

Expected Results:
✓ File downloads successfully
✓ Filename format: "[Report_Title].md"
✓ Open the file and verify:
  - Valid Markdown syntax
  - All sections present (title, metadata, summary, statistics, citations)
  - Proper formatting (headers, lists, tables)
  - Readable text content

---
TEST CASE 8: PDF Export
---
Steps:
1. Generate a report (any configuration)
2. Click "📕 Download as PDF" button

Expected Results:
✓ File downloads successfully (or warning if reportlab unavailable)
✓ Filename format: "[Report_Title].pdf"
✓ Open the file and verify:
  - Professional formatting
  - All sections present
  - Tables and statistics formatted correctly
  - Page breaks appropriate
  - Citations on separate page

Note: If reportlab is not installed, expect:
✓ Warning message: "⚠️ PDF export not available. Please use Markdown export."
✓ Markdown export still works

---
TEST CASE 9: No Datasets Available
---
Steps:
1. Delete all datasets (or test with fresh database)
2. Navigate to "📄 Report Generation" page

Expected Results:
✓ Info message displays: "No datasets available. Please upload data in the Data Upload section."
✓ No report configuration options shown
✓ No generate button available

---
TEST CASE 10: No Dataset Selected
---
Steps:
1. Navigate to "📄 Report Generation" page
2. Do NOT select any datasets from multi-select
3. Observe the page

Expected Results:
✓ Info message displays: "Please select at least one dataset to generate a report."
✓ Generate button not shown or disabled
✓ No report preview displayed

---
TEST CASE 11: Report Generation Error Handling
---
Steps:
1. Navigate to "📄 Report Generation" page
2. Select a dataset
3. Stop Ollama service: `pkill ollama` (or stop the process)
4. Click "📊 Generate Report"

Expected Results:
✓ Error message displays explaining the issue
✓ Progress indicator clears
✓ User can retry after fixing the issue
✓ No partial report displayed

---
TEST CASE 12: Report Preview Expandable Sections
---
Steps:
1. Generate a report with multiple datasets and statistics
2. Review the report preview

Expected Results:
✓ Metadata section is collapsible (expander)
✓ Each metric's statistics are in expandable sections
✓ Categorical distributions are in expandable sections
✓ Theme details are in expandable sections
✓ All expanders work correctly (expand/collapse)

---
TEST CASE 13: Progress Indicator
---
Steps:
1. Navigate to "📄 Report Generation" page
2. Select multiple datasets
3. Enable visualizations and qualitative analysis
4. Click "📊 Generate Report"
5. Observe the progress indicator

Expected Results:
✓ Progress bar appears immediately
✓ Status text updates:
  - "Creating report structure..." (20%)
  - "Generating narrative text..." (60%)
  - "Report generated successfully!" (100%)
✓ Progress bar and status text clear after completion
✓ Total time < 2 minutes for typical datasets

---
TEST CASE 14: Help Section
---
Steps:
1. Navigate to "📄 Report Generation" page
2. Scroll to bottom
3. Click "ℹ️ How to use Report Generation" expander

Expected Results:
✓ Help section expands
✓ Contains comprehensive instructions:
  - Getting Started steps
  - Report Components explanation
  - Visualizations info
  - Qualitative Analysis info
  - Export Formats info
  - Performance expectations
  - Requirements
✓ Tip displayed at bottom of page

---
TEST CASE 15: Access Logging
---
Steps:
1. Generate a report with specific datasets
2. Check access logs in database:
   ```sql
   SELECT * FROM access_logs ORDER BY timestamp DESC LIMIT 5;
   ```

Expected Results:
✓ Log entry created with:
  - Username
  - Action: "Generated report for datasets: [dataset_ids]"
  - Timestamp
  - Details

---
TEST CASE 16: Session Persistence
---
Steps:
1. Generate a report
2. Navigate to another page (e.g., "🏠 Home")
3. Navigate back to "📄 Report Generation"

Expected Results:
✓ Previously generated report still displayed in preview
✓ Export buttons still functional
✓ Can generate a new report (replaces previous)

---
TEST CASE 17: Multiple Report Generations
---
Steps:
1. Generate a report with Dataset A
2. Review the preview
3. Change selection to Dataset B
4. Generate a new report

Expected Results:
✓ First report preview displayed correctly
✓ Second report generation succeeds
✓ Preview updates to show second report
✓ First report is replaced (not accumulated)

---
TEST CASE 18: Requirements Validation
---
Verify the following requirements are met:

Requirement 4.1 - Statistical Summaries:
✓ Report includes descriptive statistics (mean, median, std dev, count, range)

Requirement 4.2 - Narrative Text:
✓ Executive summary generated using Local_LLM (Ollama)
✓ Narrative explains key findings

Requirement 4.3 - Visualizations:
✓ Data visualizations included when enabled
✓ Charts display correctly in preview

Requirement 4.4 - Export Formats:
✓ PDF export available (or graceful fallback)
✓ Markdown export available

Requirement 4.5 - Citations:
✓ All data sources cited in report
✓ Citations include dataset ID, type, and record count

Requirement 4.6 - Performance:
✓ Report generation completes within 2 minutes for typical datasets

Requirement 4.7 - Theme Summaries:
✓ Theme summaries included when qualitative analysis performed
✓ Themes show frequency, keywords, and quotes

---
ACCESSIBILITY CHECKS
---
1. Keyboard Navigation:
   ✓ All interactive elements accessible via Tab key
   ✓ Multi-select dropdown keyboard navigable
   ✓ Checkboxes keyboard toggleable
   ✓ Buttons keyboard activatable

2. Screen Reader Compatibility:
   ✓ All form elements have labels
   ✓ Help text provides context
   ✓ Error messages are clear and descriptive

3. Visual Design:
   ✓ Sufficient color contrast
   ✓ Clear visual hierarchy
   ✓ Icons supplement text (not replace)

---
EDGE CASES
---
1. Very Large Dataset (>1000 rows):
   - Report generation may take longer
   - Should still complete successfully
   - Performance warning if >2 minutes

2. Dataset with No Statistics:
   - Report should handle gracefully
   - Show available data only
   - No errors or crashes

3. Qualitative Analysis Not Available:
   - Checkbox enabled but no analysis data
   - Report generates without qualitative section
   - No errors

4. Special Characters in Dataset Names:
   - Report title handles special characters
   - Export filenames sanitized
   - No file system errors

---
INTEGRATION POINTS
---
Verify integration with:
1. csv_handler module: ✓ get_datasets() works
2. report_generator module: ✓ create_report() works
3. report_generator module: ✓ export_report() works
4. auth module: ✓ log_access() works
5. Session state: ✓ current_report persists

---
"""

def print_test_cases():
    """Print all test cases for manual testing."""
    print(TEST_CASES)


if __name__ == "__main__":
    print_test_cases()
    print("\n" + "="*70)
    print("MANUAL TESTING INSTRUCTIONS")
    print("="*70)
    print("\n1. Start Ollama: ollama serve")
    print("2. Start Streamlit: streamlit run streamlit_app.py")
    print("3. Log in to the application")
    print("4. Follow the test cases above")
    print("5. Document any issues or unexpected behavior")
    print("\n" + "="*70)

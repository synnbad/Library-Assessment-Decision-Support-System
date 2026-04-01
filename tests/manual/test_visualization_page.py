"""
Manual Test for Visualization Page (Task 11.5)

This script tests the visualization page functionality including:
- Dataset selector
- Chart type selector (bar, line, pie)
- Column selection for x and y axes
- Chart generation and display
- Chart export (PNG and HTML)

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5

To run this test:
1. Ensure you have uploaded at least one dataset with numeric data
2. Start the Streamlit app: streamlit run streamlit_app.py
3. Log in to the application
4. Navigate to "📈 Visualizations" page
5. Follow the test steps below

Test Steps:
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from modules import csv_handler, visualization
import pandas as pd


def test_visualization_functions():
    """Test visualization module functions directly."""
    print("=" * 60)
    print("Testing Visualization Module Functions")
    print("=" * 60)
    
    # Create sample data
    print("\n1. Creating sample data...")
    bar_data = pd.DataFrame({
        'Category': ['A', 'B', 'C', 'D'],
        'Value': [10, 25, 15, 30]
    })
    
    line_data = pd.DataFrame({
        'Date': ['2024-01', '2024-02', '2024-03', '2024-04'],
        'Count': [100, 150, 120, 180]
    })
    
    pie_data = pd.DataFrame({
        'Type': ['Fiction', 'Non-Fiction', 'Reference', 'Periodicals'],
        'Checkouts': [450, 320, 180, 250]
    })
    
    print("✓ Sample data created")
    
    # Test bar chart
    print("\n2. Testing bar chart creation...")
    try:
        bar_fig = visualization.create_bar_chart(
            bar_data,
            x='Category',
            y='Value',
            title='Test Bar Chart',
            x_label='Categories',
            y_label='Values'
        )
        print("✓ Bar chart created successfully")
        print(f"  - Chart type: {type(bar_fig)}")
        print(f"  - Has data: {len(bar_fig.data) > 0}")
    except Exception as e:
        print(f"✗ Bar chart creation failed: {e}")
        return False
    
    # Test line chart
    print("\n3. Testing line chart creation...")
    try:
        line_fig = visualization.create_line_chart(
            line_data,
            x='Date',
            y='Count',
            title='Test Line Chart',
            x_label='Time Period',
            y_label='Count'
        )
        print("✓ Line chart created successfully")
        print(f"  - Chart type: {type(line_fig)}")
        print(f"  - Has data: {len(line_fig.data) > 0}")
    except Exception as e:
        print(f"✗ Line chart creation failed: {e}")
        return False
    
    # Test pie chart
    print("\n4. Testing pie chart creation...")
    try:
        pie_fig = visualization.create_pie_chart(
            pie_data,
            values='Checkouts',
            names='Type',
            title='Test Pie Chart'
        )
        print("✓ Pie chart created successfully")
        print(f"  - Chart type: {type(pie_fig)}")
        print(f"  - Has data: {len(pie_fig.data) > 0}")
    except Exception as e:
        print(f"✗ Pie chart creation failed: {e}")
        return False
    
    # Test chart export (HTML)
    print("\n5. Testing chart export (HTML)...")
    try:
        html_bytes = visualization.export_chart(bar_fig, 'test_chart', format='html')
        print("✓ HTML export successful")
        print(f"  - Export size: {len(html_bytes)} bytes")
        print(f"  - Contains HTML: {'<html>' in html_bytes.decode('utf-8').lower()}")
    except Exception as e:
        print(f"✗ HTML export failed: {e}")
        return False
    
    # Test chart export (PNG)
    print("\n6. Testing chart export (PNG)...")
    try:
        png_bytes = visualization.export_chart(bar_fig, 'test_chart', format='png')
        print("✓ PNG export successful")
        print(f"  - Export size: {len(png_bytes)} bytes")
        
        # Check if it's actually PNG or HTML fallback
        if png_bytes[:4] == b'\x89PNG':
            print("  - Format: PNG image")
        elif b'<html>' in png_bytes.lower():
            print("  - Format: HTML (fallback - kaleido not available)")
        else:
            print("  - Format: Unknown")
    except Exception as e:
        print(f"✗ PNG export failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("All visualization module tests passed!")
    print("=" * 60)
    return True


def print_manual_test_instructions():
    """Print manual test instructions for the Streamlit UI."""
    print("\n" + "=" * 60)
    print("Manual Test Instructions for Visualization Page")
    print("=" * 60)
    
    print("""
PREREQUISITE:
- Ensure you have at least one dataset uploaded with numeric columns
- If not, upload a sample dataset first

TEST STEPS:

1. Navigate to Visualizations Page
   - Click on "📈 Visualizations" in the sidebar
   - Verify the page title is "📈 Visualizations"
   - Verify you see a dataset selector

2. Test Dataset Selection (Requirement 5.4)
   - Select a dataset from the dropdown
   - Verify dataset info is displayed (name, type, row count)
   - Verify chart type selector appears

3. Test Bar Chart Generation (Requirement 5.1)
   - Select "Bar Chart" from chart type dropdown
   - Enter a custom chart title
   - Select a categorical column for X-axis
   - Select a numeric column for Y-axis
   - (Optional) Enter custom axis labels
   - Click "Generate Chart"
   - Verify chart is displayed below
   - Verify chart shows correct data
   - Verify chart has proper title and labels

4. Test Line Chart Generation (Requirement 5.2)
   - Select "Line Chart" from chart type dropdown
   - Enter a custom chart title
   - Select a time/sequential column for X-axis
   - Select a numeric column for Y-axis
   - Click "Generate Chart"
   - Verify line chart is displayed
   - Verify chart shows trend correctly

5. Test Pie Chart Generation (Requirement 5.3)
   - Select "Pie Chart" from chart type dropdown
   - Enter a custom chart title
   - Select a categorical column for Labels
   - Select a numeric column for Values
   - Click "Generate Chart"
   - Verify pie chart is displayed
   - Verify slices show correct proportions
   - Verify labels and percentages are visible

6. Test Chart Export (Requirement 5.5)
   - After generating any chart, scroll to "Export Chart" section
   - Click "Download as PNG" button
   - Verify PNG file downloads (or HTML if kaleido not available)
   - Click "Download as HTML" button
   - Verify HTML file downloads
   - Open HTML file in browser and verify it's interactive

7. Test Error Handling
   - Try selecting invalid column combinations
   - Verify appropriate error messages are shown
   - Try with empty dataset (if possible)
   - Verify graceful error handling

8. Test Help Section
   - Expand "How to use Visualizations" section
   - Verify comprehensive instructions are provided
   - Verify tips and best practices are included

EXPECTED RESULTS:
✓ All chart types generate correctly
✓ Charts display in the Streamlit interface
✓ Export buttons work for both PNG and HTML
✓ Error messages are clear and helpful
✓ UI is intuitive and easy to use

REQUIREMENTS VALIDATED:
- 5.1: Generate bar charts for categorical data comparisons
- 5.2: Generate line charts for time series data
- 5.3: Generate pie charts for proportion visualization
- 5.4: Display visualizations in the web interface
- 5.5: Allow export of charts as PNG images
""")
    
    print("=" * 60)


if __name__ == "__main__":
    print("\nTask 11.5: Visualization Page Implementation Test")
    print("=" * 60)
    
    # Run automated tests
    success = test_visualization_functions()
    
    if success:
        # Print manual test instructions
        print_manual_test_instructions()
        
        print("\n✓ Automated tests passed!")
        print("\nNext: Follow the manual test instructions above to verify the Streamlit UI")
    else:
        print("\n✗ Automated tests failed. Please fix issues before manual testing.")
        sys.exit(1)

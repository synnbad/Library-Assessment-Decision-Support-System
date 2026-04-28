# User Guide: Library Assessment Decision Support System

## Table of Contents

1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation and Setup](#installation-and-setup)
4. [Getting Started](#getting-started)
5. [CSV Format Requirements](#csv-format-requirements)
6. [Feature Guide](#feature-guide)
7. [Data Privacy & Compliance](#data-privacy--compliance)
8. [Troubleshooting](#troubleshooting)
9. [Frequently Asked Questions](#frequently-asked-questions)

---

## Introduction

The Library Assessment Decision Support System is an AI-augmented assessment tool designed to help library professionals analyze patron feedback, usage patterns, and service effectiveness through a human-in-the-loop approach. The system combines quantitative and qualitative analysis with natural language querying to support data-driven decision-making.

### Key Features

- **Multi-Source Data Integration**: Upload and analyze data from multiple sources (surveys, usage stats, circulation)
- **Natural Language Queries**: Ask questions about your data in plain English across all datasets
- **Qualitative Analysis**: Automated sentiment analysis and theme identification from open-ended responses
- **Quantitative Analysis**: Advanced statistical analysis (correlation, trends, comparisons, distributions) with AI-powered interpretations
- **Report Generation**: Create comprehensive reports combining quantitative and qualitative insights
- **Data Visualization**: Generate accessible charts (bar, line, pie, heatmaps, trend charts)
- **Human-in-the-Loop**: All AI insights presented for human review and validation
- **Privacy & Governance**: FERPA-conscious with local-only processing, FAIR & CARE principles

### Who Should Use This System

This system is designed for:

- Library Assessment Specialists
- Library Administrators
- Library Staff involved in data analysis
- Branch Managers comparing performance
- Anyone responsible for library assessment and reporting

No technical expertise is required—the system is designed to be user-friendly for non-technical users while providing advanced statistical capabilities.

---

## System Requirements

### Hardware Requirements

- **RAM**: 16GB minimum (8GB for LLM, 8GB for application)
- **Storage**: 50GB available space (20GB for models, 30GB for data)
- **CPU**: 4 cores minimum (8 cores recommended)
- **GPU**: Optional but recommended for faster processing

### Software Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux
- **Python**: Version 3.10 or higher
- **Ollama**: Local LLM runtime (must be installed separately)

---

## Installation and Setup

### Step 1: Install Ollama

Ollama is required to run the AI language model locally on your computer.

1. Visit [https://ollama.ai](https://ollama.ai)
2. Download the installer for your operating system
3. Run the installer and follow the on-screen instructions
4. Verify installation by opening a terminal/command prompt and typing:
   ```bash
   ollama --version
   ```

### Step 2: Download the Language Model

After installing Ollama, download the AI model:

```bash
# Recommended: Llama 3.2 3B (smaller, faster)
ollama pull llama3.2:3b

# Alternative: Phi-3 Mini (also good for this application)
ollama pull phi3:mini
```

This download may take 10-30 minutes depending on your internet connection.

### Step 3: Install the Application

1. **Download the application files** to a folder on your computer
2. **Open a terminal/command prompt** and navigate to the application folder:
   ```bash
   cd path/to/application/folder
   ```

3. **Create a Python virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Install required Python packages**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Download additional language data**:
   ```bash
   python -m textblob.download_corpora
   ```

### Step 4: Initialize the Database

Run the initialization script to set up the database:

```bash
python scripts/init_app.py
```

This creates:
- A SQLite database for storing your data
- A default admin user (username: `admin`, password: `admin123`)

**⚠️ Important**: Change the default password immediately after your first login!

### Step 5: Start the Application

```bash
streamlit run streamlit_app.py
```

The application will automatically open in your web browser at `http://localhost:8501`

---

## Getting Started

### First Login

1. When you first open the application, you'll see a login screen
2. Use the default credentials:
   - **Username**: `admin`
   - **Password**: `admin123`
3. After logging in, immediately change your password (see below)

### Changing Your Password

To change your password, you'll need to create a new user account and delete the old one:

1. Open a terminal in the application folder
2. Activate the virtual environment (see Step 3 above)
3. Run:
   ```bash
   python -c "from modules.auth import create_user; create_user('your_username', 'your_new_password')"
   ```
4. Replace `your_username` and `your_new_password` with your desired credentials
5. Log out and log back in with your new credentials

### Understanding the Interface

The application has a sidebar navigation menu with the following pages:

- **🏠 Home**: Overview and quick start guide
- **📤 Data Upload**: Upload CSV files and manage datasets
- **💬 Ask**: Ask questions about your data in natural language
- **📊 Qualitative Analysis**: Analyze sentiment and themes in survey responses
- **📈 Visualizations**: Create charts from your data
- **📄 Report Generation**: Generate comprehensive reports
- **📋 Data Governance**: Information about FAIR/CARE principles and data privacy

---

## CSV Format Requirements

The system accepts three types of CSV files. Each type has specific required columns.

### Survey Responses

Survey response files contain open-ended text responses from library users.

**Required Columns:**
- `response_date`: Date of the survey response (format: YYYY-MM-DD)
- `question`: The survey question that was asked
- `response_text`: The respondent's answer (can be empty)

**Example:**
```csv
response_date,question,response_text
2024-01-15,What do you like most about the library?,"The quiet study spaces are excellent!"
2024-01-16,What could we improve?,"The hours are too limited on weekends."
2024-01-17,What do you like most about the library?,"The staff are always helpful."
```

**Tips:**
- Dates must be in YYYY-MM-DD format (e.g., 2024-01-15)
- Text responses can contain commas, quotes, and special characters
- Empty responses are allowed (leave the response_text field blank)
- Use double quotes around text that contains commas

### Usage Statistics

Usage statistics files contain numeric metrics about library usage over time.

**Required Columns:**
- `date`: Date of the statistic (format: YYYY-MM-DD)
- `metric_name`: Name of the metric being measured
- `metric_value`: Numeric value of the metric

**Optional Columns:**
- `category`: Category grouping for the metric (e.g., "daily_traffic", "services")

**Example:**
```csv
date,metric_name,metric_value,category
2024-01-15,gate_count,1923,daily_traffic
2024-01-15,database_sessions,678,digital_resources
2024-01-15,reference_questions,56,services
2024-01-16,gate_count,2045,daily_traffic
2024-01-16,database_sessions,701,digital_resources
```

**Common Metrics:**
- `gate_count`: Number of visitors
- `database_sessions`: Digital resource usage
- `reference_questions`: Service desk interactions
- `study_room_bookings`: Room reservations
- `computer_logins`: Technology usage
- `wifi_connections`: Network usage
- `interlibrary_loan_requests`: ILL requests
- `workshop_attendance`: Event attendance
- `printing_pages`: Print service usage

**Tips:**
- Dates must be in YYYY-MM-DD format
- Metric values must be numbers (integers or decimals)
- Use consistent metric names across your data
- The category column is optional but helps with organization

### Circulation Data

Circulation data files contain information about material checkouts.

**Required Columns:**
- `checkout_date`: Date of the checkout (format: YYYY-MM-DD)
- `material_type`: Type of material checked out
- `patron_type`: Type of patron (user category)

**Example:**
```csv
checkout_date,material_type,patron_type
2024-01-15,Book,Undergraduate
2024-01-15,DVD,Graduate
2024-01-15,Laptop,Faculty
2024-01-16,Book,Undergraduate
2024-01-16,Tablet,Graduate
```

**Common Material Types:**
- `Book`: Print books
- `DVD`: Video materials
- `Laptop`: Technology lending
- `Tablet`: Mobile devices
- `E-Reader`: E-book readers
- `Calculator`: Equipment
- `Journal`: Print periodicals

**Common Patron Types:**
- `Undergraduate`: Undergraduate students
- `Graduate`: Graduate students
- `Faculty`: Teaching and research faculty
- `Staff`: University staff

**Tips:**
- Dates must be in YYYY-MM-DD format
- Use consistent naming for material types and patron types
- Each row represents one checkout transaction

### General CSV Guidelines

**File Format:**
- Save files as CSV (Comma-Separated Values)
- Use UTF-8 encoding for special characters
- Include a header row with column names
- Column names are case-sensitive

**Data Quality:**
- Remove any personally identifiable information (PII) before uploading
- Ensure dates are in YYYY-MM-DD format
- Check for missing required columns
- Verify numeric values don't contain text

**File Size:**
- The system can handle files with thousands of rows
- For very large files (>10,000 rows), consider splitting into smaller files
- Typical processing time: 1-2 minutes per 1,000 rows

---

## Feature Guide

### 1. Data Upload

The Data Upload page allows you to import CSV files into the system.

#### How to Upload Data

1. **Navigate to Data Upload** using the sidebar menu
2. **Select Dataset Type** from the dropdown:
   - Survey Responses
   - Usage Statistics
   - Circulation Data
3. **Click "Browse files"** and select your CSV file
4. **Add Metadata** (optional but recommended):
   - **Title**: A descriptive name for your dataset
   - **Description**: What the data represents
   - **Source**: Where the data came from (e.g., "Qualtrics survey")
   - **Keywords**: Searchable terms (e.g., "survey, spring 2024, undergraduate")
   - **Usage Notes**: Context for how the data should be used
   - **Ethical Considerations**: Privacy and ethical use notes
5. **Review the Preview** to verify the data was parsed correctly
6. **Click "Upload Dataset"** to save the data

#### Managing Datasets

After uploading, you can:
- **View all datasets** in the "Uploaded Datasets" section
- **Edit metadata** by clicking the "Edit Metadata" button
- **Export datasets** in CSV or JSON format
- **Delete datasets** by clicking the "Delete" button
- **Download data manifest** to see all datasets with metadata

#### FAIR & CARE Metadata

The system implements FAIR (Findable, Accessible, Interoperable, Reusable) and CARE (Collective Benefit, Authority to Control, Responsibility, Ethics) principles for responsible data governance.

**Why add metadata?**
- Makes your data findable and searchable
- Documents data provenance and source
- Provides context for future use
- Supports ethical data practices
- Enables data sharing and reuse

**Best Practices:**
- Add descriptive titles and keywords
- Document the data source and collection method
- Include usage notes explaining the data's purpose
- Note any ethical considerations or privacy concerns
- Update metadata when you perform analysis on the data

### 2. Ask

The Ask page allows you to ask questions about your data in natural language.

#### How to Use Ask

1. **Navigate to Ask** using the sidebar menu
2. **Type your question** in the text box (e.g., "What are the most common complaints in the survey responses?")
3. **Press Enter or click "Send"**
4. **View the answer** with citations to specific data sources
5. **Ask follow-up questions** - the system maintains conversation context

#### Example Questions

**For Survey Data:**
- "What are the main themes in student feedback?"
- "What do users like most about the library?"
- "What are the most common complaints?"
- "How do students feel about the study spaces?"
- "What suggestions do users have for improvement?"

**For Usage Statistics:**
- "What are the trends in gate count over time?"
- "Which days have the highest library usage?"
- "How has database usage changed this semester?"
- "What is the average number of reference questions per day?"
- "Compare weekday vs weekend usage patterns"

**For Circulation Data:**
- "What types of materials are checked out most frequently?"
- "Which patron type uses the library most?"
- "How many laptops were checked out in January?"
- "What is the distribution of checkouts by material type?"
- "Compare undergraduate vs graduate checkout patterns"

#### Tips for Better Results

- **Be specific**: Instead of "Tell me about the data", ask "What are the top 3 themes in survey responses?"
- **Ask one thing at a time**: Break complex questions into simpler parts
- **Use follow-up questions**: The system remembers context from previous questions
- **Reference specific datasets**: "In the Spring 2024 survey, what..."
- **Clear context**: Click "Clear Context" to start a new conversation topic

#### Understanding Citations

Every answer includes citations showing which data sources were used. Citations include:
- Dataset name
- Dataset type
- Specific data points referenced
- Upload date

This ensures transparency and allows you to verify the AI's answers.

### 3. Qualitative Analysis

The Qualitative Analysis page provides automated sentiment analysis and theme identification for survey responses.

#### How to Analyze Survey Data

1. **Navigate to Qualitative Analysis** using the sidebar menu
2. **Select a survey dataset** from the dropdown
3. **Click "Run Analysis"**
4. **View the results**:
   - Sentiment distribution (positive, negative, neutral)
   - Identified themes with frequency counts
   - Representative quotes for each theme
   - Sentiment statistics (percentages, counts)
5. **Export results** by clicking "Export Analysis to CSV"

#### Understanding Sentiment Analysis

The system categorizes each response as:
- **Positive** (sentiment score > 0.1): Praise, satisfaction, appreciation
- **Negative** (sentiment score < -0.1): Complaints, dissatisfaction, criticism
- **Neutral** (sentiment score between -0.1 and 0.1): Factual statements, suggestions

**Example Results:**
- Positive: 60% - "The staff are always helpful and knowledgeable"
- Negative: 30% - "The hours are too limited on weekends"
- Neutral: 10% - "I use the library for group study"

#### Understanding Theme Identification

The system automatically identifies recurring themes in your survey responses using:
- Keyword extraction (TF-IDF)
- Text clustering
- Frequency analysis

**Common Themes in Library Surveys:**
- Study spaces and environment
- Staff helpfulness and service
- Hours of operation
- Technology and equipment
- Collections and resources
- Facilities (temperature, lighting, seating)
- Services (ILL, reference, workshops)

#### Tips for Better Analysis

- **Minimum data**: At least 20-30 responses for meaningful analysis
- **Clean data**: Remove test responses or duplicates before uploading
- **Consistent questions**: Group responses by question for better theme identification
- **Review quotes**: Representative quotes help validate the identified themes
- **Export results**: Save analysis results for inclusion in reports

### 4. Quantitative Analysis

The Quantitative Analysis page provides advanced statistical analysis with AI-powered interpretations for numeric data.

#### How to Perform Quantitative Analysis

1. **Navigate to Quantitative Analysis** using the sidebar menu
2. **Select a dataset** from the dropdown
3. **Choose an analysis type**:
   - **Correlation Analysis**: Find relationships between variables
   - **Trend Analysis**: Analyze patterns over time with forecasting
   - **Comparative Analysis**: Compare metrics across groups
   - **Distribution Analysis**: Examine distributions and detect outliers
4. **Configure parameters** for the selected analysis type
5. **Click "Run Analysis"**
6. **View results**:
   - Statistical results (tables, metrics)
   - AI-generated interpretation (plain language explanation)
   - Contextual insights about patterns
   - Actionable recommendations
   - Interactive visualizations
7. **Export results** as CSV or JSON

#### Analysis Types Explained

**Correlation Analysis**

Identifies relationships between numeric variables.

- **When to use**: To understand how different metrics relate to each other
- **Methods available**:
  - Pearson: For linear relationships (normal data)
  - Spearman: For monotonic relationships (non-normal data)
  - Kendall: For ordinal data or small samples
- **Example questions**:
  - "Is there a relationship between program attendance and satisfaction scores?"
  - "Do gate counts correlate with circulation numbers?"
  - "How do different usage metrics relate to each other?"
- **Results include**:
  - Correlation matrix
  - Top correlations with significance testing
  - Correlation heatmap visualization
  - AI interpretation of relationships

**Trend Analysis**

Analyzes patterns over time and forecasts future values.

- **When to use**: To understand how metrics change over time
- **Features**:
  - Linear regression for trend detection
  - Moving averages (7-day and 30-day)
  - Seasonal pattern detection
  - 7-period forecast with confidence intervals
- **Example questions**:
  - "How has circulation changed over the past year?"
  - "What are the usage trends for digital resources?"
  - "Can we forecast next month's gate count?"
- **Results include**:
  - Trend direction (increasing, decreasing, stable)
  - Trend strength (R-squared)
  - Forecast values with confidence intervals
  - Trend chart with forecast visualization
  - AI interpretation of trends and implications

**Comparative Analysis**

Compares metrics across different groups or categories.

- **When to use**: To compare performance across branches, time periods, or categories
- **Tests available**:
  - t-test: Compare two groups (parametric)
  - Mann-Whitney: Compare two groups (non-parametric)
  - ANOVA: Compare three or more groups (parametric)
  - Kruskal-Wallis: Compare three or more groups (non-parametric)
- **Example questions**:
  - "Do satisfaction scores differ across branches?"
  - "Is there a difference in usage between weekdays and weekends?"
  - "How do different patron types compare in their library use?"
- **Results include**:
  - Test statistics and p-values
  - Effect sizes (Cohen's d)
  - Group statistics (means, standard deviations)
  - Post-hoc pairwise comparisons
  - Comparison visualization
  - AI interpretation of differences

**Distribution Analysis**

Examines data distributions and detects outliers.

- **When to use**: To understand data spread and identify unusual values
- **Methods available**:
  - IQR method: Robust to skewed data
  - Z-score method: Assumes normal distribution
- **Features**:
  - Skewness and kurtosis calculations
  - Normality testing (Shapiro-Wilk)
  - Outlier detection and severity scoring
  - Quartile calculations
- **Example questions**:
  - "Are there any unusual circulation patterns?"
  - "What is the distribution of satisfaction scores?"
  - "Which data points are outliers and should be investigated?"
- **Results include**:
  - Distribution statistics
  - Normality test results
  - Outlier list with severity scores
  - Distribution histogram with outliers highlighted
  - AI interpretation of distribution characteristics

#### Understanding AI-Generated Content

Each analysis includes three types of AI-generated content:

1. **Interpretation**: Plain-language explanation of the statistical results
   - What the numbers mean
   - Statistical significance explained
   - Practical implications

2. **Insights**: Contextual observations about patterns in your data
   - Specific data points and statistics
   - Cross-dataset relationships
   - Notable patterns or trends

3. **Recommendations**: Actionable suggestions based on the analysis
   - Specific actions to take
   - Grounded in your actual data
   - Prioritized by importance

**Important**: All AI-generated content is presented for human review and validation. You should verify insights against your domain expertise before acting on recommendations.

#### Tips for Better Quantitative Analysis

- **Minimum data**: At least 10-20 observations for meaningful analysis
- **Clean data**: Remove missing values or handle them appropriately
- **Choose appropriate methods**: The system recommends methods based on your data characteristics
- **Validate assumptions**: Review normality tests and method assumptions
- **Cross-reference results**: Compare quantitative findings with qualitative feedback
- **Save analyses**: All analyses are stored in the database for future reference
- **Export for sharing**: Download results to share with stakeholders

#### Statistical Method Selection

The system helps you choose appropriate statistical methods:

- **Automatic recommendations**: Based on data characteristics and normality tests
- **Method assumptions**: Clear explanations of what each method assumes
- **Alternative suggestions**: Non-parametric alternatives when assumptions are violated
- **Assumption validation**: Automatic checking of normality and other requirements

### 5. Visualizations

The Visualizations page allows you to create charts from your data.

#### How to Create Visualizations

1. **Navigate to Visualizations** using the sidebar menu
2. **Select a dataset** from the dropdown
3. **Choose a chart type**:
   - **Bar Chart**: Compare categories (e.g., checkouts by material type)
   - **Line Chart**: Show trends over time (e.g., daily gate count)
   - **Pie Chart**: Show proportions (e.g., patron type distribution)
4. **Select columns** for the X-axis and Y-axis (or values/names for pie charts)
5. **Enter a chart title**
6. **Click "Generate Chart"**
7. **Export as PNG** by clicking "Download Chart"

#### Chart Type Guidelines

**Bar Charts** - Best for:
- Comparing categories
- Showing counts or totals
- Material type distribution
- Patron type comparison
- Service usage by category

**Line Charts** - Best for:
- Time series data
- Trends over days/weeks/months
- Gate count over time
- Database sessions trends
- Seasonal patterns

**Pie Charts** - Best for:
- Showing proportions
- Percentage breakdowns
- Material type percentages
- Patron type distribution
- Category composition

#### Accessibility Features

All charts are designed with accessibility in mind:
- Colorblind-friendly color schemes
- High contrast for readability
- Clear labels and legends
- Descriptive titles
- Alternative text support

### 5. Report Generation

The Report Generation page creates comprehensive reports combining statistics, narrative text, and visualizations.

#### How to Generate Reports

1. **Navigate to Report Generation** using the sidebar menu
2. **Select datasets** to include (you can select multiple)
3. **Choose options**:
   - Include visualizations (recommended)
   - Include qualitative analysis (if available)
   - Include quantitative analysis (if available)
4. **Click "Generate Report"**
5. **Review the report preview**
6. **Export the report**:
   - PDF format (for sharing and printing)
   - Markdown format (for editing)

#### Report Contents

A typical report includes:

1. **Title and Metadata**
   - Report title
   - Generation date
   - Author/username
   - Datasets included

2. **Executive Summary**
   - AI-generated overview of key findings
   - High-level insights
   - Main takeaways

3. **Statistical Summaries**
   - Descriptive statistics (mean, median, standard deviation)
   - Count summaries
   - Trend analysis

4. **Visualizations** (if enabled)
   - Embedded charts
   - Trend graphs
   - Distribution charts

5. **Qualitative Analysis** (if performed)
   - Sentiment distribution
   - Identified themes
   - Representative quotes

6. **Quantitative Analysis** (if performed)
   - Statistical results (correlations, trends, comparisons, distributions)
   - AI-generated interpretations
   - Contextual insights
   - Actionable recommendations

7. **Data Source Citations**
   - List of all datasets used
   - Upload dates
   - Data provenance

7. **Timestamp and Author**
   - When the report was generated
   - Who generated it

#### Report Generation Time

- Small datasets (<500 rows): 30-60 seconds
- Medium datasets (500-2000 rows): 1-2 minutes
- Large datasets (>2000 rows): 2-5 minutes

The system will show a progress indicator during generation.

#### Tips for Better Reports

- **Select related datasets**: Combine survey, usage, and circulation data for comprehensive insights
- **Run analysis first**: Perform qualitative analysis before generating reports
- **Include visualizations**: Charts make reports more engaging and easier to understand
- **Review before exporting**: Check the preview to ensure all sections are correct
- **Choose the right format**: PDF for final reports, Markdown for editing

### 6. Data Governance

The Data Governance page provides information about:
- FAIR principles implementation
- CARE principles implementation
- Data privacy and privacy-conscious governance
- Ethical use guidelines
- Access control and audit logging

This page is informational and helps you understand how the system protects your data and implements responsible data governance practices.

---

## Data Privacy & Compliance

### What is FERPA?

The Family Educational Rights and Privacy Act (FERPA) is a federal law that protects the privacy of student education records. Libraries that serve educational institutions must comply with FERPA when handling student data.

### How This System Maintains Privacy-Conscious Local Processing

1. **Local Processing Only**
   - All AI processing happens on your computer
   - No data is sent to external servers or cloud services
   - The language model runs locally via Ollama
   - No internet connection required for processing

2. **Data Storage**
   - All data stored in local SQLite database
   - Database file remains on your computer
   - No external database connections
   - You control data retention and deletion

3. **PII Detection and Redaction**
   - System automatically detects personally identifiable information
   - PII is redacted or flagged before display
   - Protects email addresses, phone numbers, and other identifiers

4. **Access Control**
   - Password-protected access
   - User authentication required
   - Session management
   - Audit logging of all data access

5. **Audit Trail**
   - All data access is logged with timestamps
   - Logs include username and action performed
   - Supports compliance auditing and accountability

### Best Practices for Data Privacy

1. **Remove PII Before Upload**
   - Strip student names, IDs, and contact information from CSV files
   - Use anonymous identifiers if needed
   - Review data before uploading

2. **Secure Your Computer**
   - Use strong passwords for your user account
   - Lock your computer when away
   - Keep your operating system updated
   - Use antivirus software

3. **Backup Your Data**
   - Regularly backup the `data/` folder
   - Store backups securely
   - Test backup restoration periodically

4. **Control Access**
   - Only create accounts for authorized users
   - Change default passwords immediately
   - Review access logs regularly
   - Remove accounts for users who no longer need access

5. **Data Retention**
   - Delete datasets when no longer needed
   - Follow your institution's data retention policies
   - Document data lifecycle decisions

---

## Troubleshooting

### Installation Issues

#### Problem: "Python not found" or "python: command not found"

**Solution:**
- Ensure Python 3.10+ is installed
- On Windows, check "Add Python to PATH" during installation
- On macOS/Linux, use `python3` instead of `python`
- Verify installation: `python --version` or `python3 --version`

#### Problem: "pip: command not found"

**Solution:**
- pip should be included with Python
- Try `python -m pip` instead of `pip`
- On macOS/Linux, try `pip3` instead of `pip`
- Reinstall Python if pip is missing

#### Problem: Virtual environment activation fails

**Solution:**
- Windows: Use `venv\Scripts\activate` (not `venv/Scripts/activate`)
- macOS/Linux: Use `source venv/bin/activate`
- Ensure you're in the correct directory
- Try creating a new virtual environment

### Ollama Issues

#### Problem: "Cannot connect to Ollama" or "Ollama Connection Error"

**Symptoms:**
- Error message: "Ollama Connection Error - The Ollama service is not responding"
- Query interface shows connection error
- Application displays recovery instructions

**Solution:**
1. Check if Ollama is running:
   ```bash
   ollama serve
   ```
2. Verify Ollama is accessible:
   ```bash
   curl http://localhost:11434
   ```
3. Verify model is available:
   ```bash
   ollama list
   ```
4. Pull model if missing:
   ```bash
   ollama pull llama3.2:3b
   ```
5. Restart Ollama service
6. Check firewall settings

**Note:** The system now handles Ollama crashes gracefully. If Ollama stops responding, you'll see a clear error message with recovery instructions. The application will not hang or freeze.

#### Problem: "Request Timeout" after 30 seconds

**Symptoms:**
- Error message: "Request Timeout - The response generation timed out after 30 seconds"
- Query takes too long to process

**Solution:**
- Ask a simpler or more specific question
- Break complex questions into smaller parts
- Clear conversation context (reduces processing load)
- Check system resources (CPU/memory usage)
- Close other applications to free up resources
- Consider using a smaller model for faster responses

#### Problem: "Model not found"

**Solution:**
1. Download the model:
   ```bash
   ollama pull llama3.2:3b
   ```
2. Verify model is downloaded:
   ```bash
   ollama list
   ```
3. Check model name in `config/settings.py` matches downloaded model

#### Problem: Ollama is very slow

**Solution:**
- Close other applications to free up RAM
- Use a smaller model (llama3.2:3b instead of larger models)
- Consider using a computer with more RAM or a GPU
- Reduce the number of concurrent queries
- Clear conversation history to reduce context size

### Application Issues

#### Problem: "Streamlit not found" or application won't start

**Solution:**
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check for error messages in terminal
- Try: `python -m streamlit run streamlit_app.py`

#### Problem: Login page shows but can't log in

**Solution:**
- Verify database was initialized: `python scripts/init_app.py`
- Check if `data/library.db` file exists
- Try creating a new user account
- Check for error messages in terminal

#### Problem: "Database is locked" error

**Solution:**
- Close all other instances of the application
- Restart the application
- If problem persists, restart your computer
- Check if antivirus is blocking database access

### Data Upload Issues

#### Problem: "Invalid CSV format" error

**Solution:**
- Verify file is saved as CSV (not Excel .xlsx)
- Check that file has required columns
- Ensure column names match exactly (case-sensitive)
- Open file in text editor to check for formatting issues
- Try re-saving the file as CSV with UTF-8 encoding

#### Problem: "Missing required columns" error

**Solution:**
- Check the CSV Format Requirements section above
- Verify column names are spelled correctly
- Ensure no extra spaces in column names
- Check that all required columns are present

#### Problem: Upload succeeds but data looks wrong

**Solution:**
- Check date format is YYYY-MM-DD
- Verify numeric values don't contain text
- Look for special characters that might cause parsing issues
- Review the preview before confirming upload
- Try uploading a smaller sample first

#### Problem: "Duplicate dataset" warning

**Solution:**
- This means you've already uploaded this exact file
- You can upload anyway if you want a duplicate
- Or cancel and use the existing dataset
- Check the upload date to identify the existing dataset

### Ask Issues

#### Problem: "No relevant data found" for queries

**Solution:**
- Ensure you've uploaded data first
- Check that data was indexed (may take a few minutes)
- Try rephrasing your question
- Be more specific in your query
- Verify the dataset contains relevant information

#### Problem: Queries are very slow

**Solution:**
- Ollama may be processing on CPU (slower than GPU)
- Close other applications to free up resources
- Try simpler questions
- Clear conversation context and start fresh
- Consider upgrading hardware

#### Problem: Answers don't make sense

**Solution:**
- Check if the question is clear and specific
- Verify the uploaded data is relevant to your question
- Try breaking complex questions into simpler parts
- Clear context and rephrase the question
- Review the citations to see what data was used

### Analysis Issues

#### Problem: "Insufficient data for analysis"

**Solution:**
- Upload more survey responses (minimum 20-30 recommended)
- Ensure responses contain text (not all empty)
- Check that you selected the correct dataset
- Verify the dataset type is "survey"

#### Problem: Themes don't seem accurate

**Solution:**
- Theme identification works best with 50+ responses
- Ensure responses are in English
- Check that responses are substantive (not just "yes" or "no")
- Review representative quotes to understand the themes
- Consider manual review for small datasets

#### Problem: Sentiment analysis seems wrong

**Solution:**
- Sentiment analysis is not perfect—it's a tool to assist, not replace human judgment
- Review individual responses to verify
- Consider context and sarcasm (which AI may miss)
- Use sentiment as a general indicator, not absolute truth

### Visualization Issues

#### Problem: "Cannot generate chart" error

**Solution:**
- Verify dataset has appropriate data for the chart type
- Check that selected columns contain the right data types
- Ensure numeric columns for Y-axis (bar/line charts)
- Try a different chart type
- Check for missing or invalid data

#### Problem: Chart looks wrong or empty

**Solution:**
- Verify you selected the correct columns
- Check data types (dates, numbers, text)
- Ensure dataset has data in the selected columns
- Try filtering or cleaning the data
- Review the data preview before creating charts

### Report Generation Issues

#### Problem: Report generation fails or times out

**Solution:**
- Try generating report with fewer datasets
- Disable visualizations temporarily
- Check Ollama is running and responsive
- Ensure sufficient disk space
- Try Markdown export instead of PDF

#### Problem: PDF export fails

**Solution:**
- Try Markdown export instead
- Check disk space and write permissions
- Ensure all dependencies are installed
- Review terminal for error messages
- Restart the application

#### Problem: Report is missing sections

**Solution:**
- Verify you selected the correct datasets
- Check if qualitative analysis was performed
- Ensure visualizations option is enabled
- Review the report preview before exporting
- Try regenerating the report

---

## Frequently Asked Questions

### General Questions

**Q: Do I need an internet connection to use this system?**

A: You need internet to download Ollama, the language model, and install the application. After setup, the system works completely offline. All AI processing happens locally on your computer.

**Q: How much does this system cost?**

A: The system is free and open-source. You only need a computer that meets the system requirements. There are no subscription fees or API costs.

**Q: Can multiple people use the system at the same time?**

A: The system is designed for single-user deployment. Each user should have their own installation on their own computer. For multi-user access, you would need to set up a server deployment (not covered in this guide).

**Q: How long does it take to process data?**

A: Processing time depends on data size and your computer's hardware:
- CSV upload: Seconds to minutes
- Query responses: 5-30 seconds
- Qualitative analysis: 1-5 minutes for 100 responses
- Report generation: 1-5 minutes

**Q: What languages are supported?**

A: The system is designed for English text. Other languages may work but are not officially supported or tested.

### Data and Privacy Questions

**Q: Is my data secure?**

A: Yes. All data stays on your computer. The system doesn't send data to external servers or cloud services. You control access through password authentication. Follow the security best practices in this guide.

**Q: Can I share my data with others?**

A: You can export datasets and reports to share with others. However, ensure you follow your institution's data sharing policies and remove any PII before sharing.

**Q: How do I delete my data?**

A: Use the "Delete" button on the Data Upload page to remove individual datasets. To completely remove all data, delete the `data/` folder. To start fresh, run the initialization script again.

**Q: What happens to deleted data?**

A: Deleted datasets are permanently removed from the database. This includes all associated analysis results and indexed documents. Deletion cannot be undone, so ensure you have backups if needed.

**Q: Does the system collect any usage data?**

A: The system logs access for audit purposes (username, action, timestamp). These logs are stored locally in your database. No usage data is sent to external services.

### Technical Questions

**Q: Can I use a different language model?**

A: Yes. You can use any model supported by Ollama. Edit `config/settings.py` to change the model name. Recommended models: llama3.2:3b, phi3:mini, mistral:7b.

**Q: Can I run this on a server?**

A: The system is designed for desktop use but can be adapted for server deployment. This requires additional configuration for multi-user access, authentication, and security. Consult with IT staff for server deployment.

**Q: How do I backup my data?**

A: Copy the entire `data/` folder to a secure location. This includes:
- `data/library.db` (database)
- `data/chroma_db/` (vector store)

To restore, copy these files back to the `data/` folder.

**Q: Can I customize the system?**

A: Yes. The system is open-source and can be customized. You'll need Python programming knowledge to modify the code. See the developer documentation for details.

**Q: What if I encounter a bug?**

A: Check the Troubleshooting section first. If the issue persists, check the error messages in the terminal, review the logs, and consult with technical support or the system administrator.

### Usage Questions

**Q: How many datasets can I upload?**

A: There's no hard limit, but performance may degrade with very large numbers of datasets (>100). The system is designed for typical library assessment needs (5-20 datasets).

**Q: Can I edit data after uploading?**

A: You cannot edit data directly in the system. To make changes, edit your CSV file and re-upload it. You can delete the old dataset first or keep both versions.

**Q: How accurate is the sentiment analysis?**

A: Sentiment analysis is approximately 70-80% accurate for typical library feedback. It's a tool to assist your analysis, not replace human judgment. Always review results and use your professional expertise.

**Q: How accurate are the AI-generated answers?**

A: The AI generates answers based on your uploaded data. Accuracy depends on data quality and question clarity. Always verify answers by checking the citations and reviewing the source data. The AI is a tool to assist, not replace, your expertise.

**Q: Can I use this for other types of data?**

A: The system is designed for library assessment data but can be adapted for similar use cases. The CSV format is flexible, and you can use the survey response format for any text-based feedback.

### Workflow Questions

**Q: What's the recommended workflow?**

A: 
1. Upload your CSV data with metadata
2. Use the Ask to explore your data
3. Run Qualitative Analysis on survey responses
4. Create visualizations for key metrics
5. Generate comprehensive reports
6. Export and share results

**Q: How often should I upload new data?**

A: Upload data as frequently as you collect it. Monthly or quarterly uploads are common for library assessment. You can upload multiple datasets and compare them over time.

**Q: Should I keep old datasets?**

A: Yes, keeping historical data allows you to track trends over time. However, follow your institution's data retention policies. Delete datasets when they're no longer needed.

**Q: Can I combine data from different sources?**

A: Yes. Upload each source as a separate dataset. The Ask can search across all datasets. Reports can combine multiple datasets for comprehensive analysis.

---

## Additional Resources

### Sample Data

The `../test_data/` folder contains sample CSV files you can use to learn the system:
- `sample_survey_responses.csv`: Example survey data
- `sample_usage_statistics.csv`: Example usage metrics
- `sample_circulation_data.csv`: Example circulation data

Try uploading these files to familiarize yourself with the system before using your own data.

### Documentation Files

- `../README.md`: Technical setup and developer information
- `ARCHITECTURE.md`: System design and architecture for developers
- `../test_data/README.md`: Detailed information about sample data

### Getting Help

If you need assistance:
1. Review this User Guide
2. Check the Troubleshooting section
3. Review error messages in the terminal
4. Consult with your IT department
5. Contact your system administrator

### Tips for Success

1. **Start small**: Upload a small dataset first to learn the system
2. **Use sample data**: Practice with the provided sample files
3. **Add metadata**: Take time to document your datasets properly
4. **Ask clear questions**: Specific queries get better answers
5. **Review results**: Always verify AI-generated insights
6. **Export regularly**: Save your analysis and reports
7. **Follow best practices**: Maintain data privacy and security
8. **Keep learning**: Experiment with different features and workflows

---

## Conclusion

The Library Assessment Decision Support System is a powerful tool for library assessment that maintains privacy-conscious local processing practices. By processing everything locally, you can leverage AI capabilities while supporting privacy-conscious local processing.

This system is designed to assist your work, not replace your professional judgment. Use it to:
- Save time on data analysis
- Discover insights in large datasets
- Generate professional reports
- Track trends over time
- Make data-driven decisions

Remember: The AI is a tool to augment your expertise. Always review results, verify findings, and apply your professional knowledge to interpret the data.

**Thank you for using the Library Assessment Assistant!**

---

*Document Version: 1.0*  
*Last Updated: 2024*  
*For technical support, contact your system administrator*

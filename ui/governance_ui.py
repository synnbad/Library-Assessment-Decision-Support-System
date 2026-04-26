"""
Data Governance UI Module

This module provides comprehensive documentation on FAIR and CARE principles,
data collection practices, privacy protections, and ethical use guidelines.
"""

import streamlit as st
from modules import csv_handler, query_intelligence
from ui import smart_guidance


def show_data_governance_page():
    """Display data governance documentation page with FAIR and CARE principles."""
    st.title("Data Governance")
    st.markdown("### Responsible Data Management for Library Assessment")
    
    st.markdown("""
    This system follows **FAIR** (Findable, Accessible, Interoperable, Reusable) and 
    **CARE** (Collective Benefit, Authority to Control, Responsibility, Ethics) principles 
    to ensure responsible and ethical management of library assessment data.
    """)

    _display_governance_readiness()
    
    _display_fair_principles()
    _display_care_principles()
    _display_data_collection_and_use()
    _display_privacy_protections()
    _display_ethical_guidelines()
    _display_user_control_mechanisms()
    _display_additional_resources()


def _display_governance_readiness():
    """Display live metadata and data-readiness signals for uploaded datasets."""
    datasets = csv_handler.get_datasets()
    st.markdown("---")
    st.markdown("## Governance Readiness")
    if not datasets:
        st.info("Upload a dataset to see FAIR/CARE readiness checks.")
        return

    profiles = []
    metadata_gaps = []
    for dataset in datasets:
        try:
            profile = smart_guidance.build_profile(dataset)
            if profile:
                profiles.append(profile)
        except Exception:
            pass
        missing = [
            field
            for field in ("title", "description", "source", "usage_notes", "ethical_considerations")
            if not dataset.get(field)
        ]
        if missing:
            metadata_gaps.append((dataset["name"], missing))

    summary = query_intelligence.combine_profiles(profiles)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Datasets", len(datasets))
    with col2:
        st.metric("Profiled Rows", f"{summary['total_rows']:,}" if profiles else "0")
    with col3:
        st.metric("Metadata Gaps", len(metadata_gaps))

    if metadata_gaps:
        with st.expander("Metadata Fields to Improve", expanded=True):
            for name, missing in metadata_gaps:
                st.warning(f"{name}: add {', '.join(missing)}")
    else:
        st.success("All datasets include the core governance metadata fields.")

    warnings = [warning for profile in profiles for warning in profile.warnings]
    if warnings:
        with st.expander("Data Quality Signals", expanded=False):
            for warning in warnings[:10]:
                st.warning(warning)

    questions = []
    for profile in profiles[:3]:
        questions.append(f"What limitations should I document for {profile.name}?")
        questions.append(f"What ethical considerations apply to {profile.name}?")
    if questions:
        st.markdown("### Governance Questions")
        smart_guidance.display_question_buttons(
            questions,
            key_prefix="governance_question",
            limit=5,
        )


def _display_fair_principles():
    """Display FAIR principles section."""
    st.markdown("---")
    st.markdown("## FAIR Principles")
    st.markdown("""
    FAIR principles ensure that research data is managed in ways that support discovery, 
    access, integration, and reuse by both humans and machines.
    """)
    
    with st.expander("**F - Findable**", expanded=False):
        st.markdown("""
        Data should be easy to find for both humans and computers.
        
        **How This System Implements Findability:**
        
        - **Rich Metadata**: Each dataset includes title, description, source, keywords, and upload date
        - **Unique Identifiers**: Every dataset has a unique ID for precise referencing
        - **Data Manifest**: Generate a comprehensive manifest listing all datasets with metadata
        - **Searchable Fields**: Metadata fields are stored in a searchable database
        - **Keywords**: Tag datasets with keywords to support discovery
        
        **Example:** When you upload a survey dataset, you can add keywords like "undergraduate", 
        "spring 2024", "user satisfaction" to make it easily discoverable later.
        """)
    
    with st.expander("**A - Accessible**", expanded=False):
        st.markdown("""
        Data should be accessible to authorized users through well-defined protocols.
        
        **How This System Implements Accessibility:**
        
        - **Authentication**: Password-protected access ensures only authorized users can view data
        - **Export Functionality**: Download datasets in standard formats (CSV, JSON)
        - **Clear Documentation**: User guides explain how to access and use the system
        - **Audit Logging**: All data access is logged with timestamps for transparency
        - **Local Access**: Data remains on your local machine, under your control
        
        **Example:** You can export any dataset as CSV or JSON to use in other analysis tools 
        like Excel, R, or Python.
        """)
    
    with st.expander("**I - Interoperable**", expanded=False):
        st.markdown("""
        Data should use standard formats and vocabularies to integrate with other systems.
        
        **How This System Implements Interoperability:**
        
        - **Standard Formats**: CSV and JSON export for compatibility with common tools
        - **SQLite Database**: Industry-standard database with documented schema
        - **JSON Metadata**: Machine-readable metadata format
        - **Pandas DataFrames**: Compatible with Python data science ecosystem
        - **Standard Visualizations**: Charts export as PNG and HTML for universal viewing
        
        **Example:** Export your analysis results as CSV to import into Tableau, Power BI, 
        or statistical software like SPSS or R.
        """)
    
    with st.expander("**R - Reusable**", expanded=False):
        st.markdown("""
        Data should be well-described and licensed so it can be reused in different contexts.
        
        **How This System Implements Reusability:**
        
        - **Data Provenance**: Track all transformations and analysis methods applied to data
        - **Usage Notes**: Document context and guidance for responsible reuse
        - **Source Information**: Record where data came from and how it was collected
        - **Ethical Considerations**: Document any restrictions or ethical guidelines
        - **Complete Metadata**: Comprehensive information supports informed reuse
        
        **Example:** The system tracks when you perform sentiment analysis, recording the method 
        (TextBlob), parameters, and timestamp so future users understand how results were generated.
        """)


def _display_care_principles():
    """Display CARE principles section."""
    st.markdown("---")
    st.markdown("## CARE Principles")
    st.markdown("""
    CARE principles complement FAIR by emphasizing people and purpose in data governance, 
    particularly for data about communities and individuals.
    """)
    
    with st.expander("**C - Collective Benefit**", expanded=False):
        st.markdown("""
        Data ecosystems should be designed to enable data to benefit the community it represents.
        
        **How This System Implements Collective Benefit:**
        
        - **Library Service Improvement**: Analysis results help improve library services for all users
        - **Usage Notes Field**: Document how data benefits the library community
        - **Report Generation**: Create reports that support institutional goals and decision-making
        - **Shared Insights**: Analysis results can be shared to benefit library assessment community
        - **Transparent Purpose**: Clear documentation of intended uses and benefits
        
        **Example:** Survey analysis revealing that students need more quiet study spaces can 
        lead to improvements that benefit the entire student community.
        """)
    
    with st.expander("**A - Authority to Control**", expanded=False):
        st.markdown("""
        People and communities should have authority over how their data is governed and used.
        
        **How This System Implements Authority to Control:**
        
        - **User Control**: You decide what data to upload, retain, or delete
        - **Metadata Editing**: Update context and usage restrictions at any time
        - **Dataset Deletion**: Remove datasets completely when no longer needed
        - **Local Processing**: Data never leaves your control - no external transmission
        - **Access Documentation**: Clear information about who can access data and what they can do
        - **Export Rights**: Download your data anytime in standard formats
        
        **Example:** You have complete control to delete any dataset, edit its metadata to add 
        usage restrictions, or export it for use elsewhere.
        """)
    
    with st.expander("**R - Responsibility**", expanded=False):
        st.markdown("""
        Those working with data have a responsibility to share how data is used and to nurture relationships.
        
        **How This System Implements Responsibility:**
        
        - **Ethical Considerations Field**: Document responsible use guidelines for each dataset
        - **Data Provenance Tracking**: Complete transparency about all transformations and analyses
        - **Audit Logging**: Every data access is logged for accountability
        - **PII Protection**: Automatic detection and redaction of personally identifiable information
        - **FERPA Compliance**: Student data protection built into system design
        - **Citation Requirements**: All reports include citations showing data sources used
        
        **Example:** When you run qualitative analysis, the system records exactly what method 
        was used, when, and by whom, creating a complete audit trail.
        """)
    
    with st.expander("**E - Ethics**", expanded=False):
        st.markdown("""
        Data practices should minimize harm and maximize benefit, respecting ethical norms and rights.
        
        **How This System Implements Ethics:**
        
        - **Privacy by Design**: Local-only processing ensures data never leaves your institution
        - **PII Redaction**: Automatic protection of personally identifiable information
        - **Ethical Use Documentation**: This page explains ethical principles and guidelines
        - **FERPA Compliance**: Full compliance with student data privacy regulations
        - **No External APIs**: No data sent to external services or AI providers
        - **Informed Use**: Clear documentation of data collection and use purposes
        
        **Example:** All AI processing happens locally via Ollama - student data never goes to 
        OpenAI, Google, or any external service.
        """)


def _display_data_collection_and_use():
    """Display data collection and use section."""
    st.markdown("---")
    st.markdown("## Data Collection and Use")
    
    with st.expander("**What Data Is Collected**", expanded=False):
        st.markdown("""
        This system collects and stores the following types of data:
        
        **Library Assessment Data:**
        - Survey responses (open-ended and structured feedback)
        - Usage statistics (circulation, database access, resource usage)
        - Circulation data (borrowing patterns, material types)
        
        **System Metadata:**
        - Dataset names, descriptions, and upload dates
        - User authentication information (usernames and hashed passwords)
        - Access logs (who accessed what data and when)
        - Analysis provenance (what analyses were performed and when)
        
        **Generated Data:**
        - Sentiment analysis results
        - Identified themes and keywords
        - Statistical summaries
        - Generated reports and visualizations
        
        **What Is NOT Collected:**
        - No telemetry or usage analytics sent to external services
        - No personally identifiable information beyond what you upload
        - No tracking of user behavior outside the system
        """)
    
    with st.expander("**How Data Is Used**", expanded=False):
        st.markdown("""
        Data in this system is used exclusively for library assessment purposes:
        
        **Primary Uses:**
        - **Question Answering**: RAG engine retrieves relevant data to answer your questions
        - **Qualitative Analysis**: Sentiment analysis and theme identification in survey responses
        - **Statistical Analysis**: Descriptive statistics and trend analysis
        - **Report Generation**: Creating comprehensive assessment reports for stakeholders
        - **Visualization**: Generating charts to communicate findings
        
        **Data Processing:**
        - All processing happens locally on your machine
        - AI/LLM processing uses locally-running Ollama (no external API calls)
        - Vector embeddings stored locally in ChromaDB
        - No data transmitted to external services
        
        **Data Retention:**
        - Data persists until you explicitly delete it
        - You control the lifecycle of all datasets
        - No automatic deletion or archiving
        
        **Data Sharing:**
        - Data is not shared with any external parties
        - You control all exports and report generation
        - Reports you generate can be shared at your discretion
        """)
    
    with st.expander("**Who Has Access**", expanded=False):
        st.markdown("""
        Access to data in this system is controlled and logged:
        
        **Access Control:**
        - **Authentication Required**: All users must log in with username and password
        - **Single-User System**: Designed for individual use on a local machine
        - **No Remote Access**: System runs locally, not accessible over network
        - **Password Protection**: Passwords hashed with bcrypt for security
        
        **Access Logging:**
        - Every data access operation is logged with timestamp
        - Logs include: username, action performed, and dataset accessed
        - Audit trail supports accountability and compliance
        - Logs stored in local SQLite database
        
        **User Permissions:**
        - All authenticated users have full access to all features
        - No role-based access control in MVP version
        - Users can view, analyze, export, and delete any dataset
        
        **Physical Access:**
        - Data stored on your local machine only
        - Physical security of the machine is your responsibility
        - Consider encrypting your hard drive for additional protection
        """)


def _display_privacy_protections():
    """Display privacy protections section."""
    st.markdown("---")
    st.markdown("## Privacy Protections")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Local Processing
        
        **All data processing happens on your local machine:**
        
        - No external API calls
        - No cloud services
        - No data transmission
        - Complete data sovereignty
        
        **AI Processing:**
        - Ollama runs locally (Llama 3.2 3B)
        - ChromaDB in embedded mode
        - No OpenAI, Google, or other external AI services
        
        **Benefits:**
        - FERPA compliant by design
        - No internet required for processing
        - No subscription fees or API costs
        - Complete control over your data
        """)
    
    with col2:
        st.markdown("""
        ### PII Protection
        
        **Automatic protection of personal information:**
        
        - PII detection in outputs
        - Redaction of sensitive data
        - Flagging of potential privacy issues
        - FERPA compliance measures
        
        **Protected Information:**
        - Email addresses
        - Phone numbers
        - Social Security Numbers
        - Student IDs (when detected)
        
        **Best Practices:**
        - Remove PII before uploading data
        - Review outputs before sharing
        - Use aggregate data when possible
        - Follow institutional IRB guidelines
        """)
    
    st.markdown("""
    ### Access Logging and Audit Trail
    
    **Complete transparency and accountability:**
    
    - Every data access is logged with timestamp
    - User actions tracked (upload, query, analysis, export, delete)
    - Audit logs support compliance requirements
    - Logs stored securely in local database
    
    **Audit Log Information:**
    - Username of person performing action
    - Type of action (e.g., "Uploaded dataset", "Generated report")
    - Timestamp of action
    - Details about what data was accessed
    
    **Use Cases:**
    - Demonstrate FERPA compliance
    - Investigate data access questions
    - Support institutional audits
    - Track data usage patterns
    """)


def _display_ethical_guidelines():
    """Display ethical use guidelines section."""
    st.markdown("---")
    st.markdown("## Ethical Use Guidelines")
    
    st.markdown("""
    ### Principles for Responsible Library Assessment Data Use
    
    When using this system for library assessment, please follow these ethical guidelines:
    """)
    
    with st.expander("**1. Respect Privacy and Confidentiality**", expanded=False):
        st.markdown("""
        - Remove personally identifiable information before uploading data
        - Aggregate data when possible to protect individual privacy
        - Be cautious when sharing reports that might identify individuals
        - Follow your institution's IRB requirements for human subjects research
        - Consider whether consent was obtained for the intended use
        """)
    
    with st.expander("**2. Use Data for Intended Purposes Only**", expanded=False):
        st.markdown("""
        - Use data only for library assessment and service improvement
        - Do not repurpose data for unrelated uses without proper authorization
        - Respect any usage restrictions documented in dataset metadata
        - Consider the original context in which data was collected
        - Document intended purposes in the "Usage Notes" field
        """)
    
    with st.expander("**3. Maintain Data Quality and Integrity**", expanded=False):
        st.markdown("""
        - Ensure uploaded data is accurate and complete
        - Document any data cleaning or transformation steps
        - Preserve original data alongside processed versions
        - Be transparent about data limitations and biases
        - Use appropriate statistical methods for your data type
        """)
    
    with st.expander("**4. Provide Context and Avoid Misinterpretation**", expanded=False):
        st.markdown("""
        - Include sufficient context when sharing findings
        - Acknowledge limitations of AI-generated analysis
        - Verify important findings before making decisions
        - Consider multiple interpretations of qualitative data
        - Be cautious about causal claims from correlational data
        """)
    
    with st.expander("**5. Promote Equity and Avoid Harm**", expanded=False):
        st.markdown("""
        - Consider how findings might affect different user groups
        - Avoid reinforcing stereotypes or biases in interpretation
        - Use inclusive language in reports and documentation
        - Consider accessibility in visualizations and reports
        - Be mindful of power dynamics in data collection and use
        """)
    
    with st.expander("**6. Ensure Transparency and Accountability**", expanded=False):
        st.markdown("""
        - Document data sources and analysis methods
        - Maintain audit logs of data access and use
        - Be prepared to explain how findings were generated
        - Cite data sources appropriately in reports
        - Share methodological details with stakeholders
        """)


def _display_user_control_mechanisms():
    """Display user control mechanisms section."""
    st.markdown("---")
    st.markdown("## User Access and Control Mechanisms")
    
    st.markdown("""
    You have complete control over your data in this system. Here's what you can do:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Data Management
        
        **Upload Control:**
        - Choose what data to upload
        - Add rich metadata (title, description, keywords)
        - Document usage notes and ethical considerations
        - Validate data before storing
        
        **Metadata Management:**
        - Edit metadata at any time
        - Update usage notes and restrictions
        - Add or modify keywords for findability
        - Document data provenance
        
        **Data Deletion:**
        - Delete any dataset completely
        - Cascade deletion removes all associated data
        - No recovery after deletion (permanent)
        - Deletion is logged in audit trail
        """)
    
    with col2:
        st.markdown("""
        ### Export and Portability
        
        **Dataset Export:**
        - Export any dataset as CSV or JSON
        - Download data manifest with all metadata
        - Take your data to other tools
        - No vendor lock-in
        
        **Analysis Export:**
        - Export analysis results as CSV
        - Download charts as PNG or HTML
        - Export reports as PDF or Markdown
        - Share findings on your terms
        
        **Complete Portability:**
        - All data in standard formats
        - SQLite database is portable
        - No proprietary formats
        - Easy migration to other systems
        """)
    
    st.markdown("""
    ### Access Control
    
    **Authentication:**
    - Password-protected access to all features
    - Secure password hashing (bcrypt)
    - Session management for security
    - Logout functionality
    
    **Audit and Monitoring:**
    - View access logs (feature can be added)
    - Track who accessed what data
    - Monitor system usage
    - Support compliance requirements
    
    **Data Sovereignty:**
    - All data stays on your machine
    - No external transmission
    - You control physical access
    - No cloud dependencies
    """)


def _display_additional_resources():
    """Display additional resources section."""
    st.markdown("---")
    st.markdown("## Additional Resources")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Learn More About FAIR
        
        - [GO FAIR Initiative](https://www.go-fair.org/)
        - [FAIR Principles](https://www.go-fair.org/fair-principles/)
        - [FAIR Data Maturity Model](https://www.go-fair.org/fair-principles/fairification-process/)
        
        ### Learn More About CARE
        
        - [CARE Principles for Indigenous Data Governance](https://www.gida-global.org/care)
        - [Global Indigenous Data Alliance](https://www.gida-global.org/)
        """)
    
    with col2:
        st.markdown("""
        ### Privacy and Compliance
        
        - [FERPA Overview (US Dept of Education)](https://www2.ed.gov/policy/gen/guid/fpco/ferpa/index.html)
        - [Library Privacy Guidelines (ALA)](https://www.ala.org/advocacy/privacy)
        - [Research Data Management](https://www.icpsr.umich.edu/web/pages/datamanagement/)
        
        ### Ethical Data Use
        
        - [Data Ethics Framework](https://www.gov.uk/government/publications/data-ethics-framework)
        - [Responsible Data Science](https://dataresponsibly.github.io/)
        """)
    
    st.markdown("---")
    st.markdown("""
    ### Questions or Concerns?
    
    If you have questions about data governance, privacy, or ethical use of this system, 
    please consult with your institution's:
    
    - Institutional Review Board (IRB)
    - Data Protection Officer
    - Library Administration
    - IT Security Team
    
    This system is designed to support responsible data practices, but institutional policies 
    and guidelines should always be followed.
    """)

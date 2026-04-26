"""
Data Upload UI Module

This module provides the user interface for uploading CSV datasets with FAIR/CARE metadata.
Includes file validation, metadata auto-detection, and dataset management functionality.
"""

import streamlit as st
import json
import pandas as pd
from modules import csv_handler, auth, data_importer
from modules import query_intelligence
from modules import query_queue


def show_data_upload_page():
    """Display data upload page with CSV uploader and FAIR/CARE metadata."""
    st.title("Data Upload")
    st.markdown("Import library assessment data with FAIR/CARE metadata and automatic profiling.")
    
    # Create tabs for upload and manage datasets
    tab1, tab2 = st.tabs(["Upload New Dataset", "Manage Datasets"])
    
    with tab1:
        _show_upload_tab()
    
    with tab2:
        _show_manage_tab()


def _show_upload_tab():
    """Display the upload new dataset tab."""
    st.markdown("### Import New Dataset")
    
    st.info("Tip: CSV, TSV, Excel, and JSON uploads are normalized into analysis-ready tables.")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a data file",
        type=list(data_importer.SUPPORTED_EXTENSIONS),
        help="Upload CSV, TSV, Excel, or JSON data from surveys, ILS, COUNTER, LibCal, LibAnswers, benchmark, or vendor systems."
    )
    
    if uploaded_file is not None:
        try:
            parsed_import = data_importer.parse_assessment_file(uploaded_file, uploaded_file.name)
            df = parsed_import.dataframe
            detected_type = parsed_import.detected_type
            uploaded_file.seek(0)
        except Exception as e:
            st.error(f"Unable to import this file: {e}")
            return

        # Dataset type selection
        type_options = data_importer.DATASET_TYPES
        default_index = type_options.index(detected_type) if detected_type in type_options else 0
        dataset_type = st.selectbox(
            "Dataset Type",
            type_options,
            index=default_index,
            format_func=lambda value: data_importer.DOMAIN_LABELS.get(value, value.title()),
            help="Detected from file name and columns; adjust if needed before upload."
        )

        if dataset_type != detected_type:
            df, override_notes = data_importer.normalize_assessment_dataframe(df, dataset_type)
            parsed_import.notes.extend(override_notes)
        
        # Show helpful information about dataset types
        st.caption(
            f"Detected as {data_importer.DOMAIN_LABELS.get(detected_type, detected_type)}. "
            f"Using {data_importer.DOMAIN_LABELS.get(dataset_type, dataset_type)} for analysis."
        )
        for note in parsed_import.notes:
            st.info(note)
        
        # Dataset name
        dataset_name = st.text_input(
            "Dataset Name",
            value=uploaded_file.name.replace('.csv', ''),
            help="A unique name for this dataset"
        )
        
        # Auto-detect metadata button
        col_auto1, col_auto2 = st.columns([1, 3])
        with col_auto1:
            auto_detect = st.button("Auto-Fill Metadata", help="Automatically detect metadata from the uploaded file")
        with col_auto2:
            if auto_detect:
                st.info("Analyzing dataset to auto-fill metadata fields...")
        
        # Initialize session state for metadata if not exists
        if 'metadata_title' not in st.session_state:
            st.session_state.metadata_title = ""
        if 'metadata_description' not in st.session_state:
            st.session_state.metadata_description = ""
        if 'metadata_source' not in st.session_state:
            st.session_state.metadata_source = ""
        if 'metadata_keywords' not in st.session_state:
            st.session_state.metadata_keywords = ""
        
        # Auto-detect metadata if button clicked
        if auto_detect:
            try:
                auto_metadata = csv_handler.auto_detect_metadata(df, dataset_type, uploaded_file.name)
                
                st.session_state.metadata_title = auto_metadata.get('title', '')
                st.session_state.metadata_description = auto_metadata.get('description', '')
                st.session_state.metadata_source = auto_metadata.get('source', '')
                st.session_state.metadata_keywords = ', '.join(auto_metadata.get('keywords', []))
                
                st.success("Metadata auto-filled! Review and edit as needed.")
            except UnicodeDecodeError:
                st.warning("Unable to auto-detect metadata due to file encoding issues. Please fill in metadata manually.")
                st.caption("Tip: Try saving your CSV file with UTF-8 encoding for better compatibility.")
            except Exception as e:
                st.warning(f"Unable to auto-detect metadata: {str(e)}")
                st.caption("You can still fill in the metadata fields manually below.")
        
        # FAIR/CARE Metadata Section
        st.markdown("#### FAIR/CARE Metadata")
        st.markdown("Provide metadata to support findability, accessibility, and responsible data use.")
        
        with st.expander("Metadata Fields", expanded=True):
            title = st.text_input(
                "Title",
                value=st.session_state.metadata_title,
                help="Human-readable title for the dataset"
            )
            
            description = st.text_area(
                "Description",
                value=st.session_state.metadata_description,
                help="Detailed description of dataset contents and purpose"
            )
            
            source = st.text_input(
                "Source",
                value=st.session_state.metadata_source,
                help="Origin of the data (e.g., Qualtrics, ILS, manual entry)"
            )
            
            keywords_input = st.text_input(
                "Keywords (comma-separated)",
                value=st.session_state.metadata_keywords,
                help="Keywords for findability (e.g., survey, undergraduate, spring 2024)"
            )
            
            usage_notes = st.text_area(
                "Usage Notes",
                help="Context and guidance for responsible reuse of this data"
            )
            
            ethical_considerations = st.text_area(
                "Ethical Considerations",
                help="Ethical use notes and any restrictions on data use"
            )
        
        # Validate and preview
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            validate_button = st.button("Validate CSV", use_container_width=True)
        
        with col2:
            upload_button = st.button("Upload Dataset", type="primary", use_container_width=True)
        
        # Validation
        if validate_button or upload_button:
            # Calculate file hash
            file_content = uploaded_file.getvalue()
            file_hash = csv_handler.calculate_file_hash(file_content)
            uploaded_file.seek(0)
            
            # Check for duplicates
            duplicate = csv_handler.check_duplicate(file_hash)
            if duplicate:
                st.warning(f"Warning: This dataset has already been uploaded (detected by file hash). Upload date: {duplicate['upload_date']}")
                st.info("You can still upload it if you want to create a separate copy.")
            
            # Validate normalized tabular data
            is_valid, error_msg = csv_handler.validate_csv_dataframe(df, dataset_type)
            
            if not is_valid:
                st.error(f"Import validation failed: {error_msg}")
            else:
                st.success("Import validation passed.")
                
                # Show preview
                st.markdown("#### Preview")
                st.dataframe(df.head(10), use_container_width=True)
                st.caption(f"Showing first 10 rows of {len(df)} total rows")
                _display_data_dictionary(data_importer.build_data_dictionary(df))
                profile = query_intelligence.build_dataset_profile(
                    df,
                    dataset_type=dataset_type,
                    dataset_name=dataset_name or uploaded_file.name,
                )
                _display_profile_guidance(profile, key_prefix="upload_preview")
                
                # Upload if button was clicked
                if upload_button:
                    if not dataset_name:
                        st.error("Please provide a dataset name.")
                    else:
                        try:
                            # Prepare metadata
                            keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
                            metadata = {
                                'title': title if title else None,
                                'description': description if description else None,
                                'source': source if source else None,
                                'keywords': keywords,
                                'usage_notes': usage_notes if usage_notes else None,
                                'ethical_considerations': ethical_considerations if ethical_considerations else None
                            }
                            
                            # Store dataset
                            dataset_id = csv_handler.store_dataset(
                                df,
                                dataset_name,
                                dataset_type,
                                file_hash,
                                metadata
                            )
                            
                            # Log access
                            auth.log_access(
                                st.session_state.username,
                                f"Uploaded dataset: {dataset_name} (ID: {dataset_id})"
                            )
                            
                            st.success(f"Dataset uploaded successfully! Dataset ID: {dataset_id}")
                            st.info(query_intelligence.recommended_next_action([profile]))
                            st.balloons()
                            
                        except Exception as e:
                            st.error(f"Error uploading dataset: {str(e)}")


def _show_manage_tab():
    """Display the manage datasets tab."""
    st.markdown("### Manage Datasets")
    
    # Get all datasets
    datasets = csv_handler.get_datasets()
    
    if not datasets:
        st.info("No datasets uploaded yet. Upload your first dataset in the 'Upload New Dataset' tab.")
    else:
        st.markdown(f"**Total Datasets:** {len(datasets)}")
        
        # Download data manifest button
        col1, col2 = st.columns([3, 1])
        with col2:
            manifest = csv_handler.generate_data_manifest()
            manifest_json = json.dumps(manifest, indent=2)
            st.download_button(
                "Download Data Manifest",
                data=manifest_json,
                file_name="data_manifest.json",
                mime="application/json",
                use_container_width=True
            )
        
        st.markdown("---")
        
        # Display each dataset
        for dataset in datasets:
            _display_dataset_card(dataset)


def _display_dataset_card(dataset):
    """Display a single dataset card with actions."""
    with st.expander(f"{dataset['name']} (ID: {dataset['id']})", expanded=False):
        # Basic info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Type", dataset['dataset_type'].title())
        with col2:
            st.metric("Rows", dataset['row_count'])
        with col3:
            st.metric("Uploaded", dataset['upload_date'][:10])

        try:
            preview_df = csv_handler.get_preview(dataset['id'], n_rows=1000)
            if not preview_df.empty:
                profile = query_intelligence.build_profile_from_dataset_record(dataset, preview_df)
                _display_profile_guidance(profile, key_prefix=f"managed_{dataset['id']}", compact=True)
        except Exception as e:
            st.caption(f"Dataset profile unavailable: {e}")

        # Analysis Capabilities
        caps = dataset.get('analysis_capabilities')
        if caps and caps.get('analyses'):
            st.markdown("#### Analysis Capabilities")
            analyses = caps['analyses']
            LABELS = {
                "qualitative_sentiment": "Sentiment Analysis",
                "qualitative_themes":    "Theme Extraction",
                "correlation":           "Correlation",
                "trend":                 "Trend Analysis",
                "comparative":           "Comparative Analysis",
                "distribution":          "Distribution Analysis",
                "rag_query":             "Natural Language Query",
            }
            cols = st.columns(4)
            for idx, (key, info) in enumerate(analyses.items()):
                with cols[idx % 4]:
                    label = LABELS.get(key, key)
                    if info['available']:
                        st.success(label)
                    else:
                        st.error(label)
            if caps.get('warnings'):
                for w in caps['warnings']:
                    st.warning(w)
            with st.expander("Details", expanded=False):
                for key, info in analyses.items():
                    label = LABELS.get(key, key)
                    status = "[OK]" if info['available'] else "[N/A]"
                    st.markdown(f"{status} **{label}**: {info['reason']}")
            if caps.get("data_dictionary"):
                _display_data_dictionary(caps["data_dictionary"], expanded=False)
        elif not caps:
            # Dataset uploaded before this feature - show re-evaluate button
            if st.button("Evaluate Capabilities", key=f"eval_{dataset['id']}"):
                try:
                    df_preview = csv_handler.get_preview(dataset['id'], n_rows=10000)
                    new_caps = csv_handler.evaluate_dataset_capabilities(
                        df_preview, dataset['dataset_type'], dataset['id']
                    )
                    import json as _json
                    from modules.database import execute_update as _eu
                    _eu("UPDATE datasets SET analysis_capabilities = ? WHERE id = ?",
                        (_json.dumps(new_caps), dataset['id']))
                    st.success("Capabilities evaluated - refresh to see results.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not evaluate: {e}")

        # FAIR/CARE Metadata
        st.markdown("#### Metadata")
        
        if dataset.get('title'):
            st.markdown(f"**Title:** {dataset['title']}")
        
        if dataset.get('description'):
            st.markdown(f"**Description:** {dataset['description']}")
        
        if dataset.get('source'):
            st.markdown(f"**Source:** {dataset['source']}")
        
        if dataset.get('keywords'):
            keywords_display = ', '.join(dataset['keywords'])
            st.markdown(f"**Keywords:** {keywords_display}")
        
        if dataset.get('usage_notes'):
            st.markdown(f"**Usage Notes:** {dataset['usage_notes']}")
        
        if dataset.get('ethical_considerations'):
            st.markdown(f"**Ethical Considerations:** {dataset['ethical_considerations']}")
        
        st.markdown("---")
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Edit metadata button
            if st.button("Edit Metadata", key=f"edit_{dataset['id']}"):
                st.session_state[f"editing_{dataset['id']}"] = True
        
        with col2:
            # Export CSV button
            csv_data = csv_handler.export_dataset(dataset['id'], 'csv')
            if csv_data:
                st.download_button(
                    "Export CSV",
                    data=csv_data,
                    file_name=f"{dataset['name']}.csv",
                    mime="text/csv",
                    key=f"export_csv_{dataset['id']}"
                )
        
        with col3:
            # Export JSON button
            json_data = csv_handler.export_dataset(dataset['id'], 'json')
            if json_data:
                st.download_button(
                    "Export JSON",
                    data=json_data,
                    file_name=f"{dataset['name']}.json",
                    mime="application/json",
                    key=f"export_json_{dataset['id']}"
                )
        
        with col4:
            # Delete button
            if st.button("Delete", key=f"delete_{dataset['id']}", type="secondary"):
                st.session_state[f"confirm_delete_{dataset['id']}"] = True
        
        # Edit metadata form
        if st.session_state.get(f"editing_{dataset['id']}", False):
            _show_edit_metadata_form(dataset)
        
        # Delete confirmation
        if st.session_state.get(f"confirm_delete_{dataset['id']}", False):
            _show_delete_confirmation(dataset)


def _display_profile_guidance(profile, key_prefix: str, compact: bool = False):
    """Display dataset-aware brief, quality notes, and question starters."""
    st.markdown("#### Dataset Brief")
    st.markdown(query_intelligence.generate_dataset_brief(profile))

    if profile.strengths:
        cols = st.columns(min(3, len(profile.strengths)))
        for idx, strength in enumerate(profile.strengths):
            with cols[idx % len(cols)]:
                st.success(strength)

    if profile.warnings:
        with st.expander("Data Quality Notes", expanded=not compact):
            for warning in profile.warnings:
                st.warning(warning)

    suggestions = query_intelligence.suggest_questions(profile, limit=4 if compact else 6)
    if suggestions:
        st.markdown("#### Suggested Questions")
        for idx, question in enumerate(suggestions):
            if st.button(question, key=f"{key_prefix}_question_{idx}", use_container_width=True):
                query_queue.queue_question(st.session_state, question)
                st.success("Queued. Open Query Interface to review, edit, and run it.")


def _display_data_dictionary(dictionary, expanded: bool = True):
    """Display an inferred data dictionary in a compact table."""
    if not dictionary:
        return
    with st.expander("Inferred Data Dictionary", expanded=expanded):
        display_df = pd.DataFrame(dictionary)
        st.dataframe(
            display_df[["column", "type", "role", "missing_pct", "unique_count", "examples"]],
            use_container_width=True,
        )


def _show_edit_metadata_form(dataset):
    """Display the edit metadata form for a dataset."""
    st.markdown("#### Edit Metadata")
    with st.form(f"edit_form_{dataset['id']}"):
        new_title = st.text_input("Title", value=dataset.get('title', ''))
        new_description = st.text_area("Description", value=dataset.get('description', ''))
        new_source = st.text_input("Source", value=dataset.get('source', ''))
        
        current_keywords = ', '.join(dataset.get('keywords', []))
        new_keywords_input = st.text_input("Keywords (comma-separated)", value=current_keywords)
        
        new_usage_notes = st.text_area("Usage Notes", value=dataset.get('usage_notes', ''))
        new_ethical = st.text_area("Ethical Considerations", value=dataset.get('ethical_considerations', ''))
        
        col1, col2 = st.columns(2)
        with col1:
            save_button = st.form_submit_button("Save Changes", type="primary")
        with col2:
            cancel_button = st.form_submit_button("Cancel")
        
        if save_button:
            new_keywords = [k.strip() for k in new_keywords_input.split(',') if k.strip()]
            new_metadata = {
                'title': new_title if new_title else None,
                'description': new_description if new_description else None,
                'source': new_source if new_source else None,
                'keywords': new_keywords,
                'usage_notes': new_usage_notes if new_usage_notes else None,
                'ethical_considerations': new_ethical if new_ethical else None
            }
            
            if csv_handler.update_dataset_metadata(dataset['id'], new_metadata):
                st.success("Metadata updated successfully!")
                st.session_state[f"editing_{dataset['id']}"] = False
                
                # Log access
                auth.log_access(
                    st.session_state.username,
                    f"Updated metadata for dataset: {dataset['name']} (ID: {dataset['id']})"
                )
                st.rerun()
            else:
                st.error("Failed to update metadata.")
        
        if cancel_button:
            st.session_state[f"editing_{dataset['id']}"] = False
            st.rerun()


def _show_delete_confirmation(dataset):
    """Display delete confirmation dialog for a dataset."""
    st.warning(f"Warning: Are you sure you want to delete '{dataset['name']}'? This action cannot be undone.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, Delete", key=f"confirm_yes_{dataset['id']}", type="primary"):
            if csv_handler.delete_dataset(dataset['id']):
                st.success(f"Dataset '{dataset['name']}' deleted successfully!")
                
                # Log access
                auth.log_access(
                    st.session_state.username,
                    f"Deleted dataset: {dataset['name']} (ID: {dataset['id']})"
                )
                
                st.session_state[f"confirm_delete_{dataset['id']}"] = False
                st.rerun()
            else:
                st.error("Failed to delete dataset.")
    with col2:
        if st.button("Cancel", key=f"confirm_no_{dataset['id']}"):
            st.session_state[f"confirm_delete_{dataset['id']}"] = False
            st.rerun()

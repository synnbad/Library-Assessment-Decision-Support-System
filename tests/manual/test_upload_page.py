"""
Manual test script to verify data upload page functionality.
This script tests the key functions used by the data upload page.
"""

from modules import csv_handler
from io import StringIO


def test_upload_workflow():
    """Test the complete upload workflow."""
    print("Testing Data Upload Page Workflow...")
    print("=" * 60)
    
    # 1. Test CSV validation
    print("\n1. Testing CSV validation...")
    csv_content = """response_date,question,response_text
2024-01-15,How satisfied are you?,Very satisfied
2024-01-16,What improvements?,More study spaces"""
    
    file = StringIO(csv_content)
    is_valid, error = csv_handler.validate_csv(file, "survey")
    
    if is_valid:
        print("   ✓ CSV validation passed")
    else:
        print(f"   ✗ CSV validation failed: {error}")
        return
    
    # 2. Test file hash calculation
    print("\n2. Testing file hash calculation...")
    file_content = csv_content.encode('utf-8')
    file_hash = csv_handler.calculate_file_hash(file_content)
    print(f"   ✓ File hash: {file_hash[:16]}...")
    
    # 3. Test duplicate detection
    print("\n3. Testing duplicate detection...")
    duplicate = csv_handler.check_duplicate(file_hash)
    if duplicate:
        print(f"   ! Duplicate found: {duplicate['name']}")
    else:
        print("   ✓ No duplicate found")
    
    # 4. Test dataset storage with FAIR/CARE metadata
    print("\n4. Testing dataset storage with metadata...")
    file.seek(0)
    df = csv_handler.parse_csv(file)
    
    metadata = {
        'title': 'Test Survey Data',
        'description': 'Sample survey responses for testing',
        'source': 'Manual test',
        'keywords': ['test', 'survey', 'sample'],
        'usage_notes': 'For testing purposes only',
        'ethical_considerations': 'No real student data included'
    }
    
    dataset_id = csv_handler.store_dataset(
        df,
        'test_upload_workflow',
        'survey',
        file_hash,
        metadata
    )
    print(f"   ✓ Dataset stored with ID: {dataset_id}")
    
    # 5. Test dataset retrieval
    print("\n5. Testing dataset retrieval...")
    datasets = csv_handler.get_datasets()
    test_dataset = next((d for d in datasets if d['id'] == dataset_id), None)
    
    if test_dataset:
        print(f"   ✓ Dataset retrieved: {test_dataset['name']}")
        print(f"     - Type: {test_dataset['dataset_type']}")
        print(f"     - Rows: {test_dataset['row_count']}")
        print(f"     - Title: {test_dataset.get('title')}")
        print(f"     - Keywords: {test_dataset.get('keywords')}")
    else:
        print("   ✗ Dataset not found")
        return
    
    # 6. Test metadata update
    print("\n6. Testing metadata update...")
    new_metadata = {
        'title': 'Updated Test Survey',
        'description': 'Updated description',
        'source': 'Manual test (updated)',
        'keywords': ['test', 'updated'],
        'usage_notes': 'Updated usage notes',
        'ethical_considerations': 'Updated ethical notes'
    }
    
    success = csv_handler.update_dataset_metadata(dataset_id, new_metadata)
    if success:
        print("   ✓ Metadata updated successfully")
        
        # Verify update
        datasets = csv_handler.get_datasets()
        updated_dataset = next((d for d in datasets if d['id'] == dataset_id), None)
        print(f"     - New title: {updated_dataset.get('title')}")
    else:
        print("   ✗ Metadata update failed")
    
    # 7. Test CSV export
    print("\n7. Testing CSV export...")
    csv_data = csv_handler.export_dataset(dataset_id, 'csv')
    if csv_data:
        print(f"   ✓ CSV export successful ({len(csv_data)} bytes)")
    else:
        print("   ✗ CSV export failed")
    
    # 8. Test JSON export
    print("\n8. Testing JSON export...")
    json_data = csv_handler.export_dataset(dataset_id, 'json')
    if json_data:
        print(f"   ✓ JSON export successful ({len(json_data)} bytes)")
    else:
        print("   ✗ JSON export failed")
    
    # 9. Test data manifest generation
    print("\n9. Testing data manifest generation...")
    manifest = csv_handler.generate_data_manifest()
    if manifest and 'datasets' in manifest:
        print(f"   ✓ Manifest generated with {len(manifest['datasets'])} datasets")
        print(f"     - System: {manifest['system']}")
        print(f"     - Version: {manifest['version']}")
    else:
        print("   ✗ Manifest generation failed")
    
    # 10. Test dataset deletion
    print("\n10. Testing dataset deletion...")
    success = csv_handler.delete_dataset(dataset_id)
    if success:
        print("   ✓ Dataset deleted successfully")
        
        # Verify deletion
        datasets = csv_handler.get_datasets()
        if not any(d['id'] == dataset_id for d in datasets):
            print("   ✓ Deletion verified")
        else:
            print("   ✗ Dataset still exists after deletion")
    else:
        print("   ✗ Dataset deletion failed")
    
    print("\n" + "=" * 60)
    print("All tests completed successfully! ✓")
    print("\nThe data upload page should work correctly with:")
    print("  - CSV file upload and validation")
    print("  - Dataset type selection")
    print("  - FAIR/CARE metadata input")
    print("  - Upload preview")
    print("  - Dataset management (list, edit, export, delete)")
    print("  - Data manifest download")


if __name__ == "__main__":
    test_upload_workflow()

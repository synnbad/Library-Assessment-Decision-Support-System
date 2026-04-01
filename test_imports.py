try:
    from modules.csv_handler import validate_csv
    from modules.qualitative_analysis import analyze_dataset_sentiment
    from modules.report_generator import create_report
    from modules.database import init_database
    from config import settings
    print('All imports successful')
    print(f'DEPENDENCIES_AVAILABLE = True')
except ImportError as e:
    print(f'Import error: {e}')
    print(f'DEPENDENCIES_AVAILABLE = False')

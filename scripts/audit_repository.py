#!/usr/bin/env python3
"""
Repository Audit Script

Scans the repository structure and classifies files as:
- Canonical: Part of the Library Assessment Decision Support System
- Legacy: FastAPI/sentiment-analysis artifacts to be removed
- Shared: Used by both systems or ambiguous

Generates a structured audit report for review.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple


class RepositoryAuditor:
    """Audits repository structure and classifies artifacts."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.classifications = {
            "canonical": [],
            "legacy": [],
            "shared": [],
        }
        
    def classify_file(self, file_path: Path) -> Tuple[str, str]:
        """
        Classify a file as canonical, legacy, or shared.
        
        Returns:
            (classification, justification)
        """
        path_str = str(file_path)
        
        # Legacy FastAPI application code
        if "src/services/api.py" in path_str:
            return ("legacy", "FastAPI service endpoint")
        if "src/modeling/" in path_str:
            return ("legacy", "Sentiment model training/prediction code")
        if "src/models.py" in path_str:
            return ("legacy", "FastAPI request/response models")
        if "src/config.py" in path_str:
            return ("legacy", "FastAPI configuration")
        if "src/dataset.py" in path_str:
            return ("legacy", "Sentiment dataset handling")
            
        # Legacy FastAPI tests
        if "tests/integration/test_api.py" in path_str:
            return ("legacy", "FastAPI endpoint tests")
        if "tests/unit/test_classifier.py" in path_str:
            return ("legacy", "Sentiment classifier tests")
        if "tests/unit/test_models.py" in path_str:
            return ("legacy", "FastAPI model tests")
            
        # Legacy scripts
        if "scripts/run_demo.py" in path_str:
            return ("legacy", "FastAPI demo script")
        if "scripts/evaluate_model.py" in path_str:
            return ("legacy", "Sentiment model evaluation script")
        if "scripts/download_dataset.py" in path_str:
            return ("legacy", "Sentiment dataset download script")
            
        # Legacy frontend
        if "reports/web-demo/" in path_str:
            return ("legacy", "FastAPI web frontend")
            
        # Legacy documentation
        if "docs/HUGGINGFACE_QUICK_START.md" in path_str:
            return ("legacy", "Sentiment-specific documentation")
        if "docs/NLP_TECHNIQUES_AND_MODELS.md" in path_str:
            return ("legacy", "Sentiment-specific documentation")
            
        # Canonical Streamlit application
        if path_str == "streamlit_app.py":
            return ("canonical", "Main Streamlit application entry point")
        if path_str.startswith("modules/"):
            return ("canonical", "Core business logic modules")
        if path_str.startswith("config/"):
            return ("canonical", "Application configuration")
        if path_str.startswith("ui/"):
            return ("canonical", "Streamlit UI modules (to be created)")
            
        # Canonical data
        if path_str.startswith("data/library.db"):
            return ("canonical", "Application database")
        if path_str.startswith("data/chroma_db/"):
            return ("canonical", "Vector store for RAG")
        if path_str.startswith("data/raw/") and "library" in path_str:
            return ("canonical", "Library assessment data")
            
        # Canonical documentation
        if path_str == "README.md":
            return ("canonical", "Main project documentation (needs update)")
        if path_str == "ARCHITECTURE.md":
            return ("canonical", "Architecture documentation (needs update)")
        if path_str == "USER_GUIDE.md":
            return ("canonical", "User guide")
        if path_str == "TESTING.md":
            return ("canonical", "Testing documentation")
        if path_str.startswith("docs/") and any(x in path_str for x in [
            "AMIA", "COURSE", "DATA_", "METADATA", "MODULE", "PROJECT", "QUANTITATIVE"
        ]):
            return ("canonical", "Library assessment documentation")
            
        # Canonical tests
        if path_str.startswith("tests/") and not any(x in path_str for x in [
            "test_api.py", "test_classifier.py", "test_models.py"
        ]):
            return ("canonical", "Test suite for canonical features")
            
        # Shared/ambiguous files
        if path_str == "pyproject.toml":
            return ("shared", "Project metadata (needs update for canonical identity)")
        if path_str == "requirements.txt":
            return ("shared", "Dependencies (needs cleanup)")
        if path_str.startswith("test_data/"):
            return ("shared", "Test data (may be used by both systems)")
        if path_str.startswith("data/raw/") and "feedback" in path_str:
            return ("shared", "May be legacy sentiment data")
        if "scripts/init_app.py" in path_str:
            return ("shared", "Initialization script (may need updates)")
        if "test_imports.py" in path_str or "test_system.py" in path_str:
            return ("shared", "System test scripts (may need updates)")
            
        # Configuration files
        if path_str in [".gitignore", ".env.example", ".python-version"]:
            return ("canonical", "Standard configuration files")
            
        # Git and IDE files
        if path_str.startswith(".git/") or path_str.startswith(".vscode/") or path_str.startswith(".kiro/"):
            return ("canonical", "Version control and IDE configuration")
            
        # Build artifacts and caches
        if any(x in path_str for x in ["__pycache__", ".pytest_cache", "*.pyc"]):
            return ("canonical", "Build artifacts (not tracked)")
            
        # Default to shared if unclear
        return ("shared", "Requires manual review")
        
    def scan_directory(self, directory: Path = None) -> None:
        """Recursively scan directory and classify all files."""
        if directory is None:
            directory = self.root_path
            
        try:
            for item in directory.iterdir():
                # Skip hidden directories except .kiro
                if item.name.startswith('.') and item.name not in ['.kiro', '.gitignore', '.env.example', '.python-version']:
                    continue
                    
                # Skip build artifacts and caches
                if item.name in ['__pycache__', '.pytest_cache', 'node_modules']:
                    continue
                    
                if item.is_file():
                    relative_path = item.relative_to(self.root_path)
                    classification, justification = self.classify_file(relative_path)
                    
                    self.classifications[classification].append({
                        "path": str(relative_path),
                        "justification": justification,
                        "size_bytes": item.stat().st_size,
                    })
                    
                elif item.is_dir():
                    self.scan_directory(item)
                    
        except PermissionError:
            pass
            
    def generate_report(self) -> Dict:
        """Generate structured audit report."""
        report = {
            "audit_date": "2026-04-13",
            "repository": "Library-Assessment-Decision-Support-System",
            "summary": {
                "canonical_files": len(self.classifications["canonical"]),
                "legacy_files": len(self.classifications["legacy"]),
                "shared_files": len(self.classifications["shared"]),
                "total_files": sum(len(v) for v in self.classifications.values()),
            },
            "classifications": self.classifications,
            "recommendations": self.generate_recommendations(),
        }
        return report
        
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on audit findings."""
        recommendations = []
        
        legacy_count = len(self.classifications["legacy"])
        if legacy_count > 0:
            recommendations.append(
                f"Archive {legacy_count} legacy files to archive/legacy_sentiment_api/"
            )
            
        shared_count = len(self.classifications["shared"])
        if shared_count > 0:
            recommendations.append(
                f"Review {shared_count} shared files for cleanup or reclassification"
            )
            
        recommendations.append(
            "Update pyproject.toml to reflect Library Assessment identity"
        )
        recommendations.append(
            "Remove FastAPI dependencies from requirements.txt"
        )
        recommendations.append(
            "Modularize streamlit_app.py into ui/ directory"
        )
        
        return recommendations
        
    def save_report(self, output_path: str = "docs/REFACTOR_AUDIT_SUMMARY.md") -> None:
        """Save audit report as Markdown."""
        report = self.generate_report()
        
        md_content = f"""# Repository Audit Summary

**Date:** {report['audit_date']}
**Repository:** {report['repository']}

## Executive Summary

This audit identifies all files in the repository and classifies them as:
- **Canonical**: Part of the Library Assessment Decision Support System (keep)
- **Legacy**: FastAPI/sentiment-analysis artifacts (remove/archive)
- **Shared**: Used by both systems or requires review

## Summary Statistics

- **Total Files Scanned:** {report['summary']['total_files']}
- **Canonical Files:** {report['summary']['canonical_files']}
- **Legacy Files:** {report['summary']['legacy_files']}
- **Shared Files:** {report['summary']['shared_files']}

## Canonical Files (Keep)

These files are part of the Library Assessment Decision Support System and should be preserved.

"""
        
        for item in sorted(report['classifications']['canonical'], key=lambda x: x['path']):
            md_content += f"- `{item['path']}` - {item['justification']}\n"
            
        md_content += "\n## Legacy Files (Remove/Archive)\n\n"
        md_content += "These files are FastAPI/sentiment-analysis artifacts that should be archived.\n\n"
        
        for item in sorted(report['classifications']['legacy'], key=lambda x: x['path']):
            md_content += f"- `{item['path']}` - {item['justification']}\n"
            
        md_content += "\n## Shared Files (Review Required)\n\n"
        md_content += "These files may need updates or reclassification.\n\n"
        
        for item in sorted(report['classifications']['shared'], key=lambda x: x['path']):
            md_content += f"- `{item['path']}` - {item['justification']}\n"
            
        md_content += "\n## Recommendations\n\n"
        
        for i, rec in enumerate(report['recommendations'], 1):
            md_content += f"{i}. {rec}\n"
            
        md_content += "\n## Identity Drift Findings\n\n"
        md_content += "**Current State:**\n"
        md_content += "- pyproject.toml identifies project as 'sentiment-analysis'\n"
        md_content += "- README.md describes Library Assessment Decision Support System\n"
        md_content += "- Mixed dependencies (Streamlit + FastAPI)\n"
        md_content += "- Legacy FastAPI code in src/ directory\n"
        md_content += "- streamlit_app.py is 3042 lines (monolithic)\n\n"
        
        md_content += "**Target State:**\n"
        md_content += "- Single product identity: Library Assessment Decision Support System\n"
        md_content += "- Streamlit-only dependencies\n"
        md_content += "- Modularized UI structure (ui/ directory with 10 modules)\n"
        md_content += "- No FastAPI code\n"
        md_content += "- Aligned metadata and documentation\n\n"
        
        md_content += "## Major Risks\n\n"
        md_content += "1. **Breaking Changes:** Removing legacy code may break canonical features if dependencies exist\n"
        md_content += "2. **Modularization:** Splitting streamlit_app.py requires careful testing to avoid regressions\n"
        md_content += "3. **Dependency Conflicts:** Removing transformers/torch may break modules/sentiment_enhanced.py\n\n"
        
        md_content += "## Mitigation Strategies\n\n"
        md_content += "1. Scan for imports before removing any file\n"
        md_content += "2. Test application after each major change\n"
        md_content += "3. Verify transformers/torch usage before removal\n"
        md_content += "4. Maintain git history for rollback capability\n"
        md_content += "5. Extract UI modules incrementally with testing\n\n"
        
        md_content += "## Final Canonical Project Identity\n\n"
        md_content += "**Name:** Library Assessment Decision Support System\n\n"
        md_content += "**Description:** A local-first, Streamlit-based AI assistant for library assessment that combines quantitative and qualitative analysis with natural language querying. All processing happens locally via Ollama for complete data privacy and FERPA compliance.\n\n"
        md_content += "**Technology Stack:**\n"
        md_content += "- Web Framework: Streamlit\n"
        md_content += "- Local LLM: Ollama with Llama 3.2\n"
        md_content += "- Vector Store: ChromaDB\n"
        md_content += "- Database: SQLite\n"
        md_content += "- NLP: TextBlob, TF-IDF\n"
        md_content += "- Statistics: scipy, statsmodels\n"
        md_content += "- Visualization: Plotly\n\n"
        
        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(md_content)
        
        print(f"Audit report saved to: {output_path}")
        print(f"\nSummary:")
        print(f"  Canonical files: {report['summary']['canonical_files']}")
        print(f"  Legacy files: {report['summary']['legacy_files']}")
        print(f"  Shared files: {report['summary']['shared_files']}")
        print(f"  Total files: {report['summary']['total_files']}")


def main():
    """Run repository audit."""
    print("Starting repository audit...")
    print("=" * 60)
    
    auditor = RepositoryAuditor()
    auditor.scan_directory()
    auditor.save_report()
    
    print("=" * 60)
    print("Audit complete!")
    

if __name__ == "__main__":
    main()

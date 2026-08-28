import os
import shutil
import tempfile
from pathlib import Path
from app.markdown_exporter import export_report_to_markdown


def test_export_report_to_markdown_versioning():
    temp_dir = tempfile.mkdtemp()
    try:
        report_content = "# Banking Strategy Memorandum\n\n- Recommendation: Proceed with M&A."

        # First export -> _v1.md
        res1 = export_report_to_markdown(report_content, base_name="test_report", reports_dir_path=temp_dir)
        assert res1["status"] == "success"
        assert res1["version"] == 1
        assert res1["file_name"] == "test_report_v1.md"
        assert Path(res1["file_path"]).exists()

        # Second export -> _v2.md
        res2 = export_report_to_markdown(report_content, base_name="test_report", reports_dir_path=temp_dir)
        assert res2["status"] == "success"
        assert res2["version"] == 2
        assert res2["file_name"] == "test_report_v2.md"
        assert Path(res2["file_path"]).exists()

        # Check content
        saved_text = Path(res2["file_path"]).read_text(encoding="utf-8")
        assert "Proceed with M&A" in saved_text
    finally:
        shutil.rmtree(temp_dir)

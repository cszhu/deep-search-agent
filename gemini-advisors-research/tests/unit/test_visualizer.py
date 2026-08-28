import os
import shutil
import tempfile
from pathlib import Path
from app.visualizer import render_white_theme_chart, process_report_visual_json


def test_render_white_theme_chart():
    temp_dir = tempfile.mkdtemp()
    try:
        out_path = os.path.join(temp_dir, "test_chart.png")
        data = {
            "title": "Test Capital Benchmarks",
            "subtitle": "White Theme Unit Test",
            "labels": ["CET1", "Total Cap"],
            "target_values": [13.5, 15.0],
            "peer_values": [14.8, 16.4],
            "min_values": [4.5, 8.0]
        }
        res_path = render_white_theme_chart("bar_chart", data, out_path)
        assert os.path.exists(res_path)
        assert os.path.getsize(res_path) > 1000
    finally:
        shutil.rmtree(temp_dir)


def test_process_report_visual_json():
    json_spec = """
    {
        "section1": {
            "chart_type": "capital_benchmarks",
            "data": {
                "title": "Section 1: Statutory Capital Benchmarks",
                "subtitle": "Target vs Peers",
                "labels": ["CET1", "eSLR"],
                "target_values": [13.5, 6.5],
                "peer_values": [14.8, 6.8],
                "min_values": [4.5, 5.0]
            }
        }
    }
    """
    sample_md = "# PART I: STRATEGIC BANKING MEMORANDUM\n\n## 1. Executive Summary\n\nContent here."
    updated_md = process_report_visual_json(json_spec, sample_md)
    assert "assets/section1_infographic.png" in updated_md
    assert Path("reports/assets/section1_infographic.png").exists()

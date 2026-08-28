# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Markdown Export module that saves finalized research reports to /reports with versioning."""

import os
import re
from pathlib import Path
from typing import Optional


def export_report_to_markdown(
    report_markdown: str,
    base_name: str = "gemini_advisors_report",
    reports_dir_path: Optional[str] = None,
) -> dict:
    """Saves the finalized banking strategy report into a formatted Markdown (.md) file in /reports with versioning (e.g. _v1, _v2).

    Args:
        report_markdown: The markdown content of the research report with formatted citations.
        base_name: The base name prefix for the saved file.
        reports_dir_path: Optional path to the reports directory (defaults to "reports").

    Returns:
        A dictionary containing the export status, output file path, version number, and file size.
    """
    reports_dir = Path(reports_dir_path) if reports_dir_path else Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    safe_base = re.sub(r"[^a-zA-Z0-9_\-]+", "_", base_name.lower()).strip("_")
    if not safe_base:
        safe_base = "gemini_advisors_report"

    # Find the next available version number by scanning existing _v*.md files
    version = 1
    existing_versions = []
    pattern = re.compile(rf"^{re.escape(safe_base)}_v(\d+)\.md$")

    for file in reports_dir.glob("*.md"):
        match = pattern.match(file.name)
        if match:
            existing_versions.append(int(match.group(1)))

    if existing_versions:
        version = max(existing_versions) + 1

    filename = f"{safe_base}_v{version}.md"
    target_path = reports_dir / filename

    target_path.write_text(report_markdown, encoding="utf-8")

    return {
        "status": "success",
        "file_path": str(target_path.resolve()),
        "file_name": filename,
        "version": version,
        "file_size_bytes": target_path.stat().st_size,
        "message": f"Successfully exported report to {target_path.resolve()} (version {version}).",
    }

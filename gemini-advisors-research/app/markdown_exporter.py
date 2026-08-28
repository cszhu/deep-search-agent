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

"""Markdown & HTML Export module that saves finalized research reports to /reports with versioning and executive HTML rendering."""

import os
import re
from pathlib import Path
from typing import Optional

try:
    import markdown
except ImportError:
    markdown = None


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gemini Advisors - Executive Banking Strategy Report</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #0f172a;
            --primary-accent: #2563eb;
            --primary-accent-hover: #1d4ed8;
            --bg-canvas: #f8fafc;
            --bg-card: #ffffff;
            --text-main: #1e293b;
            --text-muted: #64748b;
            --border-color: #e2e8f0;
            --table-header-bg: #0f172a;
            --table-header-text: #f8fafc;
            --table-alt-row: #f8fafc;
            --badge-bg: #eff6ff;
            --badge-text: #1d4ed8;
            --badge-border: #bfdbfe;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-canvas);
            color: var(--text-main);
            line-height: 1.7;
            padding: 40px 20px;
            -webkit-font-smoothing: antialiased;
        }

        .report-container {
            max-width: 960px;
            margin: 0 auto;
            background: var(--bg-card);
            padding: 60px 80px;
            border-radius: 16px;
            box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.04);
            border: 1px solid var(--border-color);
        }

        .executive-header {
            border-bottom: 3px solid var(--primary-accent);
            padding-bottom: 24px;
            margin-bottom: 36px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }

        .brand-title {
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: var(--primary-accent);
            margin-bottom: 6px;
        }

        .doc-title {
            font-size: 28px;
            font-weight: 800;
            color: var(--primary);
            letter-spacing: -0.5px;
        }

        h1 {
            font-size: 24px;
            font-weight: 800;
            color: var(--primary);
            margin-top: 40px;
            margin-bottom: 20px;
            padding-bottom: 8px;
            border-bottom: 2px solid #cbd5e1;
            letter-spacing: -0.3px;
        }

        h2 {
            font-size: 20px;
            font-weight: 700;
            color: var(--primary);
            margin-top: 32px;
            margin-bottom: 16px;
            letter-spacing: -0.2px;
        }

        h3 {
            font-size: 16px;
            font-weight: 600;
            color: #334155;
            margin-top: 24px;
            margin-bottom: 12px;
        }

        p {
            margin-bottom: 18px;
            font-size: 15px;
            color: #334155;
        }

        strong {
            color: #0f172a;
            font-weight: 600;
        }

        .podcast-player-card {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #ffffff;
            padding: 24px 28px;
            border-radius: 16px;
            margin: 28px 0 36px 0;
            box-shadow: 0 10px 25px rgba(15, 23, 42, 0.2);
            border: 1px solid #334155;
        }

        .podcast-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        }

        .podcast-badge {
            background: #2563eb;
            color: #ffffff;
            font-size: 11px;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 20px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            box-shadow: 0 2px 8px rgba(37, 99, 235, 0.4);
        }

        .podcast-title {
            color: #f8fafc !important;
            font-size: 18px !important;
            font-weight: 700 !important;
            margin: 8px 0 6px 0 !important;
        }

        .podcast-desc {
            color: #cbd5e1 !important;
            font-size: 13.5px !important;
            margin-bottom: 14px !important;
            line-height: 1.5 !important;
        }

        ul, ol {
            margin-bottom: 20px;
            padding-left: 28px;
            color: #334155;
        }

        li {
            margin-bottom: 8px;
            font-size: 15px;
        }

        hr {
            border: none;
            border-top: 1px solid var(--border-color);
            margin: 36px 0;
        }

        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin: 28px 0;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border-color);
            font-size: 14px;
            box-shadow: 0 4px 15px rgba(15, 23, 42, 0.05);
        }

        th {
            background-color: var(--table-header-bg);
            color: var(--table-header-text);
            font-weight: 700;
            text-align: left;
            padding: 14px 18px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            font-size: 12px;
        }

        td {
            padding: 14px 18px;
            border-bottom: 1px solid var(--border-color);
            color: #334155;
            line-height: 1.6;
        }

        tr:nth-child(even) td {
            background-color: var(--table-alt-row);
        }

        tr:last-child td {
            border-bottom: none;
        }

        tr:hover td {
            background-color: #f1f5f9;
        }

        code {
            font-family: 'JetBrains Mono', monospace;
            background-color: #f1f5f9;
            color: #0f172a;
            padding: 3px 6px;
            border-radius: 4px;
            font-size: 13px;
        }

        pre {
            background-color: #0f172a;
            color: #f8fafc;
            padding: 22px 24px;
            border-radius: 12px;
            overflow-x: auto;
            margin: 28px 0;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12.5px;
            line-height: 1.5;
            border-left: 4px solid var(--primary-accent);
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.12);
        }

        pre code {
            background: none;
            color: inherit;
            padding: 0;
        }

        a {
            color: var(--primary-accent);
            text-decoration: none;
            font-weight: 500;
            padding: 2px 6px;
            background-color: var(--badge-bg);
            border: 1px solid var(--badge-border);
            border-radius: 4px;
            font-size: 13px;
            transition: all 0.15s ease-in-out;
            display: inline-block;
            margin: 0 1px;
        }

        a:hover {
            background-color: var(--primary-accent);
            color: #ffffff;
            border-color: var(--primary-accent);
        }

        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 32px auto;
            border-radius: 14px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
            border: 1px solid var(--border-color);
            background-color: #ffffff;
            padding: 12px;
        }

        blockquote {
            border-left: 4px solid var(--primary-accent);
            padding: 14px 22px;
            background-color: #eff6ff;
            color: #1e3a8a;
            margin: 24px 0;
            border-radius: 0 10px 10px 0;
            font-style: italic;
        }

        .svc-badge {
            display: inline-block;
            background: #2563eb;
            color: #ffffff;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 6px;
            margin-right: 6px;
            letter-spacing: 0.5px;
        }

        @media print {
            body {
                background: #ffffff;
                padding: 0;
            }
            .report-container {
                box-shadow: none;
                border: none;
                padding: 0;
                max-width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="report-container">
        <div class="executive-header">
            <div>
                <div class="brand-title">Gemini Advisors • Banking Strategy Practice</div>
                <div class="doc-title">Executive Strategic Research Report</div>
            </div>
        </div>
        <!-- CONTENT_PLACEHOLDER -->
    </div>
</body>
</html>
"""


def render_markdown_to_html(markdown_text: str) -> str:
    """Converts raw markdown text to executive HTML using the markdown library."""
    # Pre-process text: clean math/percentage escapes ($13.50\\%$ -> 13.50%)
    cleaned_md = re.sub(r"\\+", "", markdown_text)
    cleaned_md = re.sub(r"\$([0-9\.\%]+)\$", r"\1", cleaned_md)
    # Format Service IDs with styled badges
    cleaned_md = re.sub(r"\[(SVC-[A-Z0-9\-]+)\]", r'<span class="svc-badge">\1</span>', cleaned_md)

    if markdown:
        html_body = markdown.markdown(
            cleaned_md,
            extensions=["tables", "fenced_code", "toc", "nl2br"],
        )
    else:
        # Fallback simple line renderer if markdown module is absent
        html_body = f"<pre>{cleaned_md}</pre>"

    return HTML_TEMPLATE.replace("<!-- CONTENT_PLACEHOLDER -->", html_body)


def export_report_to_markdown(
    report_markdown: str,
    base_name: str = "gemini_advisors_report",
    reports_dir_path: Optional[str] = None,
) -> dict:
    """Saves the finalized banking strategy report into formatted Markdown (.md) AND styled HTML (.html) files in /reports with versioning.

    Args:
        report_markdown: The markdown content of the research report with formatted citations.
        base_name: The base name prefix for the saved file.
        reports_dir_path: Optional path to the reports directory (defaults to "reports").

    Returns:
        A dictionary containing export status, output file paths, version number, and file sizes.
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

    md_filename = f"{safe_base}_v{version}.md"
    html_filename = f"{safe_base}_v{version}.html"

    target_md_path = reports_dir / md_filename
    target_html_path = reports_dir / html_filename

    # Save Markdown file
    target_md_path.write_text(report_markdown, encoding="utf-8")

    # Render & Save HTML file
    rendered_html = render_markdown_to_html(report_markdown)
    target_html_path.write_text(rendered_html, encoding="utf-8")

    return {
        "status": "success",
        "file_path": str(target_md_path.resolve()),
        "html_file_path": str(target_html_path.resolve()),
        "file_name": md_filename,
        "html_file_name": html_filename,
        "version": version,
        "file_size_bytes": target_md_path.stat().st_size,
        "html_size_bytes": target_html_path.stat().st_size,
        "message": f"Successfully exported Markdown ({target_md_path.resolve()}) and HTML ({target_html_path.resolve()}) version {version}.",
    }


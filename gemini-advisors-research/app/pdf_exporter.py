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

"""PDF Export tool that converts markdown reports to PDF with clickable inline citations."""

import datetime
import html
import os
import re
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _convert_markdown_to_reportlab_html(text: str) -> str:
    """Converts inline markdown formatting and links to ReportLab compatible XML/HTML tags."""
    # Convert markdown links [Text](URL) to <a href="URL"><font color="#1a56db"><u>Text</u></font></a>
    def link_replacer(match: re.Match) -> str:
        label = html.escape(match.group(1))
        url = html.escape(match.group(2))
        return f'<a href="{url}"><font color="#1a56db"><u>{label}</u></font></a>'

    # Handle links first
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link_replacer, text)

    # Convert bold **text** or __text__ to <b>text</b>
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__([^_]+)__", r"<b>\1</b>", text)

    # Convert italic *text* or _text_ to <i>text</i>
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    text = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"<i>\1</i>", text)

    # Convert code `code` to <font name="Courier">\1</font>
    text = re.sub(r"`([^`]+)`", r'<font name="Courier" color="#374151">\1</font>', text)

    return text


def export_report_to_pdf(
    report_markdown: str,
    title: str = "Gemini Advisors Banking Strategy Report",
    filename: Optional[str] = None,
) -> dict:
    """Renders the finalized banking strategy report into a formatted PDF document, preserving all inline clickable citations.

    Args:
        report_markdown: The markdown content of the research report, including inline citations.
        title: The title of the report document.
        filename: Optional custom filename for the PDF output.

    Returns:
        A dictionary containing the export status, output file path, and page count information.
    """
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    if not filename:
        safe_title = re.sub(r"[^a-zA-Z0-9_\-]+", "_", title.lower())[:40]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gemini_advisors_{safe_title}_{timestamp}.pdf"

    if not filename.endswith(".pdf"):
        filename += ".pdf"

    pdf_path = reports_dir / filename

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=14,
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#334155"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=8,
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        leftIndent=15,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=4,
    )

    story = []

    # Header banner
    story.append(Paragraph("<b>GEMINI ADVISORS</b> | Strategic Investment Banking Intelligence", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f172a"), spaceAfter=10))
    story.append(Paragraph(html.escape(title), title_style))
    story.append(Paragraph(f"Jurisdictional Coverage: US • EU • China | Generated: {datetime.datetime.now().strftime('%B %d, %Y')}", subtitle_style))
    story.append(Spacer(1, 10))

    # Parse markdown lines into PDF elements
    lines = report_markdown.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 4))
            continue

        if stripped.startswith("# "):
            heading_text = stripped[2:].strip()
            formatted_text = _convert_markdown_to_reportlab_html(heading_text)
            story.append(Paragraph(formatted_text, h1_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6))
        elif stripped.startswith("## "):
            heading_text = stripped[3:].strip()
            formatted_text = _convert_markdown_to_reportlab_html(heading_text)
            story.append(Paragraph(formatted_text, h1_style))
        elif stripped.startswith("### "):
            heading_text = stripped[4:].strip()
            formatted_text = _convert_markdown_to_reportlab_html(heading_text)
            story.append(Paragraph(formatted_text, h2_style))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            bullet_text = stripped[2:].strip()
            formatted_text = _convert_markdown_to_reportlab_html(bullet_text)
            story.append(Paragraph(f"• {formatted_text}", bullet_style))
        elif re.match(r"^\d+\.\s+", stripped):
            num_match = re.match(r"^(\d+\.)\s+(.*)", stripped)
            if num_match:
                prefix = num_match.group(1)
                item_text = num_match.group(2)
                formatted_text = _convert_markdown_to_reportlab_html(item_text)
                story.append(Paragraph(f"<b>{prefix}</b> {formatted_text}", bullet_style))
        else:
            formatted_text = _convert_markdown_to_reportlab_html(stripped)
            story.append(Paragraph(formatted_text, body_style))

    doc.build(story)

    return {
        "status": "success",
        "file_path": str(pdf_path.resolve()),
        "file_name": filename,
        "file_size_bytes": os.path.getsize(str(pdf_path)),
        "message": f"Successfully exported report to {pdf_path.resolve()} with preserved clickable citations.",
    }

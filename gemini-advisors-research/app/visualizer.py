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

"""Visualizer module for generating clean, white-themed visual charts and infographics from JSON specifications."""

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np


def render_white_theme_chart(chart_type: str, data: Dict[str, Any], output_path: str) -> str:
    """Renders a high-resolution visual asset on a clean white theme (#ffffff) and saves as PNG.

    Args:
        chart_type: Type of graphic ('bar_chart', 'donut_chart', 'comparison_matrix', 'flow_diagram').
        data: Dictionary containing chart title, labels, values, series, or items.
        output_path: Destination file path for saving the PNG file.

    Returns:
        The output file path string.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    title = data.get("title", "Executive Banking Strategy Visual Benchmark")
    subtitle = data.get("subtitle", "Gemini Advisors FIG Practice")

    if chart_type in ["bar_chart", "capital_benchmarks"]:
        labels = data.get("labels", ["CET1 Ratio", "Total Capital", "eSLR Ratio", "LCR Ratio"])
        target_vals = data.get("target_values", [13.5, 15.0, 6.5, 125.0])
        peer_vals = data.get("peer_values", [14.8, 16.4, 6.8, 140.0])
        min_vals = data.get("min_values", [4.5, 8.0, 5.0, 100.0])

        x = np.arange(len(labels))
        width = 0.25

        ax.bar(x - width, min_vals, width, label="Regulatory Min", color="#94a3b8")
        ax.bar(x, target_vals, width, label="Project Target", color="#2563eb")
        ax.bar(x + width, peer_vals, width, label="Tier-1 Peer Avg", color="#0f172a")

        ax.set_ylabel("Percentage (%)", fontsize=10, fontweight="bold", color="#0f172a")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=9, fontweight="bold", color="#0f172a")
        ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=9)
        ax.grid(axis="y", linestyle="--", alpha=0.3, color="#cbd5e1")

    elif chart_type in ["donut_chart", "revenue_mix"]:
        labels = data.get("labels", ["Underwriting & M&A", "Depository Sweeps", "TXSE Execution", "Wealth Mgmt"])
        sizes = data.get("values", [35, 25, 25, 15])
        colors = ["#2563eb", "#0f172a", "#3b82f6", "#64748b"]

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=colors,
            wedgeprops=dict(width=0.4, edgecolor="#ffffff", linewidth=2),
            textprops=dict(color="#0f172a", fontweight="bold", fontsize=9),
        )
        for autotext in autotexts:
            autotext.set_color("#ffffff")
            autotext.set_fontweight("bold")

    elif chart_type in ["comparison_matrix", "regulatory_flow"]:
        ax.axis("off")
        regions = data.get("regions", ["United States (OCC/Fed)", "European Union (ECB)", "PRC (PBOC/NFRA)"])
        standards = data.get("standards", [
            "Basel III Endgame & ERBA\nFDIC Depository / FINRA BD",
            "CRD VI & CRR3 Output Floor\nDORA Operational Resilience",
            "Rules on Capital Mgmt\nPIPL Data Local Vault"
        ])

        y_positions = [0.75, 0.45, 0.15]
        for idx, (reg, std) in enumerate(zip(regions, standards)):
            y = y_positions[idx]
            ax.text(0.05, y, reg, fontsize=11, fontweight="bold", color="#0f172a",
                    bbox=dict(boxstyle="round,pad=0.5", facecolor="#eff6ff", edgecolor="#bfdbfe", linewidth=1.5))
            ax.annotate("", xy=(0.45, y), xytext=(0.35, y),
                        arrowprops=dict(arrowstyle="->", lw=2, color="#2563eb"))
            ax.text(0.47, y, std, fontsize=9, color="#334155", va="center",
                    bbox=dict(boxstyle="round,pad=0.5", facecolor="#ffffff", edgecolor="#cbd5e1", linewidth=1.0))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 0.9)

    else:
        # Default metric visual summary card
        ax.axis("off")
        metrics = data.get("metrics", {"Target ROTCE": ">= 16.5%", "Efficiency Ratio": "<= 52.0%", "CET1 Floor": ">= 12.5%"})
        for i, (k, v) in enumerate(metrics.items()):
            x_pos = 0.15 + (i * 0.28)
            ax.text(x_pos, 0.55, v, fontsize=16, fontweight="bold", color="#2563eb", ha="center")
            ax.text(x_pos, 0.35, k, fontsize=9, color="#64748b", ha="center", fontweight="bold")
            ax.add_patch(plt.Rectangle((x_pos - 0.12, 0.25), 0.24, 0.45, fill=False, edgecolor="#cbd5e1", lw=1.2, rx=0.02))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

    # Title & Subtitle styling for white theme
    fig.suptitle(title, fontsize=12, fontweight="bold", color="#0f172a", x=0.5, y=0.96)
    ax.set_title(subtitle, fontsize=9, color="#64748b", pad=10)

    # Clean up borders for chart axes
    if chart_type not in ["comparison_matrix", "regulatory_flow", "metrics"]:
        for spine in ax.spines.values():
            spine.set_color("#cbd5e1")

    plt.tight_layout()
    plt.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor="none", bbox_inches="tight")
    plt.close(fig)

    return output_path


def process_report_visual_json(json_spec_str: str, report_markdown: str) -> str:
    """Parses JSON visual specification from report_visualizer_agent and injects generated white-theme images into Markdown.

    Args:
        json_spec_str: Structured JSON string specifying infographics for sections.
        report_markdown: The markdown content of the research report.

    Returns:
        Updated markdown content containing embedded image tags for generated visual assets.
    """
    assets_dir = Path("reports/assets")
    assets_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Strip potential ```json markdown blocks from model output
        clean_json = re.sub(r"^```json\s*", "", json_spec_str.strip(), flags=re.MULTILINE)
        clean_json = re.sub(r"```$", "", clean_json.strip(), flags=re.MULTILINE)
        spec_data = json.loads(clean_json)
    except Exception as e:
        logging.warning(f"Failed to parse visual JSON spec: {e}. Falling back to default visual specs.")
        spec_data = {
            "section1": {
                "chart_type": "capital_benchmarks",
                "data": {
                    "title": "Section 1: Statutory Capital & Liquidity Benchmarks",
                    "subtitle": "Project LoneStar Target vs Peer Average & Regulatory Minimums",
                    "labels": ["CET1 Ratio", "Total Capital", "eSLR", "LCR"],
                    "target_values": [13.5, 15.0, 6.5, 125.0],
                    "peer_values": [14.8, 16.4, 6.8, 140.0],
                    "min_values": [4.5, 8.0, 5.0, 100.0]
                }
            },
            "section2": {
                "chart_type": "regulatory_flow",
                "data": {
                    "title": "Section 2: Tri-Jurisdictional Regulatory Architecture",
                    "subtitle": "Reconciled Legal & Data Sovereignty Blueprint",
                    "regions": ["United States (OCC/Fed)", "European Union (ECB)", "PRC (PBOC/NFRA)"],
                    "standards": [
                        "Basel III Endgame & ERBA\nFDIC Depository / FINRA BD",
                        "CRD VI & CRR3 Output Floor\nDORA Operational Resilience",
                        "Rules on Capital Mgmt\nPIPL Data Local Vault"
                    ]
                }
            },
            "section3": {
                "chart_type": "revenue_mix",
                "data": {
                    "title": "Section 3: Pro-Forma Revenue Mix",
                    "subtitle": "5-Year Revenue Stream Distribution",
                    "labels": ["Underwriting & M&A", "Depository Sweeps", "TXSE Execution", "Wealth Mgmt"],
                    "values": [35, 25, 25, 15]
                }
            }
        }

    updated_md = report_markdown

    # Render each section's graphic and insert into Markdown
    for sec_id, item in spec_data.items():
        chart_type = item.get("chart_type", "bar_chart")
        chart_data = item.get("data", {})
        file_name = f"{sec_id}_infographic.png"
        img_path = assets_dir / file_name

        try:
            render_white_theme_chart(chart_type, chart_data, str(img_path))
            rel_path = f"assets/{file_name}"
            img_tag = f"\n\n![{chart_data.get('title', 'Section Infographic')}]({rel_path})\n\n"

            # Insert graphic near section header if available
            sec_header_match = re.search(rf"(##\s+\d+\..*)", updated_md)
            if sec_header_match:
                header_pos = sec_header_match.end()
                updated_md = updated_md[:header_pos] + img_tag + updated_md[header_pos:]
            else:
                updated_md += img_tag
        except Exception as err:
            logging.warning(f"Failed to render graphic for section {sec_id}: {err}")

    return updated_md

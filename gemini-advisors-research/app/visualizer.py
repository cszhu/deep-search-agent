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
        target_vals = data.get("target_values", [13.5, 15.0, 6.5, 125.0])
        peer_vals = data.get("peer_values", [14.8, 16.4, 6.8, 140.0])
        min_vals = data.get("min_values", [4.5, 8.0, 5.0, 100.0])

        provided_labels = data.get("labels")
        if provided_labels and len(provided_labels) == len(target_vals):
            labels = provided_labels
        else:
            default_labels = ["CET1 Ratio", "Total Capital", "eSLR Ratio", "LCR Ratio", "NSFR Ratio", "Tier-1 Cap"]
            labels = default_labels[:len(target_vals)] if len(target_vals) <= len(default_labels) else [f"Metric {i+1}" for i in range(len(target_vals))]

        x = np.arange(len(labels))
        width = 0.25

        ax.bar(x - width, min_vals[:len(labels)], width, label="Regulatory Min", color="#94a3b8")
        ax.bar(x, target_vals[:len(labels)], width, label="Project Target", color="#2563eb")
        ax.bar(x + width, peer_vals[:len(labels)], width, label="Tier-1 Peer Avg", color="#0f172a")

        ax.set_ylabel("Percentage (%)", fontsize=10, fontweight="bold", color="#0f172a")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=9, fontweight="bold", color="#0f172a")
        ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=9)
        ax.grid(axis="y", linestyle="--", alpha=0.3, color="#cbd5e1")

    elif chart_type in ["donut_chart", "revenue_mix"]:
        sizes = data.get("values", [35, 25, 25, 15])
        provided_labels = data.get("labels")
        if provided_labels and len(provided_labels) == len(sizes):
            labels = provided_labels
        else:
            default_labels = ["Underwriting & M&A", "Depository Sweeps", "TXSE Execution", "Wealth Mgmt", "Advisory Services", "Trading Operations"]
            labels = default_labels[:len(sizes)] if len(sizes) <= len(default_labels) else [f"Stream {i+1}" for i in range(len(sizes))]

        palette = ["#2563eb", "#0f172a", "#3b82f6", "#64748b", "#0284c7", "#475569"]
        colors = palette[:len(sizes)] if len(sizes) <= len(palette) else palette * (len(sizes) // len(palette) + 1)

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=colors[:len(sizes)],
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

    elif chart_type in ["balance_sheet_trajectory", "financial_trajectory"]:
        years = data.get("years", ["Year 1", "Year 2", "Year 3", "Year 4", "Year 5"])
        assets = data.get("assets", [4.8, 8.2, 12.5, 17.0, 22.5])
        rotce = data.get("rotce", [12.0, 14.8, 17.4, 19.5, 22.6])

        x = np.arange(len(years))
        width = 0.35

        rects = ax.bar(x, assets, width, label="Total Assets ($B)", color="#2563eb", alpha=0.9)
        ax.set_ylabel("Total Assets ($ Billions)", fontsize=10, fontweight="bold", color="#2563eb")
        ax.set_xticks(x)
        ax.set_xticklabels(years, fontsize=9, fontweight="bold", color="#0f172a")

        ax2 = ax.twinx()
        ax2.plot(x, rotce, color="#0f172a", marker="o", linewidth=2.5, label="ROTCE (%)")
        ax2.set_ylabel("ROTCE (%)", fontsize=10, fontweight="bold", color="#0f172a")
        ax2.set_ylim(0, 30)

        for rect in rects:
            height = rect.get_height()
            ax.annotate(f"${height:.1f}B",
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=8, fontweight='bold', color="#1e40af")

        for i, txt in enumerate(rotce):
            ax2.annotate(f"{txt:.1f}%", (x[i], rotce[i]), xytext=(0, 6), textcoords="offset points",
                         ha='center', fontsize=8, fontweight='bold', color="#0f172a")

        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left", frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=8)
        ax.grid(axis="y", linestyle="--", alpha=0.3, color="#cbd5e1")

    elif chart_type in ["capital_buffer_stack", "buffer_stack"]:
        categories = ["Baseline Min (4.50%)", "CCB (2.50%)", "SCB (3.20%)", "Mgmt Cushion (3.30%)"]
        values = data.get("values", [4.50, 2.50, 3.20, 3.30])
        colors = ["#94a3b8", "#3b82f6", "#1d4ed8", "#0f172a"]

        y_pos = [0]
        left = 0
        for cat, val, col in zip(categories, values, colors):
            ax.barh(y_pos, [val], left=left, color=col, height=0.45, label=f"{cat}")
            if val >= 2.0:
                ax.text(left + val / 2, 0, f"{val:.2f}%", ha="center", va="center", color="#ffffff", fontweight="bold", fontsize=9)
            left += val

        ax.set_yticks([])
        ax.set_xlabel("Common Equity Tier 1 (CET1) Ratio (%) — Target: 13.50%", fontsize=10, fontweight="bold", color="#0f172a")
        ax.set_xlim(0, 16)
        ax.axvline(13.5, color="#dc2626", linestyle="--", linewidth=1.5, label="Target CET1 (13.50%)")
        ax.legend(loc="upper right", frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=8)
        ax.grid(axis="x", linestyle="--", alpha=0.3, color="#cbd5e1")

    elif chart_type in ["compliance_roadmap", "roadmap_timeline"]:
        ax.axis("off")
        stages = data.get("stages", [
            "Phase 1: OCC & SEC Filings\n(Q1-Q2 2027)",
            "Phase 2: Capital Inflow & BD\n(Q3 2027)",
            "Phase 3: ECB/DORA Passport\n(Q4 2027)",
            "Phase 4: CSRC QFI & PBOC\n(Q1 2028)"
        ])
        colors = ["#2563eb", "#3b82f6", "#0284c7", "#0f172a"]

        for i, (stage, col) in enumerate(zip(stages, colors)):
            x_pos = 0.12 + (i * 0.24)
            ax.text(x_pos, 0.5, stage, fontsize=8, fontweight="bold", color="#ffffff", ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.6", facecolor=col, edgecolor="#cbd5e1", linewidth=1.0))
            if i < len(stages) - 1:
                ax.annotate("", xy=(x_pos + 0.11, 0.5), xytext=(x_pos + 0.08, 0.5),
                            arrowprops=dict(arrowstyle="->", lw=2, color="#2563eb"))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

    elif chart_type in ["service_catalog_grid", "service_offerings"]:
        ax.axis("off")
        services = data.get("services", [
            {"id": "SVC-US-SEC-01", "name": "US Regulatory Clearance", "jur": "US (SEC/Fed)", "color": "#2563eb"},
            {"id": "SVC-EU-DORA-02", "name": "EU DORA Audit", "jur": "EU (ECB/ESMA)", "color": "#0f172a"},
            {"id": "SVC-CN-NFRA-03", "name": "China Market Access", "jur": "PRC (PBOC/SAFE)", "color": "#0284c7"}
        ])

        for i, s in enumerate(services):
            x_pos = 0.16 + (i * 0.33)
            ax.text(x_pos, 0.65, s["id"], fontsize=11, fontweight="bold", color=s["color"], ha="center")
            ax.text(x_pos, 0.48, s["name"], fontsize=9, fontweight="bold", color="#0f172a", ha="center")
            ax.text(x_pos, 0.32, s["jur"], fontsize=8, color="#64748b", ha="center",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="#eff6ff", edgecolor="#bfdbfe", linewidth=0.8))
            from matplotlib.patches import FancyBboxPatch
            ax.add_patch(FancyBboxPatch((x_pos - 0.14, 0.20), 0.28, 0.58, boxstyle="round,pad=0.02,rounding_size=0.03", fill=False, edgecolor="#cbd5e1", lw=1.2))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

    else:
        # Default metric visual summary card
        ax.axis("off")
        metrics = data.get("metrics", {"Target ROTCE": ">= 16.5%", "Efficiency Ratio": "<= 52.0%", "CET1 Floor": ">= 12.5%"})
        for i, (k, v) in enumerate(metrics.items()):
            x_pos = 0.15 + (i * 0.28)
            ax.text(x_pos, 0.55, v, fontsize=16, fontweight="bold", color="#2563eb", ha="center")
            ax.text(x_pos, 0.35, k, fontsize=9, color="#64748b", ha="center", fontweight="bold")
            from matplotlib.patches import FancyBboxPatch
            ax.add_patch(FancyBboxPatch((x_pos - 0.12, 0.25), 0.24, 0.45, boxstyle="round,pad=0.02,rounding_size=0.03", fill=False, edgecolor="#cbd5e1", lw=1.2))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

    # Title & Subtitle styling for white theme
    fig.suptitle(title, fontsize=12, fontweight="bold", color="#0f172a", x=0.5, y=0.96)
    ax.set_title(subtitle, fontsize=9, color="#64748b", pad=10)

    # Clean up borders for chart axes
    if chart_type not in ["comparison_matrix", "regulatory_flow", "compliance_roadmap", "roadmap_timeline", "service_catalog_grid", "service_offerings", "metrics"]:
        for spine in ax.spines.values():
            spine.set_color("#cbd5e1")

    plt.tight_layout()
    plt.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor="none", bbox_inches="tight")
    plt.close(fig)

    return output_path


def _normalize_spec_data(spec_data: Any) -> Dict[str, Dict[str, Any]]:
    """Normalizes any JSON structure (dict, list, nested keys) into a standardized dict mapping section_ids to chart dicts."""
    normalized: Dict[str, Dict[str, Any]] = {}

    if isinstance(spec_data, list):
        items = spec_data
    elif isinstance(spec_data, dict):
        for wrapper_key in ["sections", "charts", "visuals", "items", "infographics"]:
            if wrapper_key in spec_data and isinstance(spec_data[wrapper_key], list):
                items = spec_data[wrapper_key]
                break
        else:
            for k, v in spec_data.items():
                if isinstance(v, dict):
                    normalized[str(k)] = v
                elif isinstance(v, list):
                    for idx, sub_v in enumerate(v):
                        if isinstance(sub_v, dict):
                            normalized[f"{k}_{idx+1}"] = sub_v
            return normalized
    else:
        return {}

    for idx, item in enumerate(items):
        if isinstance(item, dict):
            sec_id = item.get("section_id") or item.get("section") or f"section{idx+1}"
            normalized[str(sec_id)] = item

    return normalized


def process_report_visual_json(json_spec_str: str, report_markdown: str) -> str:
    """Parses JSON visual specification from report_visualizer_agent and injects generated white-theme images into Markdown."""
    assets_dir = Path("reports/assets")
    assets_dir.mkdir(parents=True, exist_ok=True)

    try:
        clean_json = re.sub(r"^```json\s*", "", json_spec_str.strip(), flags=re.MULTILINE)
        clean_json = re.sub(r"```$", "", clean_json.strip(), flags=re.MULTILINE)
        raw_data = json.loads(clean_json)
        spec_data = _normalize_spec_data(raw_data)
    except Exception as e:
        logging.warning(f"Failed to parse visual JSON spec: {e}. Falling back to default visual specs.")
        spec_data = {}

    if not spec_data:
        spec_data = {
            "section1": {
                "chart_type": "capital_benchmarks",
                "data": {
                    "title": "Section 1: Statutory Capital & Liquidity Benchmarks",
                    "subtitle": "Project LoneStar Target vs Peer Average & Regulatory Minimums",
                    "labels": ["CET1 Ratio", "Total Capital", "eSLR", "LCR", "NSFR"],
                    "target_values": [13.5, 15.0, 6.5, 138.5, 122.4],
                    "peer_values": [14.8, 16.4, 6.8, 140.0, 116.2],
                    "min_values": [4.5, 8.0, 5.0, 100.0, 100.0]
                }
            },
            "section1_trajectory": {
                "chart_type": "financial_trajectory",
                "data": {
                    "title": "Section 1.2: Pro-Forma Asset Expansion & ROTCE Trajectory",
                    "subtitle": "5-Year Balance Sheet Growth ($4.8B -> $22.5B) & ROTCE Expansion (22.6%)",
                    "years": ["Yr 1", "Yr 2", "Yr 3", "Yr 4", "Yr 5"],
                    "assets": [4.80, 8.20, 12.50, 17.00, 22.50],
                    "rotce": [12.0, 14.8, 17.4, 19.5, 22.6]
                }
            },
            "section2": {
                "chart_type": "regulatory_flow",
                "data": {
                    "title": "Section 2: Tri-Jurisdictional Regulatory Architecture",
                    "subtitle": "Reconciled Legal & Data Sovereignty Blueprint across US, EU, and China",
                    "regions": ["United States (OCC/Fed/SEC)", "European Union (ECB/DORA)", "PRC (PBOC/NFRA/SAFE)"],
                    "standards": [
                        "Basel III Endgame & ERBA\nFDIC Depository / FINRA BD Member",
                        "CRD VI & CRR3 Output Floor\nDORA Operational Resilience RTS",
                        "Rules on Capital Management\nPIPL Local Data Vault & Quotas"
                    ]
                }
            },
            "section2_roadmap": {
                "chart_type": "roadmap_timeline",
                "data": {
                    "title": "Section 2.3: Regulatory Compliance & Licensing Milestones",
                    "subtitle": "Phase-Gated Multi-Jurisdiction Execution Roadmap",
                    "stages": [
                        "Phase 1: OCC & SEC Filings\n(Q1-Q2 2027)",
                        "Phase 2: Capital Inflow & BD Setup\n(Q3 2027)",
                        "Phase 3: ECB/DORA & EU Passport\n(Q4 2027)",
                        "Phase 4: CSRC QFI & PBOC Gateway\n(Q1 2028)"
                    ]
                }
            },
            "section3": {
                "chart_type": "revenue_mix",
                "data": {
                    "title": "Section 3: Pro-Forma 5-Year Revenue Mix",
                    "subtitle": "5-Year Revenue Stream Distribution ($585.0M Total)",
                    "labels": ["Underwriting & M&A (35%)", "Depository Sweeps (25%)", "TXSE Execution (25%)", "Wealth Mgmt (15%)"],
                    "values": [35, 25, 25, 15]
                }
            },
            "section3_buffers": {
                "chart_type": "buffer_stack",
                "data": {
                    "title": "Section 3.2: Prudential Capital Buffer Stack",
                    "subtitle": "Target CET1 Stack (13.50%) decomposed by Regulatory & Volatility Buffers",
                    "values": [4.50, 2.50, 3.20, 3.30]
                }
            },
            "service_catalog": {
                "chart_type": "service_catalog_grid",
                "data": {
                    "title": "Part II: Gemini Advisors Institutional Advisory Service Offerings",
                    "subtitle": "Standardized Advisory Packages for Institutional Clients",
                    "services": [
                        {"id": "SVC-US-SEC-01", "name": "Cross-Border Regulatory Advisory", "jur": "US (SEC/Fed)", "color": "#2563eb"},
                        {"id": "SVC-EU-DORA-02", "name": "EU DORA ICT Operational Audit", "jur": "EU (ECB/ESMA)", "color": "#0f172a"},
                        {"id": "SVC-CN-NFRA-03", "name": "China Market Access & Quotas", "jur": "PRC (PBOC/SAFE)", "color": "#0284c7"}
                    ]
                }
            }
        }

    # Strip any existing infographic image tags to prevent duplication on re-exports/retries
    updated_md = re.sub(r"\n*!\[[^\]]*\]\(assets/[^)]+_infographic\.png\)\n*", "\n\n", report_markdown)

    # Render each section's graphic and insert into Markdown
    for idx, (sec_id, item) in enumerate(spec_data.items()):
        if not isinstance(item, dict):
            continue
        chart_type = item.get("chart_type", "bar_chart")
        chart_data = item.get("data", {})
        if not isinstance(chart_data, dict):
            chart_data = {}

        file_name = f"{sec_id}_infographic.png"
        img_path = assets_dir / file_name

        # Skip if this image asset is already placed in updated_md
        rel_path = f"assets/{file_name}"
        if rel_path in updated_md:
            continue

        try:
            render_white_theme_chart(chart_type, chart_data, str(img_path))
            rel_path = f"assets/{file_name}"
            img_tag = f"\n\n![{chart_data.get('title', 'Section Infographic')}]({rel_path})\n\n"

            # Match section number or n-th ## / ### header
            sec_num_match = re.search(r"\d+", sec_id)
            sec_num = sec_num_match.group(0) if sec_num_match else str(idx + 1)

            header_pattern = rf"(#+\s*(?:Section\s*)?{sec_num}[\.\s:][^\n]*)"
            header_match = re.search(header_pattern, updated_md, re.IGNORECASE)

            if header_match:
                header_pos = header_match.end()
                updated_md = updated_md[:header_pos] + img_tag + updated_md[header_pos:]
            else:
                # Find all H2/H3 headers and insert after the idx-th header
                all_headers = list(re.finditer(r"(^#+\s+[^\n]+)", updated_md, re.MULTILINE))
                if idx < len(all_headers):
                    header_pos = all_headers[idx].end()
                    updated_md = updated_md[:header_pos] + img_tag + updated_md[header_pos:]
                else:
                    updated_md += img_tag
        except Exception as err:
            logging.warning(f"Failed to render graphic for section {sec_id}: {err}")

    return updated_md

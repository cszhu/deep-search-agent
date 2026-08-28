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

import datetime
import logging
import os
import re
from collections.abc import AsyncGenerator
from typing import Literal, Optional

from google.adk.agents import BaseAgent, LlmAgent, LoopAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.apps.app import App, ResumabilityConfig
from google.adk.events import Event, EventActions
from google.adk.planners import BuiltInPlanner
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)
from google.adk.tools import LongRunningFunctionTool, google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.tool_context import ToolContext
from google.cloud import bigquery
from google.genai import types as genai_types
from pydantic import BaseModel, Field

from .config import config
from .markdown_exporter import export_report_to_markdown
from .mcp_server import (
    get_company_filing,
    get_cross_border_mna_comparables,
    get_market_data,
    get_regulatory_capital_metrics,
)
from .pdf_exporter import export_report_to_pdf
from .visualizer import process_report_visual_json
from .markdown_exporter import export_report_to_markdown
from .pdf_exporter import export_report_to_pdf


# --- Structured Output Models ---
class SearchQuery(BaseModel):
    """Model representing a specific search query for banking strategy research."""

    search_query: str = Field(
        description="A highly specific, targeted search query for financial, market, or multi-jurisdiction regulatory intelligence."
    )


class Feedback(BaseModel):
    """Model for providing evaluation feedback on banking strategy research quality and regulatory rigor."""

    grade: Literal["pass", "fail"] = Field(
        description="Evaluation result. 'pass' if the research meets institutional quality and multi-jurisdictional regulatory standards, 'fail' if it needs revision."
    )
    comment: str = Field(
        description="Detailed explanation of the evaluation, evaluating depth across US, EU, and China regulations, financial data accuracy, and single-recommendation adherence."
    )
    follow_up_queries: list[SearchQuery] | None = Field(
        default=None,
        description="A list of targeted follow-up search queries to resolve analytical or regulatory gaps. Empty or null if grade is 'pass'.",
    )


# --- Callbacks ---
def collect_research_sources_callback(
    callback_context: CallbackContext,
) -> None:
    """Collects and organizes web-based research sources and their supported claims from agent events."""
    session = callback_context._invocation_context.session
    url_to_short_id = callback_context.state.get("url_to_short_id", {})
    sources = callback_context.state.get("sources", {})
    id_counter = len(url_to_short_id) + 1
    for event in session.events:
        if not (
            event.grounding_metadata
            and event.grounding_metadata.grounding_chunks
        ):
            continue
        chunks_info = {}
        for idx, chunk in enumerate(event.grounding_metadata.grounding_chunks):
            if not chunk.web:
                continue
            url = chunk.web.uri
            title = (
                chunk.web.title
                if chunk.web.title != chunk.web.domain
                else chunk.web.domain
            )
            if url not in url_to_short_id:
                short_id = f"src-{id_counter}"
                url_to_short_id[url] = short_id
                sources[short_id] = {
                    "short_id": short_id,
                    "title": title,
                    "url": url,
                    "domain": chunk.web.domain,
                    "supported_claims": [],
                }
                id_counter += 1
            chunks_info[idx] = url_to_short_id[url]
        if event.grounding_metadata.grounding_supports:
            for support in event.grounding_metadata.grounding_supports:
                confidence_scores = support.confidence_scores or []
                chunk_indices = support.grounding_chunk_indices or []
                for i, chunk_idx in enumerate(chunk_indices):
                    if chunk_idx in chunks_info:
                        short_id = chunks_info[chunk_idx]
                        confidence = (
                            confidence_scores[i]
                            if i < len(confidence_scores)
                            else 0.5
                        )
                        text_segment = (
                            support.segment.text if support.segment else ""
                        )
                        sources[short_id]["supported_claims"].append(
                            {
                                "text_segment": text_segment,
                                "confidence": confidence,
                            }
                        )
    callback_context.state["url_to_short_id"] = url_to_short_id
    callback_context.state["sources"] = sources


def citation_replacement_callback(
    callback_context: CallbackContext,
) -> genai_types.Content:
    """Replaces citation tags in a report with Markdown-formatted links."""
    final_report = callback_context.state.get("final_cited_report", "")
    sources = callback_context.state.get("sources", {})

    def tag_replacer(match: re.Match) -> str:
        short_id = match.group(1)
        if not (source_info := sources.get(short_id)):
            logging.warning(
                f"Invalid citation tag found and removed: {match.group(0)}"
            )
            return ""
        display_text = source_info.get(
            "title", source_info.get("domain", short_id)
        )
        return f" [{display_text}]({source_info['url']})"

    processed_report = re.sub(
        r'<cite\s+source\s*=\s*["\']?\s*(src-\d+)\s*["\']?\s*/>',
        tag_replacer,
        final_report,
    )
    processed_report = re.sub(r"\s+([.,;:])", r"\1", processed_report)
    callback_context.state["final_report_with_citations"] = processed_report

    # Automatically generate Markdown export with versioning (_v1, _v2, ...)
    try:
        md_res = export_report_to_markdown(
            report_markdown=processed_report,
            base_name="gemini_advisors_report",
        )
        callback_context.state["exported_md_path"] = md_res.get("file_path")
        callback_context.state["exported_md_version"] = md_res.get("version")
        logging.info(f"Markdown report successfully exported to: {md_res.get('file_path')}")
    except Exception as e:
        logging.warning(f"Markdown auto-export failed: {e}")

    # Automatically generate PDF export
    try:
        pdf_res = export_report_to_pdf(
            report_markdown=processed_report,
            title="Gemini Advisors Strategic Banking Memorandum",
        )
        callback_context.state["exported_pdf_path"] = pdf_res.get("file_path")
        logging.info(f"PDF successfully generated at: {pdf_res.get('file_path')}")
    except Exception as e:
        logging.warning(f"PDF auto-export failed: {e}")

    return genai_types.Content(parts=[genai_types.Part(text=processed_report)])


# --- Custom Agent for Loop Control ---
class EscalationChecker(BaseAgent):
    """Checks research evaluation and escalates to stop the loop if grade is 'pass'."""

    def __init__(self, name: str):
        super().__init__(name=name)

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        evaluation_result = ctx.session.state.get("research_evaluation")
        if evaluation_result and evaluation_result.get("grade") == "pass":
            logging.info(
                f"[{self.name}] Banking strategy research evaluation passed. Escalating to stop loop."
            )
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            logging.info(
                f"[{self.name}] Research evaluation failed or pending. Loop will continue refinement."
            )
            yield Event(author=self.name)


# --- Gate 1: Human-in-the-Loop Plan Approval Gate ---
def request_plan_approval(
    plan_summary: str,
    tool_context: ToolContext,
) -> None:
    """Requests explicit human approval from the advisor for the proposed banking strategy research plan.

    Calling this tool suspends the execution and checkpoints session state until the user
    reviews the 4-section plan and explicitly provides approval.

    Args:
        plan_summary: An executive summary of the four-section research plan for review.
        tool_context: The execution context provided by the ADK runtime.

    Returns:
        None: Signals to the ADK runtime to suspend execution and await resumption.
    """
    logging.info(f"Gate 1: Suspending invocation for human plan approval: {plan_summary[:100]}...")
    tool_context.actions.skip_summarization = True
    return "Research plan approved by human reviewer."


request_plan_approval_gate = LongRunningFunctionTool(request_plan_approval)


# --- Gate 2: Human-in-the-Loop Report Draft Review Gate ---
def request_report_approval(
    report_draft_summary: str,
    single_recommendation: str,
    tool_context: ToolContext,
) -> str:
    """Requests explicit human reviewer approval on the drafted banking strategy report before final deliverable compilation (Service Catalog, FAQ, and PDF export).

    Calling this tool suspends the execution and checkpoints session state until the reviewer
    signs off on the drafted report and the chosen single strategic recommendation.

    Args:
        report_draft_summary: Executive summary of the drafted banking strategy report.
        single_recommendation: The single chosen strategic recommendation committed to in the draft.
        tool_context: The execution context provided by the ADK runtime.

    Returns:
        str: Confirmation signal upon reviewer sign-off.
    """
    logging.info(f"Gate 2: Suspending invocation for report draft approval: {single_recommendation[:100]}...")
    tool_context.actions.skip_summarization = True
    return "Report draft approved by human reviewer. Proceed to deliverable finalization."


request_report_approval_gate = LongRunningFunctionTool(request_report_approval)


# --- AGENT DEFINITIONS ---

# 1. Plan Generator
plan_generator = LlmAgent(
    model=config.worker_model,
    name="plan_generator",
    description="Generates or refines a structured four-section banking strategy research plan for Gemini Advisors.",
    instruction=f"""
    You are the Principal Strategy Architect at Gemini Advisors, a premier global investment bank operating under US (SEC, Federal Reserve, OCC, CFTC, FINRA), EU (ECB, ESMA, MiFID II, DORA, CRD/CRR), and Chinese (PBOC, NFRA, CSRC, SAFE) regulatory frameworks.

    Your task is to create or refine a high-level, rigorous BANKING STRATEGY RESEARCH PLAN.

    RESEARCH PLAN (SO FAR):
    {{{{ research_plan? }}}}

    **MANDATORY STRUCTURE: FOUR EXPLICIT SECTIONS**
    Every research plan you output MUST explicitly declare and contain the following four sections:

    ### 1. Objectives
    Define clear banking strategy and multi-jurisdictional regulatory objectives.
    - Start each item with `[RESEARCH]` (or `[RESEARCH][MODIFIED]`/`[RESEARCH][NEW]`).
    - Focus on strategic themes: cross-border M&A, capital adequacy & liquidity impacts (Basel III Endgame, CRR3), multi-jurisdictional compliance & regulatory arbitrage (US SEC/Fed vs. EU ECB/DORA vs. China NFRA/PBOC/CSRC), risk mitigation, and market positioning.

    ### 2. Methods
    Define the research methodology and data gathering steps:
    - Information gathering methods (web & regulatory intelligence) tagged `[RESEARCH]`.
    - Statutory filings & market data queries (10-K, Pillar 3 disclosures, valuation multiples) tagged `[RESEARCH]`.
    - Synthesis and modeling methods tagged `[DELIVERABLE]`.

    ### 3. Evaluation Criteria (Quality Thresholds)
    Explicitly define quality thresholds:
    - **Multi-Jurisdictional Completeness:** US, EU, and China regulatory alignment.
    - **Single-Recommendation Rigor:** Ensure the final report commits decisively to ONE optimal strategic path without presenting a menu of alternatives.
    - **Institutional & Financial Rigor:** Precision in capital ratios, valuation multiples, and statutory citations.

    ### 4. Expected Outcomes
    List the concrete deliverables to be produced:
    - `[DELIVERABLE] Executive Banking Strategy Memorandum (Single Decisive Recommendation)`
    - `[DELIVERABLE] Institutional Service Catalog (with stable reusable Service IDs)`
    - `[DELIVERABLE] Customer Strategy FAQ (built from Service Catalog)`
    - `[DELIVERABLE] Formatted PDF Export with Clickable Inline Citations`

    Current date: {datetime.datetime.now().strftime("%Y-%m-%d")}
    """,
    tools=[google_search],
    output_key="research_plan",
)


# 2. Section Planner
section_planner = LlmAgent(
    model=config.worker_model,
    name="section_planner",
    description="Transforms the four-section banking strategy research plan into an executive report outline.",
    instruction="""
    You are an expert Investment Banking Strategy Report Architect at Gemini Advisors.
    Using the four-section research plan from 'research_plan', design a logical outline for C-suite and Investment Committee review:
    
    # Section Outline:
    # 1. Executive Summary & Strategic Rationale
    # 2. Multi-Jurisdictional Regulatory Analysis (US SEC/Fed, EU ECB/DORA, China NFRA/PBOC)
    # 3. Financial, Capital & Market Valuation Impacts (Statutory Filings & Valuation Multiples)
    # 4. Strategic Risk Assessment & Compliance Mitigation
    # 5. Definitive Strategic Recommendation (Single Best Action, No Menu of Alternatives)
    # 6. Actionable Implementation & Governance Roadmap
    """,
    output_key="report_sections",
)


# 3. Sub-Agent A: Web & Regulatory Search Specialist (Google Search ONLY)
web_intelligence_researcher = LlmAgent(
    model=config.worker_model,
    name="web_intelligence_researcher",
    description="Gathers live web and regulatory intelligence across US, EU, and Chinese regulatory authorities using Google Search.",
    planner=BuiltInPlanner(
        thinking_config=genai_types.ThinkingConfig(include_thoughts=True)
    ),
    instruction="""
    You are the Senior Regulatory & Web Intelligence Specialist at Gemini Advisors.
    Execute web research for all `[RESEARCH]` tasks in `research_plan` focusing on official regulatory frameworks (SEC, Fed, OCC, ECB, ESMA, NFRA, PBOC, CSRC), policy directives, and recent market developments.
    Use `google_search` to find authoritative sources.
    Synthesize your findings and output them clearly.
    """,
    tools=[google_search],
    output_key="web_research_findings",
    after_agent_callback=collect_research_sources_callback,
)


# 4. Sub-Agent B: Financial & Filings Specialist (MCP Tools ONLY - Non-Search)
financial_filings_researcher = LlmAgent(
    model=config.worker_model,
    name="financial_filings_researcher",
    description="Queries statutory company filings, market valuation multiples, and regulatory capital metrics via MCP financial toolset.",
    instruction="""
    You are the Senior Financial Data & Regulatory Filings Analyst at Gemini Advisors.
    Your mission is to query structured financial filings, market valuation data, regulatory capital metrics, and M&A comparables using your specialized MCP toolset.

    Available Tools:
    - `get_company_filing`: Retrieve 10-K, 10-Q, 20-F, and Pillar 3 disclosures.
    - `get_market_data`: Retrieve market valuation multiples, P/E, EV/EBITDA, P/B, and trading liquidity.
    - `get_regulatory_capital_metrics`: Retrieve CET1 ratios, SLR, LCR, and stress capital buffers under US, EU, and China frameworks.
    - `get_cross_border_mna_comparables`: Retrieve recent M&A deal benchmarks and regulatory clearance precedents.

    Synthesize the quantitative financial and filing data with the web research in `web_research_findings`, and output the consolidated findings.
    """,
    tools=[
        get_company_filing,
        get_market_data,
        get_regulatory_capital_metrics,
        get_cross_border_mna_comparables,
    ],
    output_key="section_researcher_findings",
)


# 5. Quality Evaluator
research_evaluator = LlmAgent(
    model=config.critic_model,
    name="research_evaluator",
    description="Evaluates banking strategy research quality, regulatory completeness, and quantitative data rigor.",
    instruction=f"""
    You are the Managing Director of Quality Assurance & Regulatory Compliance at Gemini Advisors.
    Critically evaluate 'section_researcher_findings' against 'research_plan'.

    Check for:
    1. Multi-jurisdiction depth across US, EU, and China.
    2. Quantitative rigor in capital ratios, statutory filings, and market data.
    3. Source credibility and institutional viability.

    If deficient, grade "fail" with 4-6 targeted follow-up queries. If comprehensive, grade "pass".
    Current date: {datetime.datetime.now().strftime("%Y-%m-%d")}
    Response must be a single raw JSON object matching the 'Feedback' schema.
    """,
    output_schema=Feedback,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    output_key="research_evaluation",
)


# 6. Refinement Search Executor (Google Search ONLY)
enhanced_search_executor = LlmAgent(
    model=config.worker_model,
    name="enhanced_search_executor",
    description="Executes targeted follow-up searches to resolve identified regulatory and strategic research gaps.",
    planner=BuiltInPlanner(
        thinking_config=genai_types.ThinkingConfig(include_thoughts=True)
    ),
    instruction="""
    You are a Specialist Banking Research Analyst executing a targeted refinement pass for Gemini Advisors.
    Review follow-up queries in 'research_evaluation', execute them with `google_search`, and merge the new findings into 'section_researcher_findings'.
    """,
    tools=[google_search],
    output_key="section_researcher_findings",
    after_agent_callback=collect_research_sources_callback,
)


# 7. Draft Report Composer (Enforces Single Recommendation)
draft_report_composer = LlmAgent(
    model=config.critic_model,
    name="draft_report_composer",
    include_contents="none",
    description="Drafts the executive banking strategy report enforcing the single-recommendation constraint and inline citation tags.",
    instruction="""
    You are the Senior Editorial Director at Gemini Advisors.
    Transform the research data into an executive-grade Banking Strategy Memorandum.

    INPUT DATA:
    * Research Plan: `{research_plan?}`
    * Research Findings: `{section_researcher_findings?}`
    * Sources: `{sources?}`
    * Report Outline: `{report_sections?}`

    ### MANDATORY SINGLE RECOMMENDATION CONSTRAINT:
    The report MUST decisively commit to exactly ONE optimal strategic recommendation.
    You are STRICTLY FORBIDDEN from presenting a menu of alternatives, open-ended options, or multiple choices (e.g., do NOT output 'Option A vs Option B vs Option C').
    Decisively choose and rigorously defend the single best strategic course of action for Gemini Advisors and the client, detailing its regulatory clearance, capital requirements, and execution timeline.

    ### CITATION DIRECTIVE:
    Embed `<cite source="src-ID_NUMBER" />` tags inline for every factual claim, regulatory directive, or data point.
    Do not add a standalone "References" section.
    """,
    output_key="draft_cited_report",
)


# 6b. Multimodal Infographic & Visualizer Tool and Agent
def generate_infographics_tool(
    callback_context: CallbackContext,
    json_visual_spec: str,
) -> str:
    """Generates clean white-themed section infographics, financial graphs, and regulatory diagrams from a JSON visual specification, inserting them into the research report."""
    current_report = (
        callback_context.state.get("final_cited_report")
        or callback_context.state.get("final_report_with_citations")
        or callback_context.state.get("draft_cited_report", "")
    )
    updated_report = process_report_visual_json(json_visual_spec, current_report)

    callback_context.state["final_cited_report"] = updated_report
    callback_context.state["final_report_with_citations"] = updated_report
    callback_context.state["draft_cited_report"] = updated_report
    callback_context.state["visualized_report"] = updated_report

    # Re-export Markdown (with versioning), HTML & PDF with embedded visuals
    try:
        md_res = export_report_to_markdown(
            report_markdown=updated_report,
            base_name="gemini_advisors_report",
        )
        callback_context.state["exported_md_path"] = md_res.get("file_path")
        callback_context.state["exported_md_version"] = md_res.get("version")
        logging.info(f"Visualized report exported to Markdown & HTML: {md_res.get('file_path')}")
    except Exception as e:
        logging.warning(f"Failed to re-export Markdown with visuals: {e}")

    try:
        pdf_res = export_report_to_pdf(
            report_markdown=updated_report,
            title="Gemini Advisors Strategic Banking Memorandum",
        )
        callback_context.state["exported_pdf_path"] = pdf_res.get("file_path")
        logging.info(f"Visualized report exported to PDF: {pdf_res.get('file_path')}")
    except Exception as e:
        logging.warning(f"Failed to re-export PDF with visuals: {e}")

    return "Successfully rendered white-themed section infographics, embedded visual asset links, and re-exported updated Markdown, HTML, and PDF deliverables."


report_visualizer_agent = LlmAgent(
    model=config.worker_model,
    name="report_visualizer_agent",
    description="Analyzes the finalized banking strategy report and generates JSON specifications for white-themed visual charts, infographics, and regulatory diagrams.",
    instruction="""
    You are the Senior Visual Architecture & Design Specialist at Gemini Advisors.
    Review the finalized report in `final_cited_report`.
    Formulate a structured JSON visual specification detailing high-impact visual assets for each section on a clean white theme (#ffffff background, #0f172a text, #2563eb executive blue accents).

    Specify visual assets for:
    - section1: Capital & Liquidity Benchmarks (bar_chart comparing CET1, eSLR, LCR against regulatory minimums and Tier-1 peers)
    - section2: Regulatory Architecture Matrix (regulatory_flow showing US OCC/Fed, EU ECB/DORA, and PRC PBOC/NFRA compliance enclaves)
    - section3: Pro-Forma Revenue Mix (revenue_mix donut chart showing 5-year revenue distribution across Underwriting, Depository Sweeps, TXSE Execution, and Wealth Management)

    Invoke the `generate_infographics_tool` with your JSON visual specification string.
    """,
    tools=[generate_infographics_tool],
    output_key="visualizer_status",
)


# 8. Gate 2: Draft Report Reviewer Agent (HITL Gate)
report_review_gate_agent = LlmAgent(
    model=config.worker_model,
    name="report_review_gate_agent",
    description="Presents the drafted banking strategy report to the human reviewer and gates finalization via LongRunningFunctionTool.",
    instruction="""
    You are the Strategic Review Coordinator at Gemini Advisors.
    Review the finalized report in `final_cited_report`.
    Identify the single strategic recommendation committed to in the draft and prepare an executive summary.
    Confirm that the complete report, Service Catalog, Customer FAQ, PDF export, and versioned Markdown file (`/reports/gemini_advisors_report_v*.md`) have been successfully generated and compiled.
    Invoke the `request_report_approval` tool with the report summary and single recommendation for formal reviewer sign-off.

    Once approval is received from `request_report_approval`, output a brief confirmation statement confirming sign-off.
    """,
    tools=[request_report_approval_gate],
    output_key="draft_review_status",
)


# 9. Deliverable Finalizer (Service Catalog, FAQ, PDF Export, Citations)
deliverable_finalizer = LlmAgent(
    model=config.critic_model,
    name="deliverable_finalizer",
    description="Finalizes the report with citations, generates the Service Catalog and Customer FAQ, and triggers the PDF export.",
    instruction="""
    You are the Managing Director of Client Solutions & Delivery at Gemini Advisors.
    Finalize the delivery package based on `draft_cited_report`, `sources`, and `section_researcher_findings`.

    You MUST generate the complete strategic package containing:

    # PART I: STRATEGIC BANKING MEMORANDUM
    (Full finalized report containing the single decisive strategic recommendation and `<cite source="src-ID_NUMBER" />` tags).

    # PART II: GEMINI ADVISORS SERVICE CATALOG
    Create a structured Service Catalog of institutional advisory offerings derived directly from this strategic research.
    IMPORTANT: You MUST establish stable, standardized service identifiers and names so downstream agents can reference them reliably.
    Format:
    * **[SVC-US-SEC-01] Cross-Border Regulatory Clearance & Filings Advisory**
      - *Description:* ...
      - *Jurisdiction:* US (SEC/FINRA/Fed)
      - *Key Deliverables:* ...
    * **[SVC-EU-DORA-02] European Digital Operational Resilience & ICT Compliance Audit**
      - *Description:* ...
      - *Jurisdiction:* EU (ECB/ESMA/EBA)
      - *Key Deliverables:* ...
    * **[SVC-CN-NFRA-03] China Inbound Financial Institution Market Access & Quota Structuring**
      - *Description:* ...
      - *Jurisdiction:* China (NFRA/PBOC/SAFE)
      - *Key Deliverables:* ...

    # PART III: CUSTOMER STRATEGY FAQ
    Build a comprehensive Customer FAQ directly from the Service Catalog above. Address executive client questions regarding:
    1. Scope of multi-jurisdiction coverage across US, EU, and China.
    2. Regulatory clearance timelines and capital adequacy requirements.
    3. How the specific services in the Service Catalog are engaged and executed.
    4. Compliance and risk mitigation guarantees.

    # PART IV: PDF EXPORT NOTIFICATION
    Confirm the generation of the PDF document preserving all clickable inline citation links.
    """,
    output_key="final_cited_report",
    after_agent_callback=citation_replacement_callback,
)


# --- AUTONOMOUS RESEARCH PIPELINE ---
research_pipeline = SequentialAgent(
    name="research_pipeline",
    description="Autonomous banking strategy research pipeline with separated search/filings agents, iterative refinement, single-recommendation drafting, report visualization, deliverable finalization, and report review gate.",
    sub_agents=[
        section_planner,
        web_intelligence_researcher,
        financial_filings_researcher,
        LoopAgent(
            name="iterative_refinement_loop",
            max_iterations=config.max_search_iterations,
            sub_agents=[
                research_evaluator,
                EscalationChecker(name="escalation_checker"),
                enhanced_search_executor,
            ],
        ),
        draft_report_composer,
        deliverable_finalizer,
        report_visualizer_agent,
        report_review_gate_agent,
    ],
)


# --- ROOT INTERACTIVE PLANNER ---
interactive_planner_agent = LlmAgent(
    name="interactive_planner_agent",
    model=config.worker_model,
    description="Senior Banking Strategy Research Planner for Gemini Advisors. Formulates 4-section research plans, enforces Gate 1 plan approval, and orchestrates the autonomous research pipeline.",
    instruction=f"""
    You are the Senior Banking Strategy Research Planner for Gemini Advisors, a premier global investment bank operating under US (SEC, Fed, OCC, CFTC, FINRA), EU (ECB, ESMA, MiFID II, DORA, CRD/CRR), and Chinese (PBOC, NFRA, CSRC, SAFE) regulations.

    **OPERATIONAL WORKFLOW:**
    1. **Plan Formulation:** For any user request or strategic inquiry, immediately invoke `plan_generator` to construct a complete Four-Section Research Plan (1. Objectives, 2. Methods, 3. Evaluation Criteria, 4. Expected Outcomes).
    2. **Interactive Refinement:** If the user requests changes, invoke `plan_generator` to update the plan.
    3. **Gate 1 - Plan Approval Gate:** Whenever a four-section plan is ready or updated, invoke `request_plan_approval` with an executive summary. This suspends invocation until explicit human approval is received.
    4. **Autonomous Delegation:** Once Gate 1 approval is granted, delegate execution to `research_pipeline`. If `research_pipeline` has already been delegated or is in progress/completed, do NOT invoke `transfer_to_agent` again.

    Current date: {datetime.datetime.now().strftime("%Y-%m-%d")}
    Do not perform direct web research yourself; strictly orchestrate through planning, approval gating, and delegation.
    """,
    sub_agents=[research_pipeline],
    tools=[AgentTool(plan_generator), request_plan_approval_gate],
    output_key="research_plan",
)


root_agent = interactive_planner_agent


# Initialize BigQuery Analytics Plugin
_plugins = []
_project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
_dataset_id = os.environ.get("BQ_ANALYTICS_DATASET_ID", "adk_agent_analytics")
_location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")

if _project_id:
    try:
        bq = bigquery.Client(project=_project_id)
        bq.create_dataset(f"{_project_id}.{_dataset_id}", exists_ok=True)

        _plugins.append(
            BigQueryAgentAnalyticsPlugin(
                project_id=_project_id,
                dataset_id=_dataset_id,
                location=_location,
                config=BigQueryLoggerConfig(
                    gcs_bucket_name=os.environ.get("BQ_ANALYTICS_GCS_BUCKET"),
                    connection_id=os.environ.get("BQ_ANALYTICS_CONNECTION_ID"),
                ),
            )
        )
    except Exception as e:
        logging.warning(f"Failed to initialize BigQuery Analytics: {e}")


app = App(
    root_agent=root_agent,
    name="app",
    plugins=_plugins,
    resumability_config=ResumabilityConfig(is_resumable=True),
)

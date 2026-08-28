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

"""MCP Server for financial market data, company filings, and regulatory metrics."""

import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("GeminiAdvisorsFinancialData")


@mcp.tool()
def get_company_filing(
    ticker_or_name: str,
    filing_type: str = "10-K",
    jurisdiction: str = "US",
) -> str:
    """Retrieves statutory financial filings and regulatory disclosures for public institutions and corporations.

    Args:
        ticker_or_name: Ticker symbol or corporate entity name (e.g., 'JPM', 'BNP', 'ICBC', '601398.SS').
        filing_type: Type of filing: '10-K', '10-Q', '8-K', '20-F', 'Annual Report', 'Pillar 3 Disclosure'.
        jurisdiction: Regulatory jurisdiction: 'US' (SEC), 'EU' (ESMA/Euronext), 'China' (CSRC/HKEX/SSE).

    Returns:
        Structured summary of statutory filing data, financial statements, and regulatory notes.
    """
    entity = ticker_or_name.upper().strip()
    jur = jurisdiction.upper().strip()

    return json.dumps(
        {
            "entity": entity,
            "filing_type": filing_type,
            "jurisdiction": jur,
            "reporting_period": "FY2025 / Q3-2025",
            "statutory_authority": (
                "US Securities and Exchange Commission (SEC)"
                if jur == "US"
                else "European Securities and Markets Authority (ESMA)"
                if jur == "EU"
                else "China Securities Regulatory Commission (CSRC) / HKEX"
            ),
            "financial_summary": {
                "total_assets_usd_bn": 3840.5,
                "net_revenue_usd_bn": 162.4,
                "net_income_usd_bn": 48.2,
                "return_on_tangible_common_equity_pct": 19.5,
                "tier_1_leverage_ratio_pct": 7.1,
            },
            "regulatory_capital_disclosures": {
                "common_equity_tier_1_cet1_ratio_pct": 15.3,
                "total_risk_weighted_assets_rwa_usd_bn": 1720.0,
                "liquidity_coverage_ratio_lcr_pct": 142.0,
                "net_stable_funding_ratio_nsfr_pct": 118.0,
            },
            "key_risk_factors": [
                f"Multi-jurisdiction regulatory compliance obligations across US, EU, and China.",
                f"Implementation costs and RWA inflation under Basel III Endgame / CRR3 standards.",
                f"Operational resilience and ICT risk management under EU DORA and US Fed guidelines.",
                f"Cross-border capital flow and foreign exchange quota constraints under China SAFE rules.",
            ],
            "business_segment_revenue_breakdown": {
                "Global Investment Banking & Advisory": "28%",
                "Corporate Banking & Lending": "34%",
                "Global Markets & Securities": "26%",
                "Asset & Wealth Management": "12%",
            },
        },
        indent=2,
    )


@mcp.tool()
def get_market_data(
    ticker_or_name: str,
    jurisdiction: str = "US",
) -> str:
    """Retrieves live market pricing, valuation multiples, liquidity, and trading metrics.

    Args:
        ticker_or_name: Ticker symbol or company name.
        jurisdiction: Market jurisdiction ('US', 'EU', 'China').

    Returns:
        Structured market and valuation data including P/E, EV/EBITDA, Price/Book, and Beta.
    """
    entity = ticker_or_name.upper().strip()
    return json.dumps(
        {
            "ticker": entity,
            "jurisdiction": jurisdiction.upper(),
            "market_cap_usd_bn": 580.2,
            "enterprise_value_usd_bn": 640.8,
            "valuation_multiples": {
                "price_to_earnings_pe_ttm": 11.8,
                "forward_pe_1yr": 10.4,
                "price_to_book_pb": 1.45,
                "price_to_tangible_book_ptbv": 1.72,
                "ev_to_ebitda": 8.9,
            },
            "trading_and_volatility": {
                "beta_5yr_monthly": 1.12,
                "dividend_yield_pct": 2.85,
                "avg_daily_volume_shares_mn": 9.4,
                "52_week_high_usd": 215.0,
                "52_week_low_usd": 152.5,
            },
            "credit_ratings": {
                "sp_global": "A+",
                "moodys": "Aa3",
                "fitch": "AA-",
                "outlook": "Stable",
            },
        },
        indent=2,
    )


@mcp.tool()
def get_regulatory_capital_metrics(
    bank_or_institution: str,
    jurisdiction: str = "US",
) -> str:
    """Retrieves Basel III/IV, CRD/CRR, and NFRA regulatory capital adequacy ratios and buffer requirements.

    Args:
        bank_or_institution: Name or identifier of the banking institution.
        jurisdiction: Regulatory framework jurisdiction ('US', 'EU', 'China').

    Returns:
        Detailed regulatory capital ratios, stress testing buffers, and minimum regulatory thresholds.
    """
    jur = jurisdiction.upper()
    framework = (
        "US Dodd-Frank / Federal Reserve Comprehensive Capital Analysis and Review (CCAR)"
        if jur == "US"
        else "EU Capital Requirements Regulation III (CRR3) / ECB Single Supervisory Mechanism"
        if jur == "EU"
        else "China National Financial Regulatory Administration (NFRA) Capital Rules"
    )

    return json.dumps(
        {
            "institution": bank_or_institution,
            "framework": framework,
            "jurisdiction": jur,
            "capital_ratios": {
                "cet1_ratio_actual_pct": 14.8,
                "cet1_minimum_regulatory_pct": 4.5,
                "capital_conservation_buffer_pct": 2.5,
                "gsib_surcharge_pct": 2.0,
                "stress_capital_buffer_scb_pct": 3.2,
                "total_cet1_requirement_pct": 12.2,
                "cet1_management_cushion_bps": 260,
            },
            "leverage_and_liquidity": {
                "supplementary_leverage_ratio_slr_pct": 6.2,
                "slr_requirement_pct": 5.0,
                "liquidity_coverage_ratio_lcr_pct": 138.5,
                "net_stable_funding_ratio_nsfr_pct": 116.2,
            },
            "regulatory_assessment": "Well-capitalized across all standard and stressed stress scenarios.",
        },
        indent=2,
    )


@mcp.tool()
def get_cross_border_mna_comparables(
    sector: str,
    target_jurisdiction: str = "EU",
) -> str:
    """Retrieves recent cross-border M&A transactions, deal multiples, and regulatory clearance precedents across US, EU, and China.

    Args:
        sector: Industry sector (e.g., 'Financial Institutions Group (FIG)', 'Fintech', 'Commercial Banking').
        target_jurisdiction: Target geographic market ('US', 'EU', 'China', 'Cross-Border').

    Returns:
        Benchmark transactions, EV/EBITDA multiples, premium paid, and regulatory clearance timelines.
    """
    return json.dumps(
        {
            "sector": sector,
            "target_jurisdiction": target_jurisdiction,
            "recent_benchmark_transactions": [
                {
                    "deal_name": "Transatlantic Financial Services Combination",
                    "acquirer_jurisdiction": "US",
                    "target_jurisdiction": "EU",
                    "deal_value_usd_bn": 14.2,
                    "implied_ev_ebitda": 11.4,
                    "target_premium_pct": 28.5,
                    "regulatory_conditions": [
                        "ECB Section 22 Qualifying Holding Approval",
                        "EU Foreign Subsidies Regulation (FSR) clearance",
                        "US Fed Rule H approval for foreign bank branch operations",
                    ],
                    "clearance_timeline_months": 11,
                },
                {
                    "deal_name": "Sino-European Strategic Asset Management JV",
                    "acquirer_jurisdiction": "EU",
                    "target_jurisdiction": "China",
                    "deal_value_usd_bn": 4.8,
                    "implied_ev_ebitda": 13.8,
                    "target_premium_pct": 22.0,
                    "regulatory_conditions": [
                        "China NFRA Market Entry Approval",
                        "CSRC Foreign Shareholding Authorization",
                        "SAFE Cross-Border Capital Remittance Verification",
                    ],
                    "clearance_timeline_months": 14,
                },
            ],
            "median_deal_multiples": {
                "ev_to_ebitda": 12.1,
                "price_to_tangible_book": 1.65,
                "median_premium_pct": 25.0,
            },
        },
        indent=2,
    )


if __name__ == "__main__":
    mcp.run()

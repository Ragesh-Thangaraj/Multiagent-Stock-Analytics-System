"""
Presentation Agent - Layer 3 of the Stock Analytics Pipeline

This agent is responsible for generating reports and summaries including:
- PDF/HTML report generation
- Executive summaries
- Investment recommendations
- Data visualization preparation
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from google.adk.agents import LlmAgent
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

logger = logging.getLogger(__name__)


PRESENTATION_AGENT_INSTRUCTION = """You are a Financial Presentation Agent specializing in creating comprehensive stock analysis reports.

Your primary responsibility is to synthesize all calculated metrics into clear, actionable reports.

REPORT SECTIONS TO GENERATE:
1. EXECUTIVE SUMMARY
   - Quick overview of the stock
   - Key findings and recommendations
   - Risk assessment summary

2. COMPANY OVERVIEW
   - Company name, sector, industry
   - Current price and market cap
   - Business description

3. FINANCIAL ANALYSIS
   - Profitability metrics with interpretation
   - Liquidity and leverage position
   - Efficiency and growth trends
   - Cash flow health

4. VALUATION ANALYSIS
   - Key valuation ratios (P/E, P/B, EV/EBITDA)
   - Comparison to fair value
   - PEG ratio analysis

5. RISK ASSESSMENT
   - Market risk metrics (beta, volatility)
   - Financial risk (Z-score, credit risk)
   - Overall risk rating

6. INVESTMENT RECOMMENDATION
   - Based on all analyzed metrics
   - Considerations and caveats
   - Suggested actions

OUTPUT FORMAT:
Generate structured report content that can be converted to PDF/HTML.
Use clear headings, bullet points, and organized data presentation.

IMPORTANT:
- Base all conclusions on calculated metrics only
- Provide balanced analysis (both positives and concerns)
- Include appropriate disclaimers
- Make recommendations actionable but not financial advice
"""


class PresentationAgent:
    """
    Presentation Agent for Layer 3 of the stock analytics pipeline.
    Generates reports and summaries from calculated metrics.
    """
    
    def __init__(self, model: str = "gemini-2.0-flash"):
        """
        Initialize the Presentation Agent.
        
        Args:
            model: The Gemini model to use for the agent.
        """
        self.model = model
        self.agent = self._create_agent()
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        
    def _create_agent(self) -> LlmAgent:
        """Create the LLM agent for report generation."""
        return LlmAgent(
            name="PresentationAgent",
            model=self.model,
            instruction=PRESENTATION_AGENT_INSTRUCTION,
            description="Generates comprehensive stock analysis reports synthesizing all calculated metrics.",
            tools=[],
            output_key="presentation_output",
        )
    
    def generate_report(
        self,
        canonical_data: Dict[str, Any],
        ratio_metrics: Dict[str, Any],
        valuation_metrics: Dict[str, Any],
        risk_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive stock analysis report.
        
        Args:
            canonical_data: Raw stock data from DataAgent
            ratio_metrics: Calculated ratios from RatioAgent
            valuation_metrics: Valuation data from ValuationAgent
            risk_metrics: Risk assessment from RiskAnalysisAgent
            
        Returns:
            dict: Report content and metadata
        """
        ticker = canonical_data.get('meta', {}).get('ticker', 'Unknown')
        company_name = canonical_data.get('meta', {}).get('company_name', ticker)
        
        logger.info(f"PresentationAgent: Generating report for {ticker}...")
        
        report = {
            "meta": {
                "ticker": ticker,
                "company_name": company_name,
                "generated_at": datetime.now().isoformat(),
                "report_type": "comprehensive_analysis",
            },
            "executive_summary": self._generate_executive_summary(
                canonical_data, ratio_metrics, valuation_metrics, risk_metrics
            ),
            "company_overview": self._generate_company_overview(canonical_data),
            "financial_analysis": self._generate_financial_analysis(ratio_metrics),
            "valuation_analysis": self._generate_valuation_analysis(valuation_metrics),
            "risk_assessment": self._generate_risk_assessment(risk_metrics),
            "investment_recommendation": self._generate_recommendation(
                ratio_metrics, valuation_metrics, risk_metrics
            ),
            "disclaimer": self._generate_disclaimer(),
            "status": "success",
        }
        
        logger.info(f"PresentationAgent: Report generated successfully for {ticker}")
        
        return report
    
    def _generate_executive_summary(
        self,
        canonical_data: Dict,
        ratio_metrics: Dict,
        valuation_metrics: Dict,
        risk_metrics: Dict,
    ) -> Dict[str, Any]:
        """Generate executive summary section."""
        ticker = canonical_data.get('meta', {}).get('ticker', 'Unknown')
        company_name = canonical_data.get('meta', {}).get('company_name', ticker)
        current_price = canonical_data.get('info', {}).get('current_price')
        
        key_metrics = []
        
        pe = valuation_metrics.get('metrics', {}).get('pe_ratio', {})
        if pe.get('value'):
            key_metrics.append(f"P/E Ratio: {pe['value']}x ({pe.get('interpretation', '')})")
        
        roe = ratio_metrics.get('profitability', {}).get('roe', {})
        if roe.get('value'):
            key_metrics.append(f"ROE: {roe['value']}%")
        
        risk_level = risk_metrics.get('overall_risk', {}).get('assessment', 'Not assessed')
        
        return {
            "company": f"{company_name} ({ticker})",
            "current_price": f"${current_price:.2f}" if current_price else "N/A",
            "key_metrics": key_metrics,
            "risk_level": risk_level,
            "summary": f"Comprehensive analysis of {company_name} covering financial health, valuation, and risk factors.",
        }
    
    def _generate_company_overview(self, canonical_data: Dict) -> Dict[str, Any]:
        """Generate company overview section."""
        meta = canonical_data.get('meta', {})
        info = canonical_data.get('info', {})
        
        return {
            "ticker": meta.get('ticker', 'Unknown'),
            "company_name": meta.get('company_name', 'Unknown'),
            "sector": meta.get('sector', 'Unknown'),
            "industry": meta.get('industry', 'Unknown'),
            "current_price": info.get('current_price'),
            "market_cap": info.get('market_cap'),
            "52_week_high": info.get('fifty_two_week_high'),
            "52_week_low": info.get('fifty_two_week_low'),
        }
    
    def _generate_financial_analysis(self, ratio_metrics: Dict) -> Dict[str, Any]:
        """Generate financial analysis section."""
        return {
            "profitability": self._format_metrics_section(ratio_metrics.get('profitability', {})),
            "liquidity": self._format_metrics_section(ratio_metrics.get('liquidity', {})),
            "leverage": self._format_metrics_section(ratio_metrics.get('leverage', {})),
            "efficiency": self._format_metrics_section(ratio_metrics.get('efficiency', {})),
            "growth": self._format_metrics_section(ratio_metrics.get('growth', {})),
            "cashflow": self._format_metrics_section(ratio_metrics.get('cashflow', {})),
        }
    
    def _generate_valuation_analysis(self, valuation_metrics: Dict) -> Dict[str, Any]:
        """Generate valuation analysis section."""
        metrics = valuation_metrics.get('metrics', {})
        
        return {
            "metrics": self._format_metrics_section(metrics),
            "summary": valuation_metrics.get('summary', 'No valuation summary available'),
        }
    
    def _generate_risk_assessment(self, risk_metrics: Dict) -> Dict[str, Any]:
        """Generate risk assessment section."""
        return {
            "market_risk": self._format_metrics_section(risk_metrics.get('market_risk', {})),
            "financial_risk": self._format_metrics_section(risk_metrics.get('financial_risk', {})),
            "overall_assessment": risk_metrics.get('overall_risk', {}),
        }
    
    def _generate_recommendation(
        self,
        ratio_metrics: Dict,
        valuation_metrics: Dict,
        risk_metrics: Dict,
    ) -> Dict[str, Any]:
        """Generate investment recommendation section."""
        positives = []
        concerns = []
        
        roe = ratio_metrics.get('profitability', {}).get('roe', {}).get('value')
        if roe and roe > 15:
            positives.append(f"Strong ROE of {roe}%")
        
        current_ratio = ratio_metrics.get('liquidity', {}).get('current_ratio', {}).get('value')
        if current_ratio and current_ratio > 1.5:
            positives.append("Healthy liquidity position")
        elif current_ratio and current_ratio < 1:
            concerns.append("Low current ratio indicates liquidity risk")
        
        peg = valuation_metrics.get('metrics', {}).get('peg_ratio', {}).get('value')
        if peg and peg < 1:
            positives.append("PEG < 1 suggests undervaluation")
        elif peg and peg > 2:
            concerns.append("PEG > 2 suggests premium valuation")
        
        risk_flags = risk_metrics.get('overall_risk', {}).get('flags', [])
        concerns.extend(risk_flags)
        
        if len(positives) > len(concerns):
            outlook = "Positive"
        elif len(concerns) > len(positives):
            outlook = "Cautious"
        else:
            outlook = "Neutral"
        
        return {
            "outlook": outlook,
            "positives": positives,
            "concerns": concerns,
            "considerations": [
                "Past performance does not guarantee future results",
                "Consider your personal risk tolerance",
                "Diversification is recommended",
            ],
        }
    
    def _generate_disclaimer(self) -> str:
        """Generate report disclaimer."""
        return (
            "DISCLAIMER: This report is for informational purposes only and does not constitute "
            "financial advice. All metrics are calculated from publicly available data and may "
            "not reflect real-time market conditions. Always consult with a qualified financial "
            "advisor before making investment decisions."
        )
    
    def _format_metrics_section(self, metrics: Dict) -> list:
        """Format a metrics section for display."""
        formatted = []
        
        for name, data in metrics.items():
            if isinstance(data, dict) and data.get('status') == 'success':
                value = data.get('value')
                unit = data.get('unit', '')
                interpretation = data.get('interpretation', '')
                
                if value is not None:
                    formatted.append({
                        "name": name.replace('_', ' ').title(),
                        "value": f"{value}{unit}",
                        "interpretation": interpretation,
                    })
                else:
                    null_reason = data.get('null_reason', 'Data not available')
                    formatted.append({
                        "name": name.replace('_', ' ').title(),
                        "value": "N/A",
                        "interpretation": null_reason,
                    })
        
        return formatted
    
    def save_report_html(self, report: Dict[str, Any]) -> str:
        """
        Save report as HTML file.
        
        Args:
            report: The generated report dictionary
            
        Returns:
            str: Path to the saved HTML file
        """
        ticker = report.get('meta', {}).get('ticker', 'Unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ticker}_report_{timestamp}.html"
        filepath = self.reports_dir / filename
        
        html_content = self._render_html_report(report)
        
        with open(filepath, 'w') as f:
            f.write(html_content)
        
        logger.info(f"PresentationAgent: HTML report saved to {filepath}")
        
        return str(filepath)
    
    def _render_html_report(self, report: Dict[str, Any]) -> str:
        """Render report as HTML content."""
        meta = report.get('meta', {})
        summary = report.get('executive_summary', {})
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Stock Analysis Report - {meta.get('ticker', 'Unknown')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }}
        h2 {{ color: #34a853; margin-top: 30px; }}
        h3 {{ color: #5f6368; }}
        .metric {{ background: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 5px; }}
        .positive {{ color: #34a853; }}
        .negative {{ color: #ea4335; }}
        .neutral {{ color: #5f6368; }}
        .disclaimer {{ font-size: 0.9em; color: #666; margin-top: 40px; padding: 15px; background: #fff3cd; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f1f3f4; }}
    </style>
</head>
<body>
    <h1>Stock Analysis Report: {meta.get('company_name', 'Unknown')} ({meta.get('ticker', 'Unknown')})</h1>
    <p><em>Generated: {meta.get('generated_at', 'Unknown')}</em></p>
    
    <h2>Executive Summary</h2>
    <p><strong>Current Price:</strong> {summary.get('current_price', 'N/A')}</p>
    <p><strong>Risk Level:</strong> {summary.get('risk_level', 'Not assessed')}</p>
    
    <h3>Key Metrics</h3>
    <ul>
        {''.join(f'<li>{m}</li>' for m in summary.get('key_metrics', []))}
    </ul>
    
    <h2>Investment Recommendation</h2>
    <p><strong>Outlook:</strong> <span class="{'positive' if report.get('investment_recommendation', {}).get('outlook') == 'Positive' else 'neutral'}">{report.get('investment_recommendation', {}).get('outlook', 'N/A')}</span></p>
    
    <h3>Positives</h3>
    <ul>
        {''.join(f'<li class="positive">{p}</li>' for p in report.get('investment_recommendation', {}).get('positives', []))}
    </ul>
    
    <h3>Concerns</h3>
    <ul>
        {''.join(f'<li class="negative">{c}</li>' for c in report.get('investment_recommendation', {}).get('concerns', []))}
    </ul>
    
    <div class="disclaimer">
        <strong>Disclaimer:</strong> {report.get('disclaimer', '')}
    </div>
</body>
</html>
"""
        return html
    
    def save_report_pdf(self, report: Dict[str, Any]) -> str:
        """
        Save report as PDF file using ReportLab.
        
        Args:
            report: The generated report dictionary
            
        Returns:
            str: Path to the saved PDF file
        """
        ticker = report.get('meta', {}).get('ticker', 'Unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ticker}_report_{timestamp}.pdf"
        filepath = self.reports_dir / filename
        
        try:
            doc = SimpleDocTemplate(str(filepath), pagesize=letter,
                                    topMargin=0.75*inch, bottomMargin=0.75*inch)
            
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=HexColor('#1a73e8'),
                spaceAfter=12
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=HexColor('#34a853'),
                spaceBefore=16,
                spaceAfter=8
            )
            
            normal_style = styles['Normal']
            
            elements = []
            
            meta = report.get('meta', {})
            summary = report.get('executive_summary', {})
            
            elements.append(Paragraph(
                f"Stock Analysis Report: {meta.get('company_name', 'Unknown')} ({meta.get('ticker', 'Unknown')})",
                title_style
            ))
            elements.append(Paragraph(f"Generated: {meta.get('generated_at', 'Unknown')}", normal_style))
            elements.append(Spacer(1, 12))
            
            elements.append(Paragraph("Executive Summary", heading_style))
            elements.append(Paragraph(f"<b>Current Price:</b> {summary.get('current_price', 'N/A')}", normal_style))
            elements.append(Paragraph(f"<b>Risk Level:</b> {summary.get('risk_level', 'Not assessed')}", normal_style))
            elements.append(Spacer(1, 8))
            
            for metric in summary.get('key_metrics', []):
                elements.append(Paragraph(f"• {metric}", normal_style))
            
            elements.append(Spacer(1, 12))
            
            elements.append(Paragraph("Investment Recommendation", heading_style))
            rec = report.get('investment_recommendation', {})
            elements.append(Paragraph(f"<b>Outlook:</b> {rec.get('outlook', 'N/A')}", normal_style))
            elements.append(Spacer(1, 8))
            
            if rec.get('positives'):
                elements.append(Paragraph("<b>Positives:</b>", normal_style))
                for p in rec.get('positives', []):
                    elements.append(Paragraph(f"• {p}", normal_style))
            
            if rec.get('concerns'):
                elements.append(Paragraph("<b>Concerns:</b>", normal_style))
                for c in rec.get('concerns', []):
                    elements.append(Paragraph(f"• {c}", normal_style))
            
            elements.append(Spacer(1, 16))
            
            elements.append(Paragraph("Company Overview", heading_style))
            overview = report.get('company_overview', {})
            overview_data = [
                ["Field", "Value"],
                ["Ticker", overview.get('ticker', 'N/A')],
                ["Company", overview.get('company_name', 'N/A')],
                ["Sector", overview.get('sector', 'N/A')],
                ["Industry", overview.get('industry', 'N/A')],
                ["Market Cap", f"${overview.get('market_cap', 0):,.0f}" if overview.get('market_cap') else 'N/A'],
            ]
            
            overview_table = Table(overview_data, colWidths=[2*inch, 4*inch])
            overview_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f1f3f4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#333333')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dddddd')),
            ]))
            elements.append(overview_table)
            
            elements.append(Spacer(1, 20))
            
            disclaimer_style = ParagraphStyle(
                'Disclaimer',
                parent=normal_style,
                fontSize=9,
                textColor=HexColor('#666666'),
                borderColor=HexColor('#ffc107'),
                borderWidth=1,
                borderPadding=8,
            )
            elements.append(Paragraph(f"<b>Disclaimer:</b> {report.get('disclaimer', '')}", disclaimer_style))
            
            doc.build(elements)
            
            logger.info(f"PresentationAgent: PDF report saved to {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            return ""
    
    def get_llm_agent(self) -> LlmAgent:
        """Get the underlying LLM agent for use in orchestration."""
        return self.agent


def create_presentation_agent(model: str = "gemini-2.0-flash") -> PresentationAgent:
    """
    Factory function to create a Presentation Agent.
    
    Args:
        model: The Gemini model to use
        
    Returns:
        PresentationAgent: A configured Presentation Agent instance
    """
    return PresentationAgent(model=model)

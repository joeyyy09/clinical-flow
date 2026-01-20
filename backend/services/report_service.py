import io
from sqlalchemy.orm import Session
from services.risk_monitor_service import RiskMonitorService
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
from typing import Dict

class ReportService:
    @staticmethod
    def generate_assessment_report(db: Session, agent) -> io.BytesIO:
        """Orchestrates risk data collection and AI narrative generation for PDF export."""
        risk_data = RiskMonitorService.get_detailed_risk_data(db)
        high_risk = len([r for r in risk_data if r['risk_level'] == 'High'])
        
        try:
            summary_prompt = f"Summarize the risk status for {len(risk_data)} clinical sites. There are {high_risk} high risk sites. The average DQI is {sum(r['dqi'] for r in risk_data)/len(risk_data):.1f}."
            ai_summary = agent.query(summary_prompt).get('answer', '')
        except:
            ai_summary = "AI Summarization unavailable."

        report_context = {
            "study_id": "CT-2024-001",
            "sites": risk_data,
            "site_count": len(risk_data),
            "high_risk_count": high_risk,
            "executive_summary": ai_summary
        }
        
        return ReportService._generate_pdf(report_context)

    @staticmethod
    def _generate_pdf(report_data):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph(f"Clinical Trial Risk Assessment Report", styles['Title']))
        story.append(Spacer(1, 12))

        # Meta Info
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Paragraph(f"Study ID: {report_data.get('study_id', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 24))

        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        summary_text = report_data.get('executive_summary') or "Summary text unavailable."
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 12))

        # Table Data
        if 'sites' in report_data and report_data['sites']:
            story.append(Paragraph("Detailed Site Performance Matrix", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            table_data = [['Site ID', 'Risk Level', 'DQI', 'SAEs', 'Missing', 'Action']]
            for site in report_data['sites']:
                table_data.append([
                    site.get('site', 'N/A'),
                    site.get('risk_level', 'Unknown'),
                    str(site.get('dqi', 'N/A')),
                    str(site.get('sae_count', 0)),
                    str(site.get('missing_pages', 0)),
                    site.get('recommendation', 'Monitor')[:15] + "..."
                ])

            t = Table(table_data, colWidths=[60, 60, 40, 60, 60, 160])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(t)

        doc.build(story)
        buffer.seek(0)
        return buffer

    @staticmethod
    def get_report_list():
        return [
            {"id": 1, "title": "Protocol Deviation Summary - Q3", "date": "2025-10-15", "type": "Compliance", "status": "Ready"},
            {"id": 2, "title": "Safety Signal Detection - Site 404", "date": "2025-11-01", "type": "Safety", "status": "Ready"},
            {"id": 3, "title": "Missing Data Trends - Global", "date": "2025-11-10", "type": "Data Quality", "status": "Processing"}
        ]

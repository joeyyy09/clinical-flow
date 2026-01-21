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
        
        avg_dqi = sum(r['dqi'] for r in risk_data)/max(1, len(risk_data))
        avg_readiness = sum(r.get('milestone_readiness', 0) for r in risk_data)/max(1, len(risk_data))
        
        try:
            summary_prompt = (
                f"Analyze clinical trial risk for {len(risk_data)} sites. "
                f"There are {high_risk} High Risk sites. Average DQI is {avg_dqi:.1f}. "
                f"Average Dataset Readiness is {avg_readiness:.1f}%. "
                "Provide a professional executive summary highlighting critical risks and recommended actions."
            )
            ai_summary = agent.query(summary_prompt).get('answer', '')
        except Exception as e:
            print(f"AI Summary Error: {e}")
            ai_summary = f"Automated Summary: Analyzed {len(risk_data)} sites. {high_risk} sites are High Risk. The overall Dataset Readiness is {avg_readiness:.1f}%, with an average Data Quality Index of {avg_dqi:.1f}."

        report_context = {
            "title": "Clinical Trial Risk & Readiness Report",
            "study_id": "CT-2024-001",
            "sites": risk_data,
            "executive_summary": ai_summary
        }
        
        return ReportService._generate_pdf(report_context)

    @staticmethod
    def generate_performance_report(db: Session, agent) -> io.BytesIO:
        """Generates CRA and Site performance summary using AI."""
        from services.cra_service import CRAService
        
        cra_metrics = CRAService.get_cra_performance_metrics(db)
        site_metrics = RiskMonitorService.get_detailed_risk_data(db)
        
        total_queries = sum(m['pending_queries'] for m in cra_metrics)
        avg_cra_dqi = sum(m['avg_dqi'] for m in cra_metrics) / max(1, len(cra_metrics))
        
        try:
            perf_prompt = (
                f"Generate a performance summary for {len(cra_metrics)} CRAs. "
                f"Total pending queries: {total_queries}. Avg CRA DQI: {avg_cra_dqi:.1f}. "
                f"Include insights on workload distribution and data quality trends across sites."
            )
            ai_summary = agent.query(perf_prompt).get('answer', '')
        except Exception as e:
            print(f"AI Performance Summary Error: {e}")
            ai_summary = f"CRA Performance Summary: Monitoring {len(cra_metrics)} CRAs with {total_queries} total pending queries. Average CRA DQI stands at {avg_cra_dqi:.1f}."

        report_context = {
            "title": "Site & CRA Performance Summary",
            "study_id": "CT-2024-001",
            "cra_data": cra_metrics,
            "sites": site_metrics,
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
        story.append(Paragraph(report_data.get('title', "Clinical Report"), styles['Title']))
        story.append(Spacer(1, 12))

        # Meta Info
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Paragraph(f"Study ID: {report_data.get('study_id', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 24))

        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        summary_text = report_data.get('executive_summary') or "Summary text unavailable."
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 24))

        # CRA Performance Table (if available)
        if 'cra_data' in report_data and report_data['cra_data']:
            story.append(Paragraph("CRA Performance Metrics", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            table_data = [['CRA Name', 'Pending Queries', 'Resolved Queries', 'Avg DQI']]
            for cra in report_data['cra_data']:
                table_data.append([
                    cra.get('cra_name', 'N/A'),
                    str(cra.get('pending_queries', 0)),
                    str(cra.get('resolved_queries', 0)),
                    str(cra.get('avg_dqi', 0))
                ])

            t = Table(table_data, colWidths=[150, 100, 100, 100])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ]))
            story.append(t)
            story.append(Spacer(1, 24))

        # Table Data
        if 'sites' in report_data and report_data['sites']:
            story.append(Paragraph("Detailed Site Performance Matrix", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            table_data = [['Site ID', 'Risk', 'DQI', 'Readiness', 'SAEs', 'Action']]
            for site in report_data['sites']:
                table_data.append([
                    site.get('site', 'N/A'),
                    site.get('risk_level', 'Unknown'),
                    str(site.get('dqi', 'N/A')),
                    f"{site.get('milestone_readiness', 0)}%",
                    str(site.get('sae_count', 0)),
                    site.get('recommendation', 'Monitor')[:15] + "..."
                ])

            t = Table(table_data, colWidths=[80, 80, 60, 80, 60, 120])
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
            {"id": "risk_assessment", "title": "Risk Assessment & Readiness", "date": datetime.now().strftime('%Y-%m-%d'), "type": "Risk", "status": "Ready"},
            {"id": "performance_summary", "title": "CRA & Site Performance Summary", "date": datetime.now().strftime('%Y-%m-%d'), "type": "Performance", "status": "Ready"},
            {"id": "compliance_summary", "title": "Protocol Deviation Summary", "date": datetime.now().strftime('%Y-%m-%d'), "type": "Compliance", "status": "Ready"},
        ]

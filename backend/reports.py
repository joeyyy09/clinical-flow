import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

def generate_pdf_report(report_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = styles['Title']
    story.append(Paragraph(f"Clinical Trial Risk Assessment Report", title_style))
    story.append(Spacer(1, 12))

    # Meta Info
    normal_style = styles['Normal']
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    story.append(Paragraph(f"Study ID: {report_data.get('study_id', 'N/A')}", normal_style))
    story.append(Spacer(1, 24))

    # Executive Summary (AI Generated or Default)
    story.append(Paragraph("Executive Summary", styles['Heading2']))
    
    if report_data.get('executive_summary'):
        summary_text = report_data.get('executive_summary')
    else:
        summary_text = f"""
        This report summarizes the risk profile for {report_data.get('site_count', 0)} clinical sites. 
        High-risk indicators were detected in {report_data.get('high_risk_count', 0)} sites, primarily driven by 
        SAE velocity and missing page cleanup rates.
        """
        
    story.append(Paragraph(summary_text, normal_style))
    story.append(Spacer(1, 12))

    # Table Data (if available)
    if 'sites' in report_data and report_data['sites']:
        story.append(Paragraph("Detailed Site Performance Matrix", styles['Heading2']))
        story.append(Spacer(1, 12))

        # Adjusted column headers for new metrics
        table_data = [['Site ID', 'Risk Level', 'DQI', 'Query Rate', 'Deviations', 'Action']]
        
        for site in report_data['sites']:
            table_data.append([
                site.get('site', 'N/A'),
                site.get('risk_level', 'Unknown'),
                str(site.get('dqi', 'N/A')),
                f"{site.get('query_resolution_rate', 0)}%",
                str(site.get('protocol_deviations', 0)),
                site.get('recommendation', 'Monitor')[:20] + "..." # Truncate for table fit
            ])

        t = Table(table_data, colWidths=[60, 60, 40, 60, 60, 150])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')), # Blue header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(t)

        story.append(Spacer(1, 24))
        story.append(Paragraph("Metrics Definitions:", styles['Heading3']))
        story.append(Paragraph("• DQI: Data Quality Index (0-100)", normal_style))
        story.append(Paragraph("• Query Rate: % of queries resolved within 14 days", normal_style))
        story.append(Paragraph("• Deviations: Count of major protocol deviations", normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

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

    # Executive Summary
    story.append(Paragraph("Executive Summary", styles['Heading2']))
    summary_text = f"""
    This report summarizes the risk profile for {report_data.get('site_count', 0)} clinical sites. 
    High-risk indicators were detected in {report_data.get('high_risk_count', 0)} sites, primarily driven by 
    SAE velocity and missing page cleanup rates.
    """
    story.append(Paragraph(summary_text, normal_style))
    story.append(Spacer(1, 12))

    # Table Data (if available)
    if 'sites' in report_data and report_data['sites']:
        story.append(Paragraph("Site Performance Matrix", styles['Heading2']))
        story.append(Spacer(1, 12))

        table_data = [['Site ID', 'Risk Level', 'SAEs', 'Missing Pages']]
        for site in report_data['sites']:
            table_data.append([
                site.get('site', 'N/A'),
                site.get('risk_level', 'Unknown'),
                str(site.get('sae_count', 0)),
                str(site.get('missing_pages', 0))
            ])

        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(t)

    doc.build(story)
    buffer.seek(0)
    return buffer

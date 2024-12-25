from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepInFrame
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib.utils import ImageReader
from datetime import datetime
import os
from .upload_report import uploads

def create_chart(chart_type, data, width=400, height=200):
    drawing = Drawing(width, height)
    
    if chart_type == "bar":
        chart = VerticalBarChart()
        chart.x = 50
        chart.y = 50
        chart.height = 150
        chart.width = 300
        chart.data = [data['values']]
        chart.categoryAxis.categoryNames = data['labels']
        chart.bars[0].fillColor = colors.Color(0.957, 0.643, 0.765)
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = max(data['values']) * 1.1
        chart.valueAxis.valueStep = max(data['values']) // 5 if max(data['values']) > 0 else 1
        chart.categoryAxis.labels.boxAnchor = 'ne'
        chart.categoryAxis.labels.dx = -8
        chart.categoryAxis.labels.dy = -2
        chart.categoryAxis.labels.angle = 30
        
    elif chart_type == "line":
        chart = HorizontalLineChart()
        chart.x = 50
        chart.y = 50
        chart.height = 150
        chart.width = 300
        chart.data = [data['values']]
        chart.categoryAxis.categoryNames = data['labels']
        chart.lines[0].strokeColor = colors.Color(0.957, 0.643, 0.765)
        chart.lines[0].strokeWidth = 3
        min_val = min(data['values']) if data['values'] else 0
        max_val = max(data['values']) if data['values'] else 1
        chart.valueAxis.valueMin = min_val * 0.9
        chart.valueAxis.valueMax = max_val * 1.1
        chart.valueAxis.valueStep = (max_val - min_val) // 5 if max_val > min_val else 1
        
    elif chart_type == "pie":
        chart = Pie()
        chart.x = 150
        chart.y = 100
        chart.width = 150
        chart.height = 150
        chart.data = data['values']
        chart.labels = [f"{label} ({value:.1f}%)" for label, value in 
                       zip(data['labels'], 
                           [v/sum(data['values'])*100 for v in data['values']])]
        chart.slices.strokeWidth = 0.5
        
    drawing.add(chart)
def create_chart(chart_type, data, width=400, height=200):
    drawing = Drawing(width, height)
    
    if chart_type == "bar":
        chart = VerticalBarChart()
        chart.x = 50
        chart.y = 50
        chart.height = 150
        chart.width = 300
        chart.data = [data['values']]
        chart.categoryAxis.categoryNames = data['labels']
        chart.bars[0].fillColor = colors.Color(0.957, 0.643, 0.765)
        
        # Fix for zero division error
        max_value = max(data['values']) if data['values'] else 1
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = max_value * 1.1
        chart.valueAxis.valueStep = max(1, max_value // 5)  # Ensure step is at least 1
        
        chart.categoryAxis.labels.boxAnchor = 'ne'
        chart.categoryAxis.labels.dx = -8
        chart.categoryAxis.labels.dy = -2
        chart.categoryAxis.labels.angle = 30
        
    elif chart_type == "line":
        chart = HorizontalLineChart()
        chart.x = 50
        chart.y = 50
        chart.height = 150
        chart.width = 300
        chart.data = [data['values']]
        chart.categoryAxis.categoryNames = data['labels']
        chart.lines[0].strokeColor = colors.Color(0.957, 0.643, 0.765)
        chart.lines[0].strokeWidth = 3
        
        # Fix for zero division error
        min_val = min(data['values']) if data['values'] else 0
        max_val = max(data['values']) if data['values'] else 1
        value_range = max_val - min_val
        
        chart.valueAxis.valueMin = min_val - (value_range * 0.1)
        chart.valueAxis.valueMax = max_val + (value_range * 0.1)
        chart.valueAxis.valueStep = max(1, value_range // 5)  # Ensure step is at least 1
        
    elif chart_type == "pie":
        chart = Pie()
        chart.x = 150
        chart.y = 100
        chart.width = 150
        chart.height = 150
        chart.data = data['values']
        
        # Fix for zero division error
        total = sum(data['values']) if data['values'] else 1
        chart.labels = [f"{label} ({value/total*100:.1f}%)" for label, value in 
                       zip(data['labels'], data['values'])]
        chart.slices.strokeWidth = 0.5
        
    drawing.add(chart)
    return drawing

def create_fastcardio_report(report_data, expense_data):
    current_time = datetime.now().strftime("%A, %B %d, %Y _ %H_%M_%S")
    filename = f"FastCardio Management Report _ {current_time}.pdf"
    
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=60,
        bottomMargin=50
    )
    
    # Colors
    pink = colors.Color(0.957, 0.643, 0.765)
    light_pink = colors.Color(0.992, 0.933, 0.945)
    dark_pink = colors.Color(0.722, 0.329, 0.431)
    white = colors.white
    black = colors.black
    gray = colors.Color(0.4, 0.4, 0.4)

    # Create stylesheet and define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    styles.add(ParagraphStyle(
        name='Custom',
        fontSize=10,
        spaceAfter=8,
        spaceBefore=8,
        leading=14,
        textColor=gray,
        parent=styles['Normal']
    ))
    
    styles.add(ParagraphStyle(
        name='MainHeader',
        fontSize=16,
        spaceAfter=10,
        spaceBefore=10,
        alignment=1,
        textColor=dark_pink,
        parent=styles['Normal']
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        fontSize=12,
        spaceAfter=6,
        spaceBefore=6,
        textColor=dark_pink,
        fontName='Helvetica-Bold',
        parent=styles['Normal'],
        borderWidth=1,
        borderColor=pink,
        borderPadding=5
    ))
    
    styles.add(ParagraphStyle(
        name='TOCEntry',
        fontSize=10,
        spaceAfter=4,
        spaceBefore=4,
        textColor=gray,
        parent=styles['Normal']
    ))

    styles.add(ParagraphStyle(
        name='TOCHeader',
        fontSize=14,
        spaceAfter=12,
        spaceBefore=12,
        textColor=dark_pink,
        fontName='Helvetica-Bold',
        parent=styles['Normal'],
    ))

    def add_page_header(canvas, doc):
        canvas.saveState()
        
        # Logo on left
        logo_path = 'logo.jpg'
        if os.path.exists(logo_path):
            logo = ImageReader(logo_path)
            canvas.drawImage(logo, 50, letter[1] - 50, width=80, height=40, preserveAspectRatio=True, mask='auto')
        
        # Title centered
        title = "FastCardio Gym Management Report"
        canvas.setFont('Helvetica-Bold', 14)
        canvas.setFillColor(dark_pink)
        title_width = canvas.stringWidth(title, 'Helvetica-Bold', 14)
        canvas.drawString((letter[0] - title_width) / 2, letter[1] - 35, title)
        
        # Page number right-aligned
        page_num = f"Page {canvas.getPageNumber()}"
        canvas.setFont('Helvetica', 10)
        canvas.setFillColor(gray)
        canvas.drawString(letter[0] - 100, letter[1] - 35, page_num)
        
        # Decorative line
        canvas.setStrokeColor(pink)
        canvas.setLineWidth(2)
        canvas.line(50, letter[1] - 55, letter[0] - 50, letter[1] - 55)
        
        canvas.restoreState()

    elements = []

    # Table of Contents
    if elements:  # Ensure elements list is not empty
        elements.append(Paragraph("Table of Contents", styles['TOCHeader']))
    
    # Generate TOC entries
    toc_entries = []
    section_num = 1
    toc_entries.append(["1. Executive Summary", ""])
    
    for title in report_data.keys():
        section_num += 1
        toc_entries.append([f"{section_num}. {title}", ""])
        
        # Add subsections based on data type
        if report_data[title].get('chart_type') == 'pie':
            toc_entries.append([f"   • Distribution Analysis", ""])
            toc_entries.append([f"   • Category Breakdown", ""])
        else:
            toc_entries.append([f"   • Current Metrics", ""])
            toc_entries.append([f"   • Historical Trends", ""])
            toc_entries.append([f"   • Analysis", ""])

    if toc_entries:  # Check if we have TOC entries
        toc_table = Table(toc_entries, colWidths=[5*inch, 0.5*inch])
        toc_table.setStyle(TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, -1), gray),
            ('FONT', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
        ]))
        elements.append(toc_table)
        elements.append(PageBreak())

    # Executive Summary
    if report_data:  # Ensure we have data to process
        # Calculate key metrics safely
        total_revenue = sum(report_data.get('Total Revenue', {}).get('chart_data', {}).get('values', [0]))
        total_members = report_data.get('All Members', {}).get('current', 0)
        active_members = report_data.get('Active Members', {}).get('current', 0)
        engagement_rate = (active_members / total_members * 100) if total_members > 0 else 0
        
        elements.append(Paragraph("Executive Summary", styles['SectionHeader']))
        
        executive_summary = f"""
        FastCardio Gym demonstrates strong performance across key metrics. The facility currently serves {total_members} 
        members with an engagement rate of {engagement_rate:.1f}%. Total revenue stands at ${total_revenue:,.2f} with 
        diverse revenue streams across multiple subscription types. Member activity and retention rates show positive 
        trends, while operational expenses remain well-managed across all categories.
        """
        
        elements.append(Paragraph(executive_summary.strip(), styles['Custom']))
        elements.append(Spacer(1, 10))

    # Generate sections with charts
    for title, section_data in report_data.items():
        if not isinstance(section_data, dict):  # Skip if section_data is not a dictionary
            continue
            
        elements.append(PageBreak())
        elements.append(Paragraph(title, styles['SectionHeader']))
        
        # Current value display
        current_value = section_data.get("current", "N/A")
        table_data = [[
            Paragraph("Current Value", styles['TOCEntry']), 
            Paragraph(str(current_value), styles['Custom'])
        ]]
        
        metric_table = Table(table_data, colWidths=[1.5*inch, 4*inch])
        metric_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), pink),
            ('BACKGROUND', (1, 0), (-1, -1), light_pink),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, white),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(metric_table)
        elements.append(Spacer(1, 8))
        
        # Description
        if section_data.get("description"):
            elements.append(Paragraph(section_data["description"], styles['Custom']))
            elements.append(Spacer(1, 8))
        
        # Add chart if data exists
        chart_data = section_data.get("chart_data")
        if chart_data and section_data.get("chart_type"):
            try:
                chart = create_chart(
                    section_data["chart_type"],
                    chart_data
                )
                if chart:  # Only add chart if creation was successful
                    elements.append(KeepInFrame(400, 220, [chart], mode='shrink', hAlign='CENTER'))
                    elements.append(Spacer(1, 8))
                
                    # Add chart description based on type
                    if section_data["chart_type"] == "line":
                        labels = chart_data.get('labels', [])
                        if labels:
                            trend_description = f"The graph shows the historical trend over the past {len(labels)} months."
                            elements.append(Paragraph(trend_description, styles['Custom']))
                    elif section_data["chart_type"] == "pie":
                        values = chart_data.get('values', [])
                        labels = chart_data.get('labels', [])
                        if values and labels:
                            total = sum(values)
                            if total > 0:
                                percentages = [f"{label}: {(value/total)*100:.1f}%" 
                                            for label, value in zip(labels, values)]
                                distribution = f"Distribution breakdown: {', '.join(percentages)}"
                                elements.append(Paragraph(distribution, styles['Custom']))
            except Exception as e:
                print(f"Error creating chart for {title}: {str(e)}")
                # Add a placeholder or error message if chart creation fails
                elements.append(Paragraph(f"Chart data visualization unavailable", styles['Custom']))

    # Only build if we have elements
    if elements:
        doc.build(elements, onFirstPage=add_page_header, onLaterPages=add_page_header)
        return uploads(filename)
    else:
        raise ValueError("No content available to generate report")
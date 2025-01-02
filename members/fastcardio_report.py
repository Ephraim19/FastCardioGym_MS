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
    """
    Creates a chart based on the specified type and data.
    
    Args:
        chart_type (str): Type of chart ('bar', 'line', or 'pie')
        data (dict): Chart data containing 'labels' and 'values'
        width (int): Chart width in pixels
        height (int): Chart height in pixels
    
    Returns:
        Drawing: ReportLab drawing object containing the chart
    """
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
        
        max_value = max(data['values']) if data['values'] else 1
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = max_value * 1.1
        chart.valueAxis.valueStep = max(1, max_value // 5)
        
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
        value_range = max_val - min_val
        
        chart.valueAxis.valueMin = min_val - (value_range * 0.1)
        chart.valueAxis.valueMax = max_val + (value_range * 0.1)
        chart.valueAxis.valueStep = max(1, value_range // 5)
        
    elif chart_type == "pie":
        chart = Pie()
        chart.x = 150
        chart.y = 100
        chart.width = 150
        chart.height = 150
        chart.data = data['values']
        
        total = sum(data['values']) if data['values'] else 1
        chart.labels = [f"{label} ({value/total*100:.1f}%)" for label, value in 
                       zip(data['labels'], data['values'])]
        chart.slices.strokeWidth = 0.5
        
    drawing.add(chart)
    return drawing

def create_fastcardio_report(report_data, start_date=None, end_date=None):
    """
    Creates a comprehensive PDF report for FastCardio gym management.
    
    Args:
        report_data (dict): Nested dictionary containing all report sections and metrics
        start_date (str, optional): Start date for the report period
        end_date (str, optional): End date for the report period
    
    Returns:
        dict: Contains the Firebase URL of the uploaded report
    """
    # Extract key metrics from the nested structure
    membership_data = report_data["Membership Overview"]
    attendance_data = report_data["Attendance Analytics"]
    demographics_data = report_data["Member Demographics"]
    financial_data = report_data["Financial Analysis"]
    subscription_data = report_data["Subscription Plans"]

    # Format date range for display
    date_range = "All Time"
    if start_date and end_date:
        date_range = f"{start_date} to {end_date}"
    
    current_time = datetime.now().strftime("%A, %B %d, %Y _ %H_%M_%S")
    filename = f"FastCardio Management Report _ {current_time}.pdf"
    
    # Document setup
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=60,
        bottomMargin=50
    )
    
    # Define colors
    pink = colors.Color(0.957, 0.643, 0.765)
    light_pink = colors.Color(0.992, 0.933, 0.945)
    dark_pink = colors.Color(0.722, 0.329, 0.431)
    white = colors.white
    black = colors.black
    gray = colors.Color(0.4, 0.4, 0.4)

    # Get base styles
    styles = getSampleStyleSheet()
    
    # Define custom styles
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
        name='DateRange',
        fontSize=9,
        textColor=gray,
        parent=styles['Normal'],
        alignment=1,
        spaceBefore=2,
        spaceAfter=8
    ))

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
        name='MetricLabel',
        fontSize=9,
        textColor=white,
        parent=styles['Normal'],
        alignment=1
    ))
    
    styles.add(ParagraphStyle(
        name='MetricValue',
        fontSize=10,
        textColor=gray,
        parent=styles['Normal'],
        alignment=1
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

    def add_page_header(canvas, doc):
        """Adds consistent header to each page of the report."""
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
        
        # Date range in header
        date_text = f"Report Period: {date_range}"
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(gray)
        canvas.drawString(50, letter[1] - 70, date_text)
        
        # Decorative line
        canvas.setStrokeColor(pink)
        canvas.setLineWidth(2)
        canvas.line(50, letter[1] - 55, letter[0] - 50, letter[1] - 55)
        
        canvas.restoreState()

    elements = []

    # Executive Summary
    elements.append(Paragraph("Executive Summary", styles['SectionHeader']))
    elements.append(Paragraph(date_range, styles['DateRange']))
    
    executive_summary = f"""
    FastCardio Gym demonstrates strong performance across key metrics for the period {date_range}. 
    The facility currently serves {membership_data['current']} members with an engagement rate 
    of {membership_data['metrics']['Active Members']}. Total revenue stands at ${financial_data['current']:,.2f} 
    with diverse revenue streams across multiple subscription types. Member activity shows 
    a {attendance_data['metrics']['Retention Rate']} retention rate, with an average of {attendance_data['current']} 
    daily check-ins. The gym maintains a healthy gender distribution with {demographics_data['chart_data']['values'][0]}% male 
    and {demographics_data['chart_data']['values'][1]}% female members.
    """
    
    elements.append(Paragraph(executive_summary.strip(), styles['Custom']))
    elements.append(PageBreak())

    # Define sections with their metrics and charts
    sections = {
        "Member Demographics": {
            "metrics": {
                "Total Members": demographics_data['current'],
                "Active Members": membership_data['metrics']['Active Members'],
                "Male/Female Ratio": f"{demographics_data['chart_data']['values'][0]}% / {demographics_data['chart_data']['values'][1]}%",
                "New Members": membership_data['metrics']['New Members This Month']
            },
            "chart_data": {
                "type": "pie",
                "data": demographics_data['chart_data']
            }
        },
        "Attendance Analytics": {
            "metrics": {
                "Daily Check-ins": attendance_data['current'],
                "Peak Hours": attendance_data['metrics']['Peak Hours'],
                "Busiest Day": attendance_data['metrics']['Busiest Day'],
                "Retention Rate": attendance_data['metrics']['Retention Rate']
            },
            "chart_data": {
                "type": "bar",
                "data": attendance_data['chart_data']
            }
        },
        "Progress Tracking": {
            "metrics": {
                "Avg Weight": demographics_data['metrics']['Average Weight'],
                "Avg Body Fat": demographics_data['metrics']['Average Body Fat'],
                "Avg Muscle Mass": demographics_data['metrics']['Average Muscle Mass'],
                "Members with Progress": demographics_data['metrics']['Members with Weight Loss']
            }
        },
        "Financial Overview": {
            "metrics": {
                "Total Revenue": f"${financial_data['current']:,.2f}",
                "Avg Payment": financial_data['metrics']['Average Payment'],
                "Total Credit": financial_data['metrics']['Total Member Credit'],
                "Total Debt": financial_data['metrics']['Total Member Debt']
            },
            "chart_data": {
                "type": "bar",
                "data": financial_data['chart_data']
            }
        }
    }

    # Generate section content
    for title, section_data in sections.items():
        elements.append(Paragraph(title, styles['SectionHeader']))
        
        # Add metrics table
        if 'metrics' in section_data:
            metric_rows = []
            for label, value in section_data['metrics'].items():
                metric_rows.append([
                    Paragraph(label, styles['MetricLabel']),
                    Paragraph(str(value), styles['MetricValue'])
                ])
            
            metrics_table = Table(metric_rows, colWidths=[2*inch, 3*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), pink),
                ('BACKGROUND', (1, 0), (1, -1), light_pink),
                ('GRID', (0, 0), (-1, -1), 1, white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(metrics_table)
            elements.append(Spacer(1, 10))
        
        # Add chart if available
        if 'chart_data' in section_data:
            try:
                chart = create_chart(
                    section_data['chart_data']['type'],
                    section_data['chart_data']['data']
                )
                if chart:
                    elements.append(KeepInFrame(400, 220, [chart], mode='shrink', hAlign='CENTER'))
                    elements.append(Spacer(1, 15))
            except Exception as e:
                print(f"Error creating chart for {title}: {str(e)}")
                elements.append(Paragraph(f"Chart data visualization unavailable", styles['Custom']))
        
        elements.append(PageBreak())

    # Build the document
    doc.build(elements, onFirstPage=add_page_header, onLaterPages=add_page_header)
    
    # Upload and return the report URL
    return uploads(filename)
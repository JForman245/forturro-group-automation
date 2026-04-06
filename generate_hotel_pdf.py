#!/usr/bin/env python3
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

output_path = "/Users/claw1/.openclaw/workspace/Hotel_Property_Overview.pdf"

doc = SimpleDocTemplate(
    output_path,
    pagesize=letter,
    rightMargin=0.75*inch,
    leftMargin=0.75*inch,
    topMargin=0.75*inch,
    bottomMargin=0.75*inch
)

# Colors
navy = HexColor("#1B2A4A")
gold = HexColor("#C5A55A")
teal = HexColor("#2A7B88")
dark_gray = HexColor("#333333")
light_gray = HexColor("#F5F5F5")
white = HexColor("#FFFFFF")

styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Title'],
    fontSize=26,
    textColor=navy,
    spaceAfter=4,
    fontName='Helvetica-Bold',
    alignment=TA_CENTER,
)

subtitle_style = ParagraphStyle(
    'Subtitle',
    parent=styles['Normal'],
    fontSize=13,
    textColor=teal,
    spaceAfter=20,
    fontName='Helvetica',
    alignment=TA_CENTER,
)

section_style = ParagraphStyle(
    'SectionHeader',
    parent=styles['Heading2'],
    fontSize=14,
    textColor=navy,
    spaceBefore=16,
    spaceAfter=8,
    fontName='Helvetica-Bold',
    borderPadding=(0, 0, 2, 0),
)

body_style = ParagraphStyle(
    'CustomBody',
    parent=styles['Normal'],
    fontSize=10.5,
    textColor=dark_gray,
    leading=15,
    fontName='Helvetica',
    spaceAfter=6,
)

bullet_style = ParagraphStyle(
    'Bullet',
    parent=body_style,
    leftIndent=20,
    bulletIndent=8,
    spaceAfter=4,
)

table_header_style = ParagraphStyle(
    'TableHeader',
    parent=styles['Normal'],
    fontSize=10,
    textColor=white,
    fontName='Helvetica-Bold',
    alignment=TA_LEFT,
)

table_cell_style = ParagraphStyle(
    'TableCell',
    parent=styles['Normal'],
    fontSize=10,
    textColor=dark_gray,
    fontName='Helvetica',
)

table_cell_right = ParagraphStyle(
    'TableCellRight',
    parent=table_cell_style,
    alignment=TA_RIGHT,
)

footer_style = ParagraphStyle(
    'Footer',
    parent=styles['Normal'],
    fontSize=8,
    textColor=HexColor("#999999"),
    alignment=TA_CENTER,
    spaceBefore=30,
)

elements = []

# Header
elements.append(Spacer(1, 0.3*inch))
elements.append(Paragraph("OCEANFRONT HOTEL PROPERTY", title_style))
elements.append(Paragraph("Myrtle Beach, South Carolina", subtitle_style))
elements.append(HRFlowable(width="100%", thickness=2, color=gold, spaceAfter=20))

# Property Overview
elements.append(Paragraph("PROPERTY OVERVIEW", section_style))
elements.append(HRFlowable(width="100%", thickness=0.5, color=teal, spaceAfter=10))

overview_data = [
    [Paragraph("<b>Total Rooms</b>", table_cell_style), Paragraph("51 guest rooms + 3 staff accommodations", table_cell_style)],
    [Paragraph("<b>Additional Units</b>", table_cell_style), Paragraph("Third-floor space (4–5 apartments, revenue-generating)", table_cell_style)],
    [Paragraph("<b>Buildings</b>", table_cell_style), Paragraph("Two buildings — Oceanfront &amp; Side-View", table_cell_style)],
    [Paragraph("<b>Location</b>", table_cell_style), Paragraph("Myrtle Beach, SC — Oceanfront", table_cell_style)],
]

overview_table = Table(overview_data, colWidths=[2*inch, 4.5*inch])
overview_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (0, -1), light_gray),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#DDDDDD")),
]))
elements.append(overview_table)

# Building Layout
elements.append(Spacer(1, 0.15*inch))
elements.append(Paragraph("BUILDING LAYOUT", section_style))
elements.append(HRFlowable(width="100%", thickness=0.5, color=teal, spaceAfter=10))

elements.append(Paragraph("<b>Oceanfront Building:</b> 6 floors × 4 rooms per floor = 24 rooms", body_style))
elements.append(Paragraph("<b>Side-View Building:</b> 3 floors with guest rooms on floors 1–2. The third floor features a large apartment configurable as 4–5 units, suitable for extended-stay or long-term rental income.", body_style))

# Renovations & Capital Improvements
elements.append(Spacer(1, 0.15*inch))
elements.append(Paragraph("RENOVATIONS &amp; CAPITAL IMPROVEMENTS", section_style))
elements.append(HRFlowable(width="100%", thickness=0.5, color=teal, spaceAfter=10))

reno_data = [
    [Paragraph("<b>Year</b>", ParagraphStyle('th', parent=table_header_style, alignment=TA_CENTER)), 
     Paragraph("<b>Improvement</b>", table_header_style)],
    [Paragraph("2022", ParagraphStyle('tc', parent=table_cell_style, alignment=TA_CENTER)), 
     Paragraph("Side-view building roof replaced; main drain checked &amp; maintained", table_cell_style)],
    [Paragraph("2023", ParagraphStyle('tc', parent=table_cell_style, alignment=TA_CENTER)), 
     Paragraph("Full furniture renovation across all rooms", table_cell_style)],
    [Paragraph("2023–2025", ParagraphStyle('tc', parent=table_cell_style, alignment=TA_CENTER)), 
     Paragraph("All bathrooms in side-view building fully renovated — walk-in showers replacing bathtubs; partial shower updates in oceanfront building", table_cell_style)],
    [Paragraph("2025", ParagraphStyle('tc', parent=table_cell_style, alignment=TA_CENTER)), 
     Paragraph("Natural gas line across parking lot inspected &amp; partially replaced", table_cell_style)],
    [Paragraph("2025", ParagraphStyle('tc', parent=table_cell_style, alignment=TA_CENTER)), 
     Paragraph("All sprinkler heads replaced in oceanfront building", table_cell_style)],
    [Paragraph("2025", ParagraphStyle('tc', parent=table_cell_style, alignment=TA_CENTER)), 
     Paragraph("Elevator — key electronic component replaced; in excellent working condition", table_cell_style)],
]

reno_table = Table(reno_data, colWidths=[1.1*inch, 5.4*inch])
reno_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), navy),
    ('TEXTCOLOR', (0, 0), (-1, 0), white),
    ('BACKGROUND', (0, 1), (-1, 1), light_gray),
    ('BACKGROUND', (0, 3), (-1, 3), light_gray),
    ('BACKGROUND', (0, 5), (-1, 5), light_gray),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#DDDDDD")),
]))
elements.append(reno_table)

# Facilities & Amenities
elements.append(Spacer(1, 0.15*inch))
elements.append(Paragraph("FACILITIES &amp; AMENITIES", section_style))
elements.append(HRFlowable(width="100%", thickness=0.5, color=teal, spaceAfter=10))

elements.append(Paragraph("• Outdoor swimming pool", bullet_style))
elements.append(Paragraph("• Indoor heated swimming pool", bullet_style))
elements.append(Paragraph("• Jacuzzi / hot tub", bullet_style))
elements.append(Paragraph("• Kiddie pool", bullet_style))
elements.append(Paragraph("• On-site laundry room (2 washers, 2 dryers)", bullet_style))
elements.append(Paragraph("• Elevator — regularly inspected, excellent condition", bullet_style))

# Safety Systems
elements.append(Spacer(1, 0.15*inch))
elements.append(Paragraph("SAFETY &amp; FIRE PROTECTION", section_style))
elements.append(HRFlowable(width="100%", thickness=0.5, color=teal, spaceAfter=10))

elements.append(Paragraph("• All sprinkler heads in oceanfront building replaced (2025)", bullet_style))
elements.append(Paragraph("• Fire alarm system monitored by third-party service — fully operational", bullet_style))

# Financial Overview
elements.append(Spacer(1, 0.15*inch))
elements.append(Paragraph("FINANCIAL OVERVIEW", section_style))
elements.append(HRFlowable(width="100%", thickness=0.5, color=teal, spaceAfter=10))

elements.append(Paragraph("<b>Revenue</b>", body_style))

rev_data = [
    [Paragraph("<b>Period</b>", ParagraphStyle('th', parent=table_header_style, alignment=TA_CENTER)),
     Paragraph("<b>Gross Revenue</b>", ParagraphStyle('th', parent=table_header_style, alignment=TA_RIGHT)),
     Paragraph("<b>Notes</b>", table_header_style)],
    [Paragraph("2024 (Apr–Dec)", ParagraphStyle('tc', parent=table_cell_style, alignment=TA_CENTER)),
     Paragraph("~$789,000", table_cell_right),
     Paragraph("Partial year (9 months)", table_cell_style)],
    [Paragraph("2025 (Full Year)", ParagraphStyle('tc', parent=table_cell_style, alignment=TA_CENTER)),
     Paragraph("$793,000", table_cell_right),
     Paragraph("Full year operations", table_cell_style)],
    [Paragraph("Stabilized Estimate", ParagraphStyle('tc', parent=table_cell_style, alignment=TA_CENTER)),
     Paragraph("$1.0M – $1.2M", table_cell_right),
     Paragraph("Good season performance target", table_cell_style)],
    [Paragraph("Apartment Upside", ParagraphStyle('tc', parent=table_cell_style, alignment=TA_CENTER)),
     Paragraph("+~$100,000", table_cell_right),
     Paragraph("Third-floor apartments (not yet included in figures)", table_cell_style)],
]

rev_table = Table(rev_data, colWidths=[1.5*inch, 1.5*inch, 3.5*inch])
rev_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), navy),
    ('TEXTCOLOR', (0, 0), (-1, 0), white),
    ('BACKGROUND', (0, 1), (-1, 1), light_gray),
    ('BACKGROUND', (0, 3), (-1, 3), light_gray),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#DDDDDD")),
]))
elements.append(rev_table)

# Operating Expenses
elements.append(Spacer(1, 0.15*inch))
elements.append(Paragraph("<b>Operating Expenses (2025)</b>", body_style))

exp_data = [
    [Paragraph("<b>Expense Category</b>", table_header_style),
     Paragraph("<b>Annual Cost</b>", ParagraphStyle('th', parent=table_header_style, alignment=TA_RIGHT))],
    [Paragraph("Power / Electric", table_cell_style), Paragraph("$44,800", table_cell_right)],
    [Paragraph("Natural Gas", table_cell_style), Paragraph("$8,900", table_cell_right)],
    [Paragraph("Water", table_cell_style), Paragraph("$9,700", table_cell_right)],
    [Paragraph("Front Desk &amp; Housekeeping Staff", table_cell_style), Paragraph("$88,000", table_cell_right)],
    [Paragraph("Spectrum (Internet, TV, Phones)", table_cell_style), Paragraph("$17,000", table_cell_right)],
    [Paragraph("Property Tax", table_cell_style), Paragraph("$48,169", table_cell_right)],
    [Paragraph("Insurance", table_cell_style), Paragraph("$53,000", table_cell_right)],
    [Paragraph("<b>Subtotal (Listed Expenses)</b>", ParagraphStyle('b', parent=table_cell_style, fontName='Helvetica-Bold')), 
     Paragraph("<b>$269,569</b>", ParagraphStyle('br', parent=table_cell_right, fontName='Helvetica-Bold'))],
    [Paragraph("Miscellaneous &amp; Other Operating Expenses", table_cell_style), Paragraph("TBD", table_cell_right)],
]

exp_table = Table(exp_data, colWidths=[4.5*inch, 2*inch])
exp_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), navy),
    ('TEXTCOLOR', (0, 0), (-1, 0), white),
    ('BACKGROUND', (0, 1), (-1, 1), light_gray),
    ('BACKGROUND', (0, 3), (-1, 3), light_gray),
    ('BACKGROUND', (0, 5), (-1, 5), light_gray),
    ('BACKGROUND', (0, 7), (-1, 7), light_gray),
    ('BACKGROUND', (0, 8), (-1, 8), HexColor("#E8E8E8")),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#DDDDDD")),
    ('LINEABOVE', (0, 8), (-1, 8), 1.5, navy),
]))
elements.append(exp_table)

# NOI note
elements.append(Spacer(1, 0.1*inch))
elements.append(Paragraph("<i>Note: Based on 2025 revenue of $793,000 and listed expenses of $269,569, the estimated NOI before miscellaneous expenses is approximately $523,431. With stabilized revenue of $1.0M–$1.2M and apartment income of ~$100K, total potential gross revenue reaches $1.1M–$1.3M.</i>", 
    ParagraphStyle('note', parent=body_style, fontSize=9.5, textColor=HexColor("#666666"))))

# Footer
elements.append(Spacer(1, 0.3*inch))
elements.append(HRFlowable(width="100%", thickness=1, color=gold, spaceAfter=8))
elements.append(Paragraph("CONFIDENTIAL — Prepared for prospective buyers. All figures are approximate and subject to verification.", footer_style))
elements.append(Paragraph("The Forturro Group | Jeff Forman | jeff@forturro.com | (843) 902-4325", footer_style))

doc.build(elements)
print(f"PDF generated: {output_path}")

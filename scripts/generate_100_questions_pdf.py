"""
Script to generate a comprehensive, publication-grade PDF containing
100 Technical Viva & Project Exhibition Questions and Answers for GEOSEG.
"""

import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

PDF_OUTPUT_PATH = "GEOSEG_100_Viva_Questions_Project_Exhibition.pdf"

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "GEOSEG: Master Project Exhibition Viva & Defense Guide")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 747, 558, 747)

        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, page_text)
        self.drawString(54, 36, "Confidential - Project Exhibition Viva Voce Compendium (100 Questions)")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 46, 558, 46)
        self.restoreState()


# Load the 100 questions and answers data
from questions_data import QUESTIONS_DATA

def build_pdf():
    doc = SimpleDocTemplate(
        PDF_OUTPUT_PATH,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#0284c7"),
        spaceAfter=14
    )

    domain_heading_style = ParagraphStyle(
        'DomainHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    q_style = ParagraphStyle(
        'QStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12.5,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=5,
        spaceAfter=3,
        keepWithNext=True
    )

    a_style = ParagraphStyle(
        'AStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6
    )

    story = []

    # Title & Metadata Card
    story.append(Paragraph("🛰️ GEOSEG: 100 VIVA & DEFENSE QUESTIONS", title_style))
    story.append(Paragraph("Master Technical Knowledge Assessment Guide for Project Exhibition & Oral Examination", subtitle_style))
    
    meta_text = (
        "<b>Project Focus:</b> Progressive Satellite Super-Resolution (2x-8x) & Multispectral Land Cover Segmentation<br/>"
        "<b>Architectures Covered:</b> PSISRNet (Sharma et al. 2025), ColNet (IEEE TGRS), UNetFormer (ISPRS 2022), FarSeg (TPAMI)<br/>"
        "<b>Hardware & Stack:</b> NVIDIA GeForce RTX 5050 (8GB VRAM) • PyTorch 2.11 (CUDA 12.8, FP16 AMP) • C++17 Engine • FastAPI"
    )
    meta_table = Table([[Paragraph(meta_text, a_style)]], colWidths=[504])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Process all 10 domains and 100 questions
    current_domain = None
    for item in QUESTIONS_DATA:
        if item.get("domain") != current_domain:
            current_domain = item["domain"]
            story.append(Spacer(1, 8))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=6, spaceBefore=8))
            story.append(Paragraph(f"<b>{current_domain}</b>", domain_heading_style))
        
        q_num = item["num"]
        q_text = item["question"]
        a_text = item["answer"]

        q_p = Paragraph(f"<b>Q{q_num}: {q_text}</b>", q_style)
        a_p = Paragraph(f"<b>Answer:</b> {a_text}", a_style)
        
        # Enclose in a subtle box or keep together
        item_table = Table([[q_p], [a_p]], colWidths=[504])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#ffffff")),
            ('LINEBELOW', (0,-1), (-1,-1), 0.5, colors.HexColor("#f1f5f9")),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,-1), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(item_table)
        story.append(Spacer(1, 3))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] PDF generated at: {os.path.abspath(PDF_OUTPUT_PATH)}")
    print(f"File size: {os.path.getsize(PDF_OUTPUT_PATH):,} bytes")

if __name__ == '__main__':
    build_pdf()

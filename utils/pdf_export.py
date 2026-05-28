import os
import time
from typing import Dict, Any, List

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class NumberedCanvas(canvas.Canvas):
    """Custom canvas to compute total page count and add a beautiful modern footer."""
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        
        # Draw top accent glowing bar
        self.setStrokeColor(colors.HexColor("#8a2be2")) # Purple
        self.setLineWidth(3)
        self.line(0.5 * inch, 10.5 * inch, 8.0 * inch, 10.5 * inch)

        # Draw bottom footer line
        self.setStrokeColor(colors.HexColor("#1c203b"))
        self.setLineWidth(1)
        self.line(0.5 * inch, 0.75 * inch, 8.0 * inch, 0.75 * inch)

        # Footer Text
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        self.drawString(0.5 * inch, 0.55 * inch, "StartupForge-AI | Virtual Agent Accelerator")
        
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.0 * inch, 0.55 * inch, page_str)
        self.restoreState()


class ForgePDFExporter:
    """Compiles StartupForge-AI reports into styled, executive PDFs."""

    @staticmethod
    def is_available() -> bool:
        return REPORTLAB_AVAILABLE

    @staticmethod
    def generate_report_pdf(report: Dict[str, Any], output_path: str) -> bool:
        if not REPORTLAB_AVAILABLE:
            print("ReportLab is not installed. PDF generation aborted.")
            return False

        try:
            # 1. Setup Document Template
            # Letter size: 8.5 x 11 inches. Margins: 0.5 inches all around.
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                leftMargin=0.5 * inch,
                rightMargin=0.5 * inch,
                topMargin=0.75 * inch,
                bottomMargin=0.9 * inch
            )

            story = []
            styles = getSampleStyleSheet()

            # 2. Define Custom Styles (Modern typography)
            primary_color = colors.HexColor("#0f111f")  # Deep blue/gray
            accent_purple = colors.HexColor("#8a2be2")  # Deep purple
            accent_cyan = colors.HexColor("#00f2fe")    # Neon Cyan
            accent_gold = colors.HexColor("#ffb000")    # Amber
            text_dark = colors.HexColor("#1e293b")      # Slate 800
            text_muted = colors.HexColor("#64748b")     # Slate 500

            title_style = ParagraphStyle(
                'DocTitle',
                parent=styles['Heading1'],
                fontName='Helvetica-Bold',
                fontSize=24,
                leading=28,
                textColor=primary_color,
                spaceAfter=4
            )

            meta_style = ParagraphStyle(
                'DocMeta',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=9,
                leading=12,
                textColor=text_muted,
                spaceAfter=15
            )

            h2_style = ParagraphStyle(
                'SectionHeading',
                parent=styles['Heading2'],
                fontName='Helvetica-Bold',
                fontSize=14,
                leading=18,
                textColor=accent_purple,
                spaceBefore=12,
                spaceAfter=10,
                keepWithNext=True
            )

            body_style = ParagraphStyle(
                'BodyText',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=10,
                leading=14,
                textColor=text_dark,
                spaceAfter=8
            )

            # Speaker Roles styles
            role_badge_styles = {
                "CEO": colors.HexColor("#ff5f00"),      # Orange
                "CTO": colors.HexColor("#00b0ff"),      # Blue
                "PM": colors.HexColor("#9b51e0"),       # Purple
                "Developer": colors.HexColor("#00e676"),# Green
                "Marketer": colors.HexColor("#ff1744"), # Red
                "General": colors.HexColor("#718096")
            }

            # 3. Add Document Header
            story.append(Paragraph(report.get("title", "Untitled Forge Report"), title_style))
            
            created_at = report.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))
            meta_text = (
                f"<b>TYPE:</b> {report.get('type', 'General').upper()} &nbsp;|&nbsp; "
                f"<b>SIMULATION TIMELINE:</b> Operational Day {report.get('day', 1)} &nbsp;|&nbsp; "
                f"<b>COMPILED AT:</b> {created_at}"
            )
            story.append(Paragraph(meta_text, meta_style))
            
            # Subtle divider
            divider = Table([[""]], colWidths=[7.5 * inch])
            divider.setStyle(TableStyle([
                ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor("#e2e8f0")),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(divider)
            story.append(Spacer(1, 15))

            # 4. Add Content
            content = report.get("content", "")

            if isinstance(content, list):
                # We have a conversation list! Loop through messages and lay them out elegantly.
                story.append(Paragraph("💬 Virtual Board Meeting Transcript", h2_style))
                story.append(Spacer(1, 5))

                for i, msg in enumerate(content):
                    sender = msg.get("sender", "Agent")
                    role = msg.get("role", "Co-Founder")
                    text = msg.get("message", "")
                    
                    # Highlight colors based on role
                    border_color = role_badge_styles.get(role, role_badge_styles["General"])

                    # Create standard speaker row
                    speaker_header = f"<b>{sender}</b> <font color='{border_color.hexval()}'>[{role.upper()}]</font>"
                    
                    speaker_header_p = Paragraph(speaker_header, ParagraphStyle(
                        'SpeakerHead', parent=styles['Normal'],
                        fontName='Helvetica-Bold', fontSize=10, leading=12, textColor=primary_color
                    ))
                    
                    msg_p = Paragraph(text, ParagraphStyle(
                        'SpeakerMsg', parent=styles['Normal'],
                        fontName='Helvetica', fontSize=9.5, leading=13.5, textColor=text_dark
                    ))

                    # Place into a stylized single-column block table with a colored left-border
                    bubble_table = Table([[speaker_header_p], [msg_p]], colWidths=[7.3 * inch])
                    bubble_table.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
                        ('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('LEFTPADDING', (0,0), (-1,-1), 12),
                        ('RIGHTPADDING', (0,0), (-1,-1), 12),
                        ('TOPPADDING', (0,0), (-1,-1), 8),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                        ('LINELEFT', (0,0), (0,-1), 4, border_color),
                        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                    ]))

                    story.append(KeepTogether([bubble_table, Spacer(1, 10)]))
            else:
                # Text-based layout (roadmaps, branding guides, etc.)
                # Split content into paragraphs or headers to preserve layout formatting
                paragraphs = str(content).split("\n")
                
                in_list = False
                list_items = []

                for line in paragraphs:
                    line = line.strip()
                    if not line:
                        if in_list:
                            # Render list before blank space
                            story.append(Spacer(1, 5))
                            in_list = False
                        story.append(Spacer(1, 6))
                        continue

                    # Handle headings (e.g., #, ##, ### or bold headings)
                    if line.startswith("#"):
                        # Count the number of hashes
                        hash_count = len(line) - len(line.lstrip('#'))
                        clean_text = line.lstrip('#').strip()
                        
                        heading_size = 14 if hash_count <= 2 else 11
                        heading_color = accent_purple if hash_count <= 2 else primary_color

                        story.append(Paragraph(clean_text, ParagraphStyle(
                            f'SubHead_{hash_count}', parent=styles['Heading3'],
                            fontName='Helvetica-Bold', fontSize=heading_size, leading=heading_size+4,
                            textColor=heading_color, spaceBefore=8, spaceAfter=6, keepWithNext=True
                        )))
                    elif line.startswith("-") or line.startswith("*") or (len(line) > 2 and line[0].isdigit() and line[1] == '.'):
                        # List item
                        clean_text = line.lstrip('-*').strip()
                        if line[0].isdigit():
                            clean_text = line.split('.', 1)[1].strip()
                            bullet = f"{line.split('.', 1)[0]}."
                        else:
                            bullet = "&bull;"

                        list_item_p = Paragraph(f"{bullet} {clean_text}", ParagraphStyle(
                            'ListItem', parent=body_style,
                            leftIndent=15, firstLineIndent=-10, spaceAfter=4
                        ))
                        story.append(list_item_p)
                    else:
                        # Standard paragraph
                        story.append(Paragraph(line, body_style))

            # 5. Build Document
            doc.build(story, canvasmaker=NumberedCanvas)
            return True

        except Exception as e:
            print(f"Error compiling PDF: {e}")
            import traceback
            traceback.print_exc()
            return False

import math
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas


class CertificateData:
    def __init__(
        self,
        recipient_name: str,
        recipient_email: str,
        event_name: str,
        issue_date: str,
        issuer_name: str,
        issuer_title: str,
        organization: str,
        certificate_code: str,
        recipient_identifier: Optional[str] = None,
        custom_data: Optional[dict[str, Any]] = None,
        verification_url: Optional[str] = None,
    ):
        self.recipient_name = recipient_name
        self.recipient_email = recipient_email
        self.event_name = event_name
        self.issue_date = issue_date
        self.issuer_name = issuer_name
        self.issuer_title = issuer_title
        self.organization = organization
        self.certificate_code = certificate_code
        self.recipient_identifier = recipient_identifier
        self.custom_data = custom_data or {}
        self.verification_url = verification_url or f"https://verify.certificate.org/{certificate_code}"


class CertificateGenerator:
    """
    High-performance, elegant vector PDF Certificate Generator using ReportLab.
    Produces high-resolution, print-ready certificates on Landscape A4.
    """

    PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)  # 841.89 x 595.27 points

    # Color Palette
    COLOR_NAVY_DARK = colors.HexColor("#0A192F")
    COLOR_NAVY_LIGHT = colors.HexColor("#1E3A8A")
    COLOR_GOLD_DARK = colors.HexColor("#B8860B")
    COLOR_GOLD_LIGHT = colors.HexColor("#D4AF37")
    COLOR_GOLD_ACCENT = colors.HexColor("#F3E5AB")
    COLOR_TEXT_DARK = colors.HexColor("#0F172A")
    COLOR_TEXT_MUTED = colors.HexColor("#475569")
    COLOR_TEXT_LIGHT = colors.HexColor("#64748B")
    COLOR_BG_CREAM = colors.HexColor("#FDFAF6")

    @classmethod
    def generate_pdf(cls, data: CertificateData, output_path: Path) -> Path:
        """
        Generate a certificate PDF and save to output_path.
        Returns the output Path.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        c = canvas.Canvas(str(output_path), pagesize=(cls.PAGE_WIDTH, cls.PAGE_HEIGHT))
        c.setTitle(f"Certificate - {data.recipient_name}")
        c.setAuthor(data.organization)
        c.setSubject(data.event_name)

        # 1. Background Fill
        c.setFillColor(cls.COLOR_BG_CREAM)
        c.rect(0, 0, cls.PAGE_WIDTH, cls.PAGE_HEIGHT, fill=1, stroke=0)

        # 2. Draw Decorative Borders
        cls._draw_borders_and_decorations(c)

        # 3. Draw Header & Organization
        cls._draw_header(c, data)

        # 4. Draw Recipient Section
        cls._draw_recipient(c, data)

        # 5. Draw Body / Event Statement
        cls._draw_body_statement(c, data)

        # 6. Draw Gold Seal & Watermark in lower footer center
        cls._draw_seal(c, cls.PAGE_WIDTH / 2, 38 * mm)

        # 7. Draw Signatures & Footer Metadata
        cls._draw_footer(c, data)

        # Finalize and write
        c.showPage()
        c.save()
        return output_path

    @classmethod
    def _draw_borders_and_decorations(cls, c: canvas.Canvas) -> None:
        w, h = cls.PAGE_WIDTH, cls.PAGE_HEIGHT

        # Outer thick navy border
        c.setStrokeColor(cls.COLOR_NAVY_DARK)
        c.setLineWidth(5)
        c.rect(12 * mm, 12 * mm, w - 24 * mm, h - 24 * mm, stroke=1, fill=0)

        # Inner thin gold border
        c.setStrokeColor(cls.COLOR_GOLD_LIGHT)
        c.setLineWidth(1.5)
        c.rect(16 * mm, 16 * mm, w - 32 * mm, h - 32 * mm, stroke=1, fill=0)

        # Innermost fine decorative border
        c.setStrokeColor(cls.COLOR_GOLD_DARK)
        c.setLineWidth(0.5)
        c.rect(18 * mm, 18 * mm, w - 36 * mm, h - 36 * mm, stroke=1, fill=0)

        # Corner Ornaments (Geometric 4-corner accents)
        corner_offsets = [
            (16 * mm, 16 * mm, 1, 1),
            (w - 16 * mm, 16 * mm, -1, 1),
            (16 * mm, h - 16 * mm, 1, -1),
            (w - 16 * mm, h - 16 * mm, -1, -1),
        ]
        c.setFillColor(cls.COLOR_GOLD_DARK)
        c.setStrokeColor(cls.COLOR_GOLD_DARK)
        c.setLineWidth(1)
        for cx, cy, dx, dy in corner_offsets:
            p = c.beginPath()
            p.moveTo(cx, cy)
            p.lineTo(cx + 14 * mm * dx, cy)
            p.lineTo(cx, cy + 14 * mm * dy)
            p.close()
            c.drawPath(p, fill=1, stroke=0)

            # Extra corner notch
            c.circle(cx + 5 * mm * dx, cy + 5 * mm * dy, 1.2 * mm, fill=1, stroke=0)

    @classmethod
    def _draw_header(cls, c: canvas.Canvas, data: CertificateData) -> None:
        w, h = cls.PAGE_WIDTH, cls.PAGE_HEIGHT

        # Issuing Organization
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(cls.COLOR_GOLD_DARK)
        c.drawCentredString(w / 2, h - 32 * mm, data.organization.upper())

        # Thin divider line under organization
        c.setStrokeColor(cls.COLOR_GOLD_LIGHT)
        c.setLineWidth(0.8)
        org_width = c.stringWidth(data.organization.upper(), "Helvetica-Bold", 11)
        line_half = max(org_width / 2 + 15, 60)
        c.line(w / 2 - line_half, h - 34.5 * mm, w / 2 + line_half, h - 34.5 * mm)

        # Certificate Main Title
        c.setFont("Helvetica-Bold", 26)
        c.setFillColor(cls.COLOR_NAVY_DARK)
        c.drawCentredString(w / 2, h - 48 * mm, "CERTIFICATE OF ACHIEVEMENT")

        # Subtitle / Presentation line
        c.setFont("Helvetica", 11)
        c.setFillColor(cls.COLOR_TEXT_MUTED)
        c.drawCentredString(w / 2, h - 57 * mm, "THIS IS PROUDLY PRESENTED TO")

    @classmethod
    def _draw_recipient(cls, c: canvas.Canvas, data: CertificateData) -> None:
        w, h = cls.PAGE_WIDTH, cls.PAGE_HEIGHT

        name = data.recipient_name
        # Dynamic font scaling to ensure names never clip
        font_size = 28
        max_width = w - 100 * mm
        while c.stringWidth(name, "Helvetica-Bold", font_size) > max_width and font_size > 16:
            font_size -= 2

        c.setFont("Helvetica-Bold", font_size)
        c.setFillColor(cls.COLOR_NAVY_LIGHT)
        c.drawCentredString(w / 2, h - 74 * mm, name)

        # Decorative underline below recipient name
        name_width = c.stringWidth(name, "Helvetica-Bold", font_size)
        c.setStrokeColor(cls.COLOR_GOLD_LIGHT)
        c.setLineWidth(1.5)
        c.line(w / 2 - name_width / 2 - 10, h - 78 * mm, w / 2 + name_width / 2 + 10, h - 78 * mm)

        # Center diamond accent on underline
        c.setFillColor(cls.COLOR_GOLD_DARK)
        diamond_y = h - 78 * mm
        p = c.beginPath()
        p.moveTo(w / 2, diamond_y + 3)
        p.lineTo(w / 2 + 4, diamond_y)
        p.lineTo(w / 2, diamond_y - 3)
        p.lineTo(w / 2 - 4, diamond_y)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

    @classmethod
    def _draw_body_statement(cls, c: canvas.Canvas, data: CertificateData) -> None:
        w, h = cls.PAGE_WIDTH, cls.PAGE_HEIGHT

        # Context description
        c.setFont("Helvetica", 11)
        c.setFillColor(cls.COLOR_TEXT_MUTED)
        c.drawCentredString(
            w / 2,
            h - 88 * mm,
            "for successfully fulfilling all requirements and demonstrating outstanding excellence in",
        )

        # Event / Course Name
        event = data.event_name
        font_size = 18
        max_width = w - 90 * mm
        while c.stringWidth(event, "Helvetica-Bold", font_size) > max_width and font_size > 12:
            font_size -= 1.5

        c.setFont("Helvetica-Bold", font_size)
        c.setFillColor(cls.COLOR_NAVY_DARK)
        c.drawCentredString(w / 2, h - 98 * mm, event)

        # Optional Custom Details or Identifier
        extra_items = []
        if data.recipient_identifier:
            extra_items.append(f"ID: {data.recipient_identifier}")
        if data.custom_data:
            for k, v in data.custom_data.items():
                if isinstance(v, (str, int, float)):
                    formatted_k = k.replace("_", " ").title()
                    extra_items.append(f"{formatted_k}: {v}")

        if extra_items:
            c.setFont("Helvetica", 9)
            c.setFillColor(cls.COLOR_TEXT_LIGHT)
            details_str = "  |  ".join(extra_items[:3])  # Top 3 attributes
            c.drawCentredString(w / 2, h - 107 * mm, details_str)

    @classmethod
    def _draw_seal(cls, c: canvas.Canvas, cx: float, cy: float) -> None:
        """Draw an official gold rosette seal with star and circular inscription."""
        # Rosette petals (outer sunburst)
        c.setFillColor(cls.COLOR_GOLD_ACCENT)
        c.setStrokeColor(cls.COLOR_GOLD_LIGHT)
        c.setLineWidth(0.5)

        num_points = 24
        radius_outer = 16 * mm
        radius_inner = 13.5 * mm

        p = c.beginPath()
        for i in range(num_points * 2):
            angle = i * math.pi / num_points
            r = radius_outer if i % 2 == 0 else radius_inner
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            if i == 0:
                p.moveTo(x, y)
            else:
                p.lineTo(x, y)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

        # Inner gold ring
        c.setFillColor(cls.COLOR_GOLD_LIGHT)
        c.setStrokeColor(cls.COLOR_GOLD_DARK)
        c.setLineWidth(1)
        c.circle(cx, cy, 12.5 * mm, fill=1, stroke=1)

        # Inner navy core
        c.setFillColor(cls.COLOR_NAVY_DARK)
        c.circle(cx, cy, 9.5 * mm, fill=1, stroke=0)

        # Central Star
        c.setFillColor(cls.COLOR_GOLD_LIGHT)
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(cx, cy - 4.5, "★")

        # Subtle seal text around
        c.setFont("Helvetica-Bold", 5)
        c.setFillColor(cls.COLOR_GOLD_ACCENT)
        c.drawCentredString(cx, cy + 6.5 * mm, "VERIFIED")
        c.drawCentredString(cx, cy - 8 * mm, "EXCELLENCE")

    @classmethod
    def _draw_footer(cls, c: canvas.Canvas, data: CertificateData) -> None:
        w, h = cls.PAGE_WIDTH, cls.PAGE_HEIGHT
        left_margin = 35 * mm
        right_margin = w - 35 * mm
        footer_line_y = 36 * mm

        # Left Column: Date & Verification ID
        c.setStrokeColor(cls.COLOR_TEXT_LIGHT)
        c.setLineWidth(0.8)
        c.line(left_margin, footer_line_y, left_margin + 50 * mm, footer_line_y)

        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(cls.COLOR_TEXT_DARK)
        c.drawString(left_margin, footer_line_y - 4.5 * mm, data.issue_date)

        c.setFont("Helvetica", 8)
        c.setFillColor(cls.COLOR_TEXT_LIGHT)
        c.drawString(left_margin, footer_line_y - 8.5 * mm, "Date of Issuance")

        # Certificate Verification Code Box
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(cls.COLOR_NAVY_DARK)
        c.drawString(left_margin, footer_line_y - 14 * mm, f"ID: {data.certificate_code}")

        # Right Column: Issuer Signature & Title
        sig_width = 55 * mm
        c.setStrokeColor(cls.COLOR_TEXT_LIGHT)
        c.setLineWidth(0.8)
        c.line(right_margin - sig_width, footer_line_y, right_margin, footer_line_y)

        # Stylized faux signature representation
        c.setFont("Times-Italic", 14)
        c.setFillColor(cls.COLOR_NAVY_LIGHT)
        c.drawCentredString(right_margin - sig_width / 2, footer_line_y + 4 * mm, data.issuer_name)

        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(cls.COLOR_TEXT_DARK)
        c.drawCentredString(right_margin - sig_width / 2, footer_line_y - 4.5 * mm, data.issuer_name)

        c.setFont("Helvetica", 8)
        c.setFillColor(cls.COLOR_TEXT_LIGHT)
        c.drawCentredString(right_margin - sig_width / 2, footer_line_y - 8.5 * mm, data.issuer_title)

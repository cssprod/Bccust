"""
Export evidence log to PDF and CSV formats for court submission.
"""
import csv
import io
from datetime import datetime
from typing import List, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
)


LEGAL_DISCLAIMER = (
    "This tool organizes communication records for informational and clerical preparation only. "
    "It does not provide legal advice, and users must retain original unedited device screenshots "
    "to authenticate evidence for BC Provincial or Supreme Court."
)


def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawString(0.75 * inch, 0.5 * inch, "BC Parenting Log - Evidence Exhibit")
    canvas.drawRightString(letter[0] - 0.75 * inch, 0.5 * inch, f"Page {doc.page}")
    canvas.setFont("Helvetica-Oblique", 7)
    canvas.drawString(0.75 * inch, 0.35 * inch, LEGAL_DISCLAIMER[:120])
    canvas.restoreState()


def export_pdf(infractions: List[Dict], output_path: str, case_info: Dict = None) -> str:
    """Generate a court-ready PDF exhibit table."""
    case_info = case_info or {}
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.75 * inch, bottomMargin=0.9 * inch)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=16, spaceAfter=12)
    subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=10, spaceAfter=6)

    story = []
    story.append(Paragraph("BC Parenting Log - Evidence Exhibit", title_style))

    if case_info.get("case_name"):
        story.append(Paragraph(f"Case: {case_info['case_name']}", subtitle_style))
    if case_info.get("court"):
        story.append(Paragraph(f"Court: {case_info['court']}", subtitle_style))
    if case_info.get("file_number"):
        story.append(Paragraph(f"File Number: {case_info['file_number']}", subtitle_style))
    story.append(Spacer(1, 12))

    # Build table
    header = ["Exhibit #", "Date & Time", "BC FLA Category", "Severity", "Verbatim Quote", "Objective Summary"]
    rows = [header]

    for i, inf in enumerate(infractions, 1):
        rows.append([
            f"EX-{i:02d}",
            inf.get("timestamp", ""),
            inf.get("category", ""),
            inf.get("severity", ""),
            inf.get("verbatim_quote", ""),
            inf.get("objective_summary", ""),
        ])

    col_widths = [0.65 * inch, 0.95 * inch, 1.35 * inch, 0.55 * inch, 2.0 * inch, 1.9 * inch]
    table = Table(rows, colWidths=col_widths, repeatRows=1)

    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7.5),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])

    # Severity coloring
    severity_colors = {
        "High": colors.HexColor("#fee2e2"),
        "Medium": colors.HexColor("#fef3c7"),
        "Low": colors.HexColor("#d1fae5"),
    }
    for i, inf in enumerate(infractions, start=1):
        sev = inf.get("severity", "")
        if sev in severity_colors:
            style.add("BACKGROUND", (3, i), (3, i), severity_colors[sev])

    table.setStyle(style)
    story.append(table)
    story.append(Spacer(1, 16))
    story.append(Paragraph(LEGAL_DISCLAIMER, subtitle_style))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return output_path


def export_csv(infractions: List[Dict], output_path: str) -> str:
    """Export infractions to CSV."""
    fieldnames = ["exhibit_number", "timestamp", "category", "severity",
                  "verbatim_quote", "context_before_after", "objective_summary"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, inf in enumerate(infractions, 1):
            writer.writerow({
                "exhibit_number": f"EX-{i:02d}",
                "timestamp": inf.get("timestamp", ""),
                "category": inf.get("category", ""),
                "severity": inf.get("severity", ""),
                "verbatim_quote": inf.get("verbatim_quote", ""),
                "context_before_after": inf.get("context_before_after", ""),
                "objective_summary": inf.get("objective_summary", ""),
            })
    return output_path


def export_xlsx(infractions: List[Dict], output_path: str) -> str:
    """Export infractions to Excel (.xlsx)."""
    import pandas as pd

    rows = []
    for i, inf in enumerate(infractions, 1):
        rows.append({
            "Exhibit #": f"EX-{i:02d}",
            "Date & Time": inf.get("timestamp", ""),
            "BC FLA Category": inf.get("category", ""),
            "Severity": inf.get("severity", ""),
            "Verbatim Quote": inf.get("verbatim_quote", ""),
            "Context / Before-After": inf.get("context_before_after", ""),
            "Objective Summary": inf.get("objective_summary", ""),
        })

    df = pd.DataFrame(rows)
    df.to_excel(output_path, index=False)
    return output_path

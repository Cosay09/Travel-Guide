# utils/pdf_export.py
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def export_itinerary_to_pdf(plan: dict | list, path: str, title: str = "Itinerary"):
    """
    plan:
      - dict with keys: requested, costs, plan
      - OR directly a list of day plans
    """

    # Normalize plan
    if isinstance(plan, dict) and "plan" in plan:
        plan_list = plan["plan"]
        requested = plan.get("requested", {})
    elif isinstance(plan, list):
        plan_list = plan
        requested = {}
    else:
        raise ValueError("Invalid plan shape for PDF export")

    # Optional Bangla font
    FONT_PATH = os.path.join("data", "fonts", "SolaimanLipi.ttf")
    font_name = "Helvetica"

    try:
        if os.path.exists(FONT_PATH):
            pdfmetrics.registerFont(TTFont("Bangla", FONT_PATH))
            font_name = "Bangla"
    except Exception:
        font_name = "Helvetica"

    # Document setup
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleCenter",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontName=font_name,
            fontSize=18,
            leading=22,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DayHeading",
            parent=styles["Heading2"],
            fontName=font_name,
            fontSize=14,
            leading=18,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="StopName",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=12,
            leading=14,
            spaceAfter=2,
            leftIndent=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="StopDesc",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=11,
            leading=14,
            spaceAfter=8,
            leftIndent=12,
            textColor="#333333",
        )
    )
    styles.add(
        ParagraphStyle(
            name="Meta",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=9,
            leading=11,
            textColor="#666666",
        )
    )

    story = []

    # Title
    story.append(Paragraph(title, styles["TitleCenter"]))
    story.append(Spacer(1, 6))

    # Meta line
    if requested:
        meta = f"{requested.get('days','?')} days · {requested.get('people','?')} people · {requested.get('destination','')}"
        story.append(Paragraph(meta, styles["Meta"]))
        story.append(Spacer(1, 6))

    # Days
    for day in plan_list:
        day_no = day.get("day")
        story.append(
            Paragraph(f"Day {day_no}" if day_no else "Day", styles["DayHeading"])
        )

        stops = day.get("stops", [])
        if not stops:
            story.append(Paragraph("No suggested stops.", styles["StopDesc"]))
        else:
            for stop in stops:
                time = stop.get("time", "")
                name = stop.get("name", "")
                desc = stop.get("desc") or stop.get("summary", "")

                story.append(
                    Paragraph(f"<b>{time} — {name}</b>", styles["StopName"])
                )
                if desc:
                    story.append(Paragraph(desc, styles["StopDesc"]))

        story.append(Spacer(1, 8))

    doc.build(story)

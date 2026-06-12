"""Report export service using ReportLab.

Generates PDF reports with VisSpec watermark, diagrams, metrics, and traceability.
"""

import io
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


def _add_watermark(canvas_obj, doc):
    """Add VisSpec watermark to every page."""
    canvas_obj.saveState()

    watermark = settings.REPORT_WATERMARK
    canvas_obj.setFont("Helvetica", 60)
    canvas_obj.setFillColor(HexColor("#E0E0E0"))
    canvas_obj.rotate(45)
    canvas_obj.drawString(100, 200, watermark)
    canvas_obj.restoreState()


class ExportService:
    """Generates PDF reports with analysis results, diagrams, and metrics."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._register_styles()

    def _register_styles(self):
        """Register custom paragraph styles."""
        self.styles.add(
            ParagraphStyle(
                name="ReportTitle",
                parent=self.styles["Title"],
                fontSize=24,
                textColor=HexColor("#1A2332"),
                spaceAfter=6,
                alignment=TA_CENTER,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="ReportSubtitle",
                parent=self.styles["Normal"],
                fontSize=12,
                textColor=HexColor("#5A6B7F"),
                spaceAfter=20,
                alignment=TA_CENTER,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Heading1"],
                fontSize=16,
                textColor=HexColor("#2C3E50"),
                spaceBefore=20,
                spaceAfter=10,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="SubSectionHeader",
                parent=self.styles["Heading2"],
                fontSize=13,
                textColor=HexColor("#34495E"),
                spaceBefore=12,
                spaceAfter=6,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="BodyTextCustom",
                parent=self.styles["Normal"],
                fontSize=10,
                leading=14,
                alignment=TA_JUSTIFY,
            )
        )

    def generate_report(
        self,
        project_name: str,
        analysis_data: Dict[str, Any],
        diagrams: Optional[List[Dict[str, Any]]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        traceability: Optional[List[Dict[str, Any]]] = None,
        report_type: str = "full",
    ) -> bytes:
        """Generate a PDF report. Returns PDF bytes."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            title=f"VisSpec Report - {project_name}",
            author="VisSpec",
            onFirstPage=_add_watermark,
            onLaterPages=_add_watermark,
        )

        story: List[Any] = []

        # Title page
        story.append(Paragraph("VisSpec", self.styles["ReportTitle"]))
        story.append(
            Paragraph(
                "Visual Specification System", self.styles["ReportSubtitle"]
            )
        )
        story.append(Spacer(1, 30))
        story.append(Paragraph(project_name, self.styles["Title"]))
        story.append(Spacer(1, 10))
        story.append(
            Paragraph(
                f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
                self.styles["BodyTextCustom"],
            )
        )
        story.append(
            Paragraph(
                f"Report Type: {report_type.title()}",
                self.styles["BodyTextCustom"],
            )
        )
        story.append(PageBreak())

        # Executive Summary
        if report_type in ("full", "summary"):
            story.append(
                Paragraph("Executive Summary", self.styles["SectionHeader"])
            )
            if analysis_data:
                score = analysis_data.get("overall_score", "N/A")
                total_defects = analysis_data.get("total_defects", 0)
                story.append(
                    Paragraph(
                        f"<b>Overall Quality Score:</b> {score}/100<br/>"
                        f"<b>Total Defects Found:</b> {total_defects}",
                        self.styles["BodyTextCustom"],
                    )
                )
                story.append(Spacer(1, 10))

                defects_by_type = analysis_data.get("defects_by_type", {})
                if defects_by_type:
                    story.append(
                        Paragraph(
                            "<b>Defects by Type:</b>",
                            self.styles["BodyTextCustom"],
                        )
                    )
                    data = [["Type", "Count"]]
                    for dtype, count in defects_by_type.items():
                        data.append([str(dtype).title(), str(count)])
                    table = Table(data, colWidths=[3 * inch, 1.5 * inch])
                    table.setStyle(
                        TableStyle(
                            [
                                (
                                    "BACKGROUND",
                                    (0, 0),
                                    (-1, 0),
                                    HexColor("#2C3E50"),
                                ),
                                (
                                    "TEXTCOLOR",
                                    (0, 0),
                                    (-1, 0),
                                    HexColor("#FFFFFF"),
                                ),
                                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                (
                                    "FONTNAME",
                                    (0, 0),
                                    (-1, 0),
                                    "Helvetica-Bold",
                                ),
                                ("FONTSIZE", (0, 0), (-1, -1), 10),
                                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                                (
                                    "BACKGROUND",
                                    (0, 1),
                                    (-1, -1),
                                    HexColor("#F8F9FA"),
                                ),
                                (
                                    "GRID",
                                    (0, 0),
                                    (-1, -1),
                                    1,
                                    HexColor("#DEE2E6"),
                                ),
                            ]
                        )
                    )
                    story.append(table)
                    story.append(Spacer(1, 15))

            story.append(PageBreak())

        # Metrics section
        if report_type == "full" and metrics:
            story.append(Paragraph("Project Metrics", self.styles["SectionHeader"]))
            metric_items = [
                ("Complexity Score", metrics.get("complexity_score", "N/A")),
                ("Estimated Weeks", metrics.get("estimated_weeks", "N/A")),
                ("Cost Index", metrics.get("relative_cost_index", "N/A")),
                ("Actor Count", metrics.get("actor_count", 0)),
                (
                    "Total Requirements",
                    metrics.get("total_requirements", 0),
                ),
                ("Quality Score", metrics.get("quality_score", "N/A")),
            ]

            data = [["Metric", "Value"]]
            for label, value in metric_items:
                data.append([label, str(value)])

            table = Table(data, colWidths=[3 * inch, 2 * inch])
            table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            HexColor("#2C3E50"),
                        ),
                        (
                            "TEXTCOLOR",
                            (0, 0),
                            (-1, 0),
                            HexColor("#FFFFFF"),
                        ),
                        ("ALIGN", (0, 0), (0, -1), "LEFT"),
                        ("ALIGN", (1, 0), (1, -1), "CENTER"),
                        (
                            "FONTNAME",
                            (0, 0),
                            (-1, 0),
                            "Helvetica-Bold",
                        ),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                        (
                            "BACKGROUND",
                            (0, 1),
                            (-1, -1),
                            HexColor("#F8F9FA"),
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            1,
                            HexColor("#DEE2E6"),
                        ),
                    ]
                )
            )
            story.append(table)
            story.append(PageBreak())

        # Defects detail
        if report_type == "full" and analysis_data:
            story.append(
                Paragraph("Defect Details", self.styles["SectionHeader"])
            )
            defects = analysis_data.get("defects", [])
            if defects:
                for i, defect in enumerate(defects[:50], 1):
                    story.append(
                        Paragraph(
                            f"<b>Defect #{i}</b> [{defect.get('severity', 'N/A').upper()}]",
                            self.styles["SubSectionHeader"],
                        )
                    )
                    story.append(
                        Paragraph(
                            f"<b>Type:</b> {defect.get('type', 'N/A')}<br/>"
                            f"<b>Confidence:</b> {defect.get('confidence', 0):.0%}<br/>"
                            f"<b>Description:</b> {defect.get('description', 'N/A')}<br/>"
                            f"<b>Suggestion:</b> {defect.get('suggestion', 'N/A')}",
                            self.styles["BodyTextCustom"],
                        )
                    )
                    story.append(Spacer(1, 8))
            else:
                story.append(
                    Paragraph("No defects found.", self.styles["BodyTextCustom"])
                )
            story.append(PageBreak())

        # Traceability
        if report_type == "full" and traceability:
            story.append(
                Paragraph("Traceability Matrix", self.styles["SectionHeader"])
            )
            data = [["Req ID", "Status", "Defects", "Diagrams"]]
            for item in traceability[:100]:
                data.append(
                    [
                        item.get("req_id", ""),
                        item.get("validation_status", ""),
                        item.get("defect_count", "0"),
                        item.get("diagram_count", "0"),
                    ]
                )

            table = Table(data, colWidths=[1.5 * inch, 1.2 * inch, 1 * inch, 1 * inch])
            table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            HexColor("#2C3E50"),
                        ),
                        (
                            "TEXTCOLOR",
                            (0, 0),
                            (-1, 0),
                            HexColor("#FFFFFF"),
                        ),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            1,
                            HexColor("#DEE2E6"),
                        ),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [HexColor("#FFFFFF"), HexColor("#F8F9FA")],
                        ),
                    ]
                )
            )
            story.append(table)

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()


# Backwards-compatible alias for existing imports.
ReportExportService = ExportService


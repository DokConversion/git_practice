"""
Export engine: CSV and PDF generation from KPI dicts.
"""
import io
import csv
from datetime import date


def export_csv(kpis: dict, client_name: str, date_from: date, date_to: date) -> bytes:
    """Return CSV bytes ready for st.download_button."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Kunde", client_name])
    writer.writerow(["Zeitraum", f"{date_from} bis {date_to}"])
    writer.writerow([])
    writer.writerow(["KPI", "Wert"])
    for k, v in kpis.items():
        if not k.startswith("_") and not isinstance(v, list):
            writer.writerow([k, v])
    return buf.getvalue().encode("utf-8-sig")


def export_pdf(kpis: dict, targets: dict, client_name: str, date_from: date, date_to: date) -> bytes:
    """Return PDF bytes using ReportLab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        )
        from reportlab.lib.units import cm

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story  = []

        # Title
        title_style = ParagraphStyle("title", parent=styles["Heading1"], fontSize=18, spaceAfter=6)
        story.append(Paragraph(f"Performance Report: {client_name}", title_style))
        story.append(Paragraph(f"Zeitraum: {date_from} – {date_to}", styles["Normal"]))
        story.append(Spacer(1, 0.5*cm))

        # KPI Table
        data = [["KPI", "Ist-Wert", "Ziel-Wert"]]
        display_keys = {
            "meta_spend":        "Meta Spend (€)",
            "meta_leads":        "Meta Leads",
            "meta_cpl":          "Meta CPL (€)",
            "meta_ctr":          "Meta CTR (%)",
            "meta_roas":         "Meta ROAS",
            "ga4_sessions":      "GA4 Sessions",
            "ga4_conversion_rate": "GA4 Conv.-Rate (%)",
            "crm_new_leads":     "CRM Neue Leads",
            "crm_revenue":       "CRM Revenue (€)",
            "crm_won_deals":     "Gewonnene Deals",
            "combined_roas":     "Gesamt-ROAS",
            "combined_cac":      "CAC (€)",
        }
        for key, label in display_keys.items():
            val = kpis.get(key, "–")
            tgt = targets.get(key, {}).get("value")
            data.append([
                label,
                f"{val:,.2f}" if isinstance(val, float) else str(val),
                f"{tgt:,.2f}" if isinstance(tgt, float) else (str(tgt) if tgt is not None else "–"),
            ])

        col_widths = [9*cm, 4*cm, 4*cm]
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, 0), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
            ("FONTSIZE",   (0, 1), (-1, -1), 9),
            ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(table)
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph(
            f"Erstellt am {date.today()} | Performance Dashboard",
            styles["Normal"],
        ))

        doc.build(story)
        return buf.getvalue()
    except ImportError:
        raise RuntimeError("reportlab ist nicht installiert. Bitte 'pip install reportlab' ausführen.")

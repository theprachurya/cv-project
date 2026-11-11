from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _table(rows, widths=None):
    t = Table(rows, colWidths=widths, hAlign="LEFT")
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbe7fb")),
                           ("FONTSIZE", (0, 0), (-1, -1), 9), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


def build_pdf(path, session: dict, summary: dict, alerts: list[dict]):
    ss = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=A4, title="Road safety analysis report")
    el = [Paragraph("Smart Road Safety Analysis Report", ss["Title"]),
          Paragraph("Driver-assistance simulation using computer vision. Distances and times are approximate "
                    "and this is not a certified automotive safety system.", ss["Italic"]), Spacer(1, 10)]
    g = summary.get
    el += [_table([["Item", "Value"],
                   ["Video / source", session.get("filename") or session["source"]],
                   ["Analysis duration", f"{g('duration_s', 0)} s (video time {g('video_seconds', 0)} s)"],
                   ["Frames analyzed", g("frames_analyzed", 0)],
                   ["Unique objects detected", g("unique_objects", 0)],
                   ["Vehicles / pedestrians", f"{g('vehicles', 0)} / {g('pedestrians', 0)}"],
                   ["Average detection confidence", f"{g('avg_confidence', 0):.0%}"],
                   ["Total alerts", g("total_alerts", 0)],
                   ["High-risk events", len([a for a in alerts if a["severity"] == "high"])],
                   ["Left / right blind-spot alerts", f"{g('left_alerts', 0)} / {g('right_alerts', 0)}"]], [200, 280]), Spacer(1, 12)]
    for title, key in (("Detections by class", "by_label"), ("Alerts by type", "alerts_by_type"),
                       ("Risk distribution (% of frames)", "risk_distribution"), ("Motion distribution (object-frames)", "motion_distribution")):
        data = g(key) or {}
        el += [Paragraph(title, ss["Heading3"]), _table([["Name", "Value"]] + [[k, v] for k, v in data.items()] or [["-", "-"]], [200, 280]), Spacer(1, 8)]
    ev = [a for a in alerts if a["severity"] == "high"][:25]
    el.append(Paragraph("Important events (high severity)", ss["Heading3"]))
    el.append(_table([["Video time", "Type", "Object", "Reason"]] +
                     [[f"{a['video_time']} s", a["type"], f"#{a['track_id']}", Paragraph(a["reason"], ss["BodyText"])] for a in ev]
                     if ev else [["No high-severity events recorded"]], [60, 100, 45, 275] if ev else None))
    doc.build(el)

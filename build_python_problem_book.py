from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether

from problem_book_source import PROBLEMS, SOURCE_URL, COURSE_URL, LECTURE_URL, QUIZ_URL


OUT = Path(__file__).parent / "output" / "pdf" / "python-problem-book-newton-psp-b.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

blue = colors.HexColor("#173B69")
teal = colors.HexColor("#168B83")
ink = colors.HexColor("#202B38")
muted = colors.HexColor("#617083")
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=27, leading=33, textColor=blue, alignment=TA_CENTER, spaceAfter=12))
styles.add(ParagraphStyle(name="Deck", parent=styles["Normal"], fontSize=12, leading=18, textColor=muted, alignment=TA_CENTER))
styles.add(ParagraphStyle(name="Chapter", parent=styles["Heading1"], fontSize=19, leading=24, textColor=blue, spaceBefore=8, spaceAfter=12))
styles.add(ParagraphStyle(name="Question", parent=styles["Heading2"], fontSize=13, leading=17, textColor=ink, spaceBefore=12, spaceAfter=6))
styles.add(ParagraphStyle(name="BodyText2", parent=styles["BodyText"], fontSize=10.5, leading=16, textColor=ink, spaceAfter=8))
styles.add(ParagraphStyle(name="Meta", parent=styles["BodyText"], fontSize=8.5, leading=12, textColor=muted))
styles.add(ParagraphStyle(name="Note", parent=styles["BodyText"], fontSize=9.5, leading=14, textColor=ink, backColor=colors.HexColor("#EEF5FA"), borderColor=colors.HexColor("#D7E3EF"), borderWidth=0.6, borderPadding=9, spaceBefore=10, spaceAfter=12))


def footer(canvas, doc):
    canvas.saveState()
    w, _ = A4
    canvas.setStrokeColor(colors.HexColor("#DCE4EC"))
    canvas.line(18 * mm, 15 * mm, w - 18 * mm, 15 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(muted)
    canvas.drawString(18 * mm, 10 * mm, "Newton School | PSP B | Captured 2 November 2026")
    canvas.drawRightString(w - 18 * mm, 10 * mm, f"{doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm, topMargin=20 * mm, bottomMargin=23 * mm, title="Python Problem Book - Newton PSP B")
story = [Spacer(1, 32 * mm), Paragraph("Python Problem Book", styles["CoverTitle"]), Paragraph("Newton School | PSP B", styles["Deck"]), Spacer(1, 8 * mm), Paragraph("Chapter-wise problem statements captured from course assignments and a lecture-attached classroom quiz.", styles["Deck"]), Spacer(1, 17 * mm), Paragraph(f"<b>Verified in this edition:</b> {len(PROBLEMS)} full problem and quiz prompts across Python functions, scope, if-else, and logical operators. Includes the 3-question 2 November assignment, 5 assignments attached to the 30 September lecture, and all 4 questions in its in-class quiz.", styles["Note"]), Paragraph("Problem statements only. No answers or solutions are included.", styles["Deck"]), PageBreak()]
current_chapter = None
for i, p in enumerate(PROBLEMS, 1):
    if p["chapter"] != current_chapter:
        current_chapter = p["chapter"]
        story.append(Paragraph(current_chapter, styles["Chapter"]))
    story.append(KeepTogether([
        Paragraph(f"{i}. {p['title']}", styles["Question"]),
        Paragraph(f"<b>Type / difficulty:</b> {p['difficulty']}", styles["Meta"]),
        Spacer(1, 2 * mm),
        Paragraph(p["statement"].replace("\n", "<br/>"), styles["BodyText2"]),
    ]))
story.extend([Spacer(1, 6 * mm), Paragraph("Sources", styles["Heading2"]), Paragraph(f"Newton School assignment page: <link href='{SOURCE_URL}' color='#168B83'>PSP B Python Function assignment</link>", styles["Meta"]), Paragraph(f"Course assignment list: <link href='{COURSE_URL}' color='#168B83'>PSP B assignments</link>", styles["Meta"]), Paragraph(f"Lecture assignments: <link href='{LECTURE_URL}' color='#168B83'>Python if-else lecture assignments</link>", styles["Meta"]), Paragraph(f"In-class quiz: <link href='{QUIZ_URL}' color='#168B83'>Python if-else classroom quiz</link>", styles["Meta"]), Spacer(1, 5 * mm), Paragraph("This is a source-verified partial collection. Newton lists 70 PSP B assignment questions; this edition includes only the full prompts captured so far, plus the accessible lecture-attached questions above.", styles["Note"])])
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)

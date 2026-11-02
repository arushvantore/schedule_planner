"""Build a chapter-grouped PDF from Python problems synced for one student."""
from collections import defaultdict
from html import escape
import io
import re
from urllib.parse import urlsplit

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Preformatted, Spacer

PROBLEM_KINDS = {"question", "problem", "exercise", "assignment", "quiz", "contest", "worksheet"}


def _is_python_problem(row):
    kind = (row["kind"] or "").casefold()
    language = (row["language"] or "").casefold()
    title = (row["title"] or "").casefold()
    content = (row["content"] or "").casefold()
    explicit_python = language in {"python", "python 3", "py"} or "python" in title
    fenced_python = bool(re.search(r"```\s*python\b", content))
    return kind in PROBLEM_KINDS and (explicit_python or fenced_python)


def collect_python_problems(conn):
    """Return distinct, explicitly identified Python problems from this DB."""
    rows = conn.execute(
        """SELECT id, kind, title, subject, chapter, language, content, url
           FROM source_items WHERE content IS NOT NULL OR url IS NOT NULL
           ORDER BY subject, chapter, title, id"""
    ).fetchall()
    result, seen = [], set()
    for row in rows:
        if not _is_python_problem(row):
            continue
        statement = (row["content"] or "").strip()
        title = (row["title"] or "Python problem").strip()
        identity = re.sub(r"\s+", " ", (title + "\n" + statement).casefold())
        if identity in seen:
            continue
        seen.add(identity)
        result.append({
            "title": title,
            "subject": row["subject"] or "Unsorted subject",
            "chapter": row["chapter"] or "Unsorted chapter",
            "content": statement or title,
            "url": row["url"],
        })
    return result


def _clean_text(value):
    return value.encode("latin-1", "replace").decode("latin-1")


def make_python_problems_pdf(problems):
    """Render one PDF with subject and chapter sections; return its bytes."""
    if not problems:
        return None
    grouped = defaultdict(lambda: defaultdict(list))
    for problem in problems:
        grouped[problem["subject"]][problem["chapter"]].append(problem)

    buffer = io.BytesIO()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "BookTitle", parent=styles["Title"], alignment=TA_CENTER,
        textColor=colors.HexColor("#26366b"), spaceAfter=8,
    )
    subject_style = ParagraphStyle(
        "Subject", parent=styles["Heading1"], textColor=colors.HexColor("#26366b"),
        spaceBefore=15, spaceAfter=8, keepWithNext=True,
    )
    chapter_style = ParagraphStyle(
        "Chapter", parent=styles["Heading2"], textColor=colors.HexColor("#4858b8"),
        spaceBefore=10, spaceAfter=6, keepWithNext=True,
    )
    problem_style = ParagraphStyle(
        "Problem", parent=styles["Heading3"], spaceBefore=7, spaceAfter=5,
        keepWithNext=True,
    )
    body_style = ParagraphStyle("ProblemBody", parent=styles["BodyText"], leading=14, spaceAfter=7)
    code_style = ParagraphStyle(
        "Code", fontName="Courier", fontSize=8, leading=10, leftIndent=8,
        rightIndent=8, backColor=colors.HexColor("#f1f3f8"), borderPadding=6, spaceAfter=7,
    )
    story = [
        Paragraph("Python Problem Book", title_style),
        Paragraph("Collected from the student's connected course sources", styles["Normal"]),
        Spacer(1, 8),
    ]
    index = 0
    for subject in sorted(grouped, key=str.casefold):
        story.append(Paragraph(escape(_clean_text(subject)), subject_style))
        for chapter in sorted(grouped[subject], key=str.casefold):
            story.append(Paragraph("Chapter: " + escape(_clean_text(chapter)), chapter_style))
            for problem in grouped[subject][chapter]:
                index += 1
                story.append(Paragraph(
                    f"Problem {index}: {escape(_clean_text(problem['title']))}", problem_style
                ))
                pieces = re.split(r"```(?:python)?\s*\n?(.*?)```", problem["content"], flags=re.I | re.S)
                for part_index, part in enumerate(pieces):
                    if not part.strip():
                        continue
                    if part_index % 2:
                        story.append(Preformatted(escape(_clean_text(part.strip())), code_style, maxLineLength=88))
                    else:
                        text = escape(_clean_text(part.strip())).replace("\n", "<br/>")
                        story.append(Paragraph(text, body_style))
                url = problem.get("url") or ""
                parsed = urlsplit(url)
                if parsed.scheme in {"http", "https"} and parsed.netloc:
                    safe_url = escape(url, quote=True)
                    label = escape(_clean_text(url))
                    story.append(Paragraph(
                        f'Source: <link href="{safe_url}" color="#4054b2">{label}</link>',
                        styles["BodyText"],
                    ))
                story.append(Spacer(1, 4))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#667085"))
        canvas.drawString(18 * mm, 12 * mm, "Schedule Planner - Python problem collection")
        canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, str(doc.page))
        canvas.restoreState()

    frame = Frame(18 * mm, 19 * mm, A4[0] - 36 * mm, A4[1] - 37 * mm, id="main")
    doc = BaseDocTemplate(buffer, pagesize=A4, title="Python Problem Book", author="Schedule Planner")
    doc.addPageTemplates([PageTemplate(id="book", frames=frame, onPage=footer)])
    doc.build(story)
    return buffer.getvalue()

from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    PageBreak,
    ListFlowable,
    ListItem,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "omniagentai_research_paper.md"
OUTPUT = ROOT / "docs" / "OmniAgentAI_Research_Paper.pdf"


def clean_inline(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.*?)`", r"<font name='Courier'>\1</font>", text)
    return text


def build_story(markdown: str):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="PaperTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=25,
        alignment=TA_CENTER,
        spaceAfter=24,
        textColor=colors.HexColor("#0F172A"),
    ))
    styles.add(ParagraphStyle(
        name="AuthorLine",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475569"),
        spaceAfter=18,
    ))
    styles.add(ParagraphStyle(
        name="H1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        spaceBefore=14,
        spaceAfter=8,
        textColor=colors.HexColor("#0F172A"),
    ))
    styles.add(ParagraphStyle(
        name="H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        spaceBefore=10,
        spaceAfter=6,
        textColor=colors.HexColor("#1E293B"),
    ))
    styles.add(ParagraphStyle(
        name="Body",
        parent=styles["BodyText"],
        fontName="Times-Roman",
        fontSize=10.5,
        leading=14,
        alignment=TA_LEFT,
        spaceAfter=7,
    ))
    styles.add(ParagraphStyle(
        name="PaperBullet",
        parent=styles["Body"],
        leftIndent=14,
        firstLineIndent=0,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="CodeBlock",
        parent=styles["Body"],
        fontName="Courier",
        fontSize=9,
        leading=12,
        leftIndent=10,
        textColor=colors.HexColor("#334155"),
        backColor=colors.HexColor("#F8FAFC"),
        spaceBefore=5,
        spaceAfter=8,
    ))

    story = []
    lines = markdown.splitlines()
    title = ""
    paragraph = []
    bullets = []
    code_lines = []
    in_code = False

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            story.append(Paragraph(clean_inline(" ".join(paragraph)), styles["Body"]))
            paragraph = []

    def flush_bullets():
        nonlocal bullets
        if bullets:
            items = [
                ListItem(Paragraph(clean_inline(item), styles["PaperBullet"]), bulletColor=colors.HexColor("#2563EB"))
                for item in bullets
            ]
            story.append(ListFlowable(items, bulletType="bullet", start="circle", leftIndent=18))
            story.append(Spacer(1, 5))
            bullets = []

    def flush_code():
        nonlocal code_lines
        if code_lines:
            story.append(Paragraph("<br/>".join(clean_inline(line) for line in code_lines), styles["CodeBlock"]))
            code_lines = []

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                flush_paragraph()
                flush_bullets()
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            flush_paragraph()
            flush_bullets()
            continue

        if line.startswith("# "):
            flush_paragraph()
            flush_bullets()
            title = line[2:].strip()
            story.append(Paragraph(clean_inline(title), styles["PaperTitle"]))
            story.append(Paragraph(
                "Draft manuscript prepared for ResearchGate-style sharing",
                styles["AuthorLine"],
            ))
            story.append(Spacer(1, 0.2 * inch))
            continue

        if line.startswith("## "):
            flush_paragraph()
            flush_bullets()
            heading = line[3:].strip()
            if heading in {"1. Introduction", "References"}:
                story.append(PageBreak())
            story.append(Paragraph(clean_inline(heading), styles["H1"]))
            continue

        if line.startswith("### "):
            flush_paragraph()
            flush_bullets()
            story.append(Paragraph(clean_inline(line[4:].strip()), styles["H2"]))
            continue

        if line.startswith("- "):
            flush_paragraph()
            bullets.append(line[2:].strip())
            continue

        if re.match(r"^\d+\.\s+", line):
            flush_paragraph()
            bullets.append(line)
            continue

        if line.startswith("->") or "->" in line:
            flush_paragraph()
            flush_bullets()
            story.append(Paragraph(clean_inline(line), styles["CodeBlock"]))
            continue

        paragraph.append(line)

    flush_paragraph()
    flush_bullets()
    flush_code()
    return story


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawString(0.75 * inch, 0.45 * inch, "OmniAgentAI Research Paper")
    canvas.drawRightString(7.75 * inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def main():
    markdown = SOURCE.read_text(encoding="utf-8")
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="OmniAgentAI Research Paper",
        author="OmniAgentAI",
        subject="Multi-agent agentic RAG architecture",
    )
    doc.build(build_story(markdown), onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    main()

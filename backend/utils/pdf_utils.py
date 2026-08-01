"""PDF生成工具"""

from typing import List, Dict, Any
import os


def generate_test_pdf(
    questions: List[Dict[str, Any]],
    output_path: str,
    title: str = "数学试卷",
    show_answer: bool = False,
) -> str:
    """生成试卷PDF"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        raise ImportError("请安装 reportlab: pip install reportlab")

    from backend.config import settings
    font_path = settings.FONT_PATH
    font_name = "Helvetica"
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont("Chinese", font_path))
            font_name = "Chinese"
        except Exception:
            pass

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("CustomTitle", parent=styles["Title"], fontName=font_name, fontSize=18, spaceAfter=20)
    question_style = ParagraphStyle("Question", parent=styles["Normal"], fontName=font_name, fontSize=11, leading=16, spaceBefore=10, spaceAfter=5)
    answer_style = ParagraphStyle("Answer", parent=styles["Normal"], fontName=font_name, fontSize=10, textColor=colors.grey, spaceBefore=5)

    story = [Paragraph(title, title_style), Spacer(1, 10)]
    for i, q in enumerate(questions, 1):
        content = q.get("content", "").replace("\n", "<br/>")
        story.append(Paragraph(f"{i}. {content}", question_style))
        if show_answer:
            if q.get("answer"):
                story.append(Paragraph(f"答案：{q['answer']}", answer_style))
            if q.get("analysis"):
                story.append(Paragraph(f"解析：{q['analysis']}", answer_style))
        story.append(Spacer(1, 5))

    doc.build(story)
    return output_path

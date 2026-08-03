"""PDF生成工具"""

from typing import List, Dict, Any, Optional
import os
import re


def _render_latex_to_image(latex_str: str, output_dir: str) -> str:
    """尝试用 matplotlib 将 LaTeX 渲染为图片，返回图片路径"""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib import mathtext
        import hashlib

        # 生成唯一文件名
        md5 = hashlib.md5(latex_str.encode()).hexdigest()[:8]
        img_path = os.path.join(output_dir, f"latex_{md5}.png")

        if os.path.exists(img_path):
            return img_path

        # 替换 matplotlib 不支持的 LaTeX 命令
        rendered = latex_str
        rendered = rendered.replace(r'\le', r'\leq')
        rendered = rendered.replace(r'\ge', r'\geq')

        fig = plt.figure(figsize=(0.01, 0.01))
        fig.patch.set_alpha(0)
        text = fig.text(0, 0, f"${rendered}$", fontsize=12, color='black')
        fig.savefig(img_path, dpi=150, bbox_inches='tight', pad_inches=0.02, transparent=True)
        plt.close(fig)

        return img_path
    except Exception:
        return ""


def _parse_answer_analysis(answer_analysis: str) -> tuple:
    """解析 answer_analysis 字段，返回 (答案, 解析)"""
    if not answer_analysis:
        return "", ""
    if "---解析---" in answer_analysis:
        parts = answer_analysis.split("---解析---", 1)
        return parts[0].strip(), parts[1].strip()
    return answer_analysis.strip(), ""


def _escape_for_reportlab(text: str) -> str:
    """转义 ReportLab XML 解析器不支持的字符"""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def _process_latex_in_text(text: str, latex_dir: str) -> str:
    """处理文本中的 LaTeX 公式，将 $...$ 转换为可显示的格式"""
    if not text:
        return ""

    # 修复双反斜杠：\\\\times -> \\times
    text = re.sub(r'\\\\([a-zA-Z]+)', r'\\\1', text)

    # 先处理图片引用 __IMAGE__...__END_IMAGE__
    image_parts = []
    def save_image_placeholder(match):
        image_parts.append(match.group(0))
        return f"__IMG_PLACEHOLDER_{len(image_parts)-1}__"
    text = re.sub(r'__IMAGE__.*?__END_IMAGE__', save_image_placeholder, text)

    # 转义 HTML 特殊字符（在处理 LaTeX 之前）
    text = _escape_for_reportlab(text)

    # 恢复图片占位符
    for idx, part in enumerate(image_parts):
        text = text.replace(f"__IMG_PLACEHOLDER_{idx}__", part)

    # 替换换行符
    text = text.replace("\n", "<br/>")

    # 处理 $$...$$ 块级公式
    def replace_block(match):
        latex = match.group(1).strip()
        img_path = _render_latex_to_image(latex, latex_dir)
        if img_path and os.path.exists(img_path):
            return f'<img src="{img_path}" height="20"/>'
        return f'<i>{latex}</i>'

    text = re.sub(r'\$\$(.*?)\$\$', replace_block, text, flags=re.DOTALL)

    # 处理 $...$ 行内公式（支持嵌套花括号）
    def replace_inline(match):
        latex = match.group(1).strip()
        img_path = _render_latex_to_image(latex, latex_dir)
        if img_path and os.path.exists(img_path):
            return f'<img src="{img_path}" height="16"/>'
        return f'<i>{latex}</i>'

    # 使用更宽松的匹配：$ 后跟任意内容直到下一个 $（不跨行）
    result = []
    i = 0
    while i < len(text):
        if text[i] == '$':
            # 找到结束的 $
            j = i + 1
            while j < len(text) and text[j] != '$' and text[j] != '<br/>':
                j += 1
            if j < len(text) and text[j] == '$':
                latex = text[i+1:j].strip()
                if latex:
                    img_path = _render_latex_to_image(latex, latex_dir)
                    if img_path and os.path.exists(img_path):
                        result.append(f'<img src="{img_path}" height="16"/>')
                    else:
                        result.append(f'<i>{latex}</i>')
                i = j + 1
            else:
                result.append(text[i])
                i += 1
        else:
            result.append(text[i])
            i += 1

    return ''.join(result)


def generate_test_pdf(
    questions: List[Dict[str, Any]],
    output_path: str,
    title: str = "数学试卷",
    show_answer: bool = False,
    question_scores: Optional[Dict[int, int]] = None,
) -> str:
    """生成试卷PDF"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
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

    # 创建临时目录用于 LaTeX 图片
    latex_dir = os.path.join(os.path.dirname(output_path), "latex_tmp")
    os.makedirs(latex_dir, exist_ok=True)

    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()

    # 样式定义
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Title"],
        fontName=font_name, fontSize=20, spaceAfter=6, alignment=1
    )
    meta_style = ParagraphStyle(
        "Meta", parent=styles["Normal"],
        fontName=font_name, fontSize=11, alignment=1, textColor=colors.HexColor("#666666"), spaceAfter=16
    )
    question_style = ParagraphStyle(
        "Question", parent=styles["Normal"],
        fontName=font_name, fontSize=12, leading=18, spaceBefore=12, spaceAfter=4
    )
    score_style = ParagraphStyle(
        "Score", parent=styles["Normal"],
        fontName=font_name, fontSize=10, textColor=colors.HexColor("#888888"), spaceBefore=0, spaceAfter=8
    )
    answer_style = ParagraphStyle(
        "Answer", parent=styles["Normal"],
        fontName=font_name, fontSize=10, textColor=colors.HexColor("#333333"),
        spaceBefore=6, spaceAfter=4, leftIndent=20
    )
    answer_analysis_style = ParagraphStyle(
        "AnswerAnalysis", parent=styles["Normal"],
        fontName=font_name, fontSize=10, textColor=colors.HexColor("#555555"),
        spaceBefore=4, spaceAfter=8, leftIndent=20, backColor=colors.HexColor("#f5f5f5")
    )
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontName=font_name, fontSize=10, alignment=1, textColor=colors.HexColor("#999999"), spaceBefore=20
    )

    # 计算总分
    if question_scores:
        total_score = sum(question_scores.values())
    else:
        total_score = len(questions) * 10  # 默认每题10分

    story = []

    # 试卷标题
    story.append(Paragraph(title, title_style))

    # 元信息
    grade = questions[0].get("grade", "") if questions else ""
    meta_text = f"年级：{grade}　　时间：90分钟　　总分：{total_score}分"
    story.append(Paragraph(meta_text, meta_style))

    # 分割线
    story.append(Spacer(1, 4))

    # 题目
    for i, q in enumerate(questions, 1):
        q_id = q.get("id", i)
        content = q.get("content", "")
        images = q.get("images", "[]")

        # 解析images JSON字符串
        import json
        try:
            images_list = json.loads(images) if isinstance(images, str) else images
        except:
            images_list = []

        # 处理内容中的图片引用 {{img:N}}
        content_html = _process_content_with_images(content, images_list, latex_dir)

        # 获取该题的分值
        score = question_scores.get(q_id, 10) if question_scores else 10

        story.append(Paragraph(f"<b>{i}.</b> {content_html}", question_style))
        story.append(Paragraph(f"（{score}分）", score_style))

        # 答题区域（空白行）
        if not show_answer:
            story.append(Spacer(1, 24))

        # 答案与解析
        if show_answer:
            answer_analysis = q.get("answer_analysis", "")
            answer, analysis = _parse_answer_analysis(answer_analysis)
            if answer:
                story.append(Paragraph(f"<b>答案：</b>{answer}", answer_style))
            if analysis:
                analysis_processed = _process_latex_in_text(analysis, latex_dir)
                story.append(Paragraph(f"<b>解析：</b>{analysis_processed}", answer_analysis_style))

        story.append(Spacer(1, 8))

    # 试卷底部
    story.append(Spacer(1, 20))
    story.append(Paragraph("— 试卷结束 —", footer_style))

    doc.build(story)
    return output_path


def _process_content_with_images(content: str, images: List[str], latex_dir: str) -> str:
    """处理内容中的图片引用和LaTeX公式"""
    import re
    import urllib.request

    if not content:
        return ""

    # 修复双反斜杠
    content = re.sub(r'\\\\([a-zA-Z]+)', r'\\\1', content)

    # 处理图片引用 {{img:N}}
    def replace_image(match):
        img_index = int(match.group(1))
        if img_index < len(images):
            img_url = images[img_index]
            # 下载图片到临时目录
            try:
                img_filename = f"img_{img_index}_{hash(img_url) % 10000}.png"
                img_path = os.path.join(latex_dir, img_filename)
                if not os.path.exists(img_path):
                    # 处理相对路径
                    if img_url.startswith("uploads/"):
                        from backend.config import settings
                        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        full_path = os.path.join(base_dir, img_url)
                        if os.path.exists(full_path):
                            import shutil
                            shutil.copy(full_path, img_path)
                        else:
                            return f"[图片{img_index + 1}]"
                    else:
                        urllib.request.urlretrieve(img_url, img_path)
                # 返回图片占位符，后面会用reportlab的Image处理
                return f"__IMAGE__{img_path}__END_IMAGE__"
            except Exception as e:
                print(f"[PDF] Image download error: {e}")
                return f"[图片{img_index + 1}]"
        return f"[图片{img_index + 1}]"

    content = re.sub(r'\{\{img:(\d+)\}\}', replace_image, content)

    # 处理LaTeX公式
    content = _process_latex_in_text(content, latex_dir)

    return content

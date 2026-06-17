"""
PDF 工具模块
- 读取 PDF 并转换为图片预览
- 生成试卷 PDF（支持 LaTeX 渲染）
"""

import os
import sys
import io
import logging
import fitz  # PyMuPDF
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT

logger = logging.getLogger(__name__)


def get_font_paths():
    """获取字体搜索路径列表（跨平台）"""
    paths = []

    # 1. 从环境变量获取
    env_font = os.environ.get('FONT_PATH')
    if env_font:
        paths.append(env_font)

    # 2. 根据操作系统添加常见路径
    if sys.platform == 'win32':
        # Windows
        font_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
        paths.extend([
            os.path.join(font_dir, 'msyh.ttc'),    # 微软雅黑
            os.path.join(font_dir, 'simhei.ttf'),   # 黑体
            os.path.join(font_dir, 'simsun.ttc'),   # 宋体
        ])
    elif sys.platform == 'darwin':
        # macOS
        paths.extend([
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/Library/Fonts/Arial Unicode.ttf',
        ])
    else:
        # Linux
        paths.extend([
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
        ])

    return paths


def register_chinese_font():
    """注册中文字体，优先使用系统字体"""
    font_paths = get_font_paths()

    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("ChineseFont", path))
                logger.info(f"Registered Chinese font: {path}")
                return "ChineseFont"
            except Exception as e:
                logger.warning(f"Failed to register font {path}: {str(e)}")
                continue

    logger.warning("No Chinese font found. Using Helvetica fallback.")
    return "Helvetica"


def pdf_to_images(pdf_path, output_dir, dpi=150):
    """将 PDF 每页转换为图片，返回图片路径列表"""
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    image_paths = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        img_path = os.path.join(output_dir, f"page_{page_num + 1}.png")
        pix.save(img_path)
        image_paths.append(img_path)

    doc.close()
    return image_paths


def pdf_page_count(pdf_path):
    """获取 PDF 页数"""
    doc = fitz.open(pdf_path)
    count = len(doc)
    doc.close()
    return count


def generate_test_pdf(questions, output_path, title="数学试卷"):
    """
    生成试卷 PDF
    questions: 题目列表，每项包含 title, content, image_path 等
    """
    font_name = register_chinese_font()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=18,
        spaceAfter=20,
    )
    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=11,
        leading=16,
        spaceAfter=10,
    )
    answer_style = ParagraphStyle(
        "AnswerBody",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor="#666666",
    )

    story = []

    # 标题
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 10 * mm))

    # 题目
    for i, q in enumerate(questions, 1):
        q_text = q.get("title", "") or q.get("content", "") or "（见图片）"
        story.append(Paragraph(f"{i}. {q_text}", body_style))

        # 如果有图片，嵌入
        img_path = q.get("image_path", "")
        if img_path:
            full_path = os.path.join(os.path.dirname(__file__), "static", img_path)
            if os.path.exists(full_path):
                try:
                    img = RLImage(full_path)
                    max_width = 150 * mm
                    if img.drawWidth > max_width:
                        ratio = max_width / img.drawWidth
                        img.drawWidth = max_width
                        img.drawHeight *= ratio
                    story.append(img)
                    story.append(Spacer(1, 5 * mm))
                except Exception:
                    pass

        story.append(Spacer(1, 3 * mm))

    # 答案部分
    story.append(Spacer(1, 15 * mm))
    story.append(Paragraph("参考答案", title_style))
    story.append(Spacer(1, 5 * mm))

    for i, q in enumerate(questions, 1):
        answer = q.get("answer", "暂无答案")
        story.append(Paragraph(f"{i}. {answer}", answer_style))

    doc.build(story)
    return output_path

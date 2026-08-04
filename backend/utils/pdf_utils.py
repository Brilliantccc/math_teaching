"""PDF生成工具 - 使用HTML + Playwright方案"""

from typing import List, Dict, Any, Optional
import os
import re
import hashlib
import shutil
import threading
import asyncio

# LaTeX渲染缓存目录（全局共享）
_LATEX_CACHE_DIR = None
_LATEX_CACHE_LOCK = threading.Lock()


def _get_latex_cache_dir() -> str:
    """获取LaTeX缓存目录"""
    global _LATEX_CACHE_DIR
    if _LATEX_CACHE_DIR is None:
        with _LATEX_CACHE_LOCK:
            if _LATEX_CACHE_DIR is None:
                from backend.config import settings
                _LATEX_CACHE_DIR = os.path.join(
                    os.path.dirname(settings.UPLOAD_DIR),
                    "latex_cache"
                )
                os.makedirs(_LATEX_CACHE_DIR, exist_ok=True)
    return _LATEX_CACHE_DIR


def _get_latex_hash(latex_str: str) -> str:
    """计算LaTeX公式的哈希值"""
    normalized = latex_str.strip().replace(" ", "")
    return hashlib.md5(normalized.encode()).hexdigest()[:12]


def _render_latex_to_image(latex_str: str, output_dir: str, fontsize: int = 14) -> str:
    """用 matplotlib 将 LaTeX 渲染为图片，返回图片路径（带缓存）"""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        formula_hash = _get_latex_hash(latex_str)
        cache_dir = _get_latex_cache_dir()
        cache_path = os.path.join(cache_dir, f"latex_{formula_hash}.png")

        # 检查全局缓存
        if os.path.exists(cache_path):
            local_path = os.path.join(output_dir, f"latex_{formula_hash}.png")
            if not os.path.exists(local_path):
                shutil.copy2(cache_path, local_path)
            return local_path

        # 替换 matplotlib 不支持的 LaTeX 命令
        rendered = latex_str
        rendered = rendered.replace(r'\le', r'\leq')
        rendered = rendered.replace(r'\ge', r'\geq')
        rendered = rendered.replace(r'\dfrac', r'\frac')
        rendered = rendered.replace(r'\cfrac', r'\frac')
        rendered = rendered.replace(r'\bmatrix', r'\begin{matrix}')
        rendered = rendered.replace(r'\pmatrix', r'\begin{pmatrix}')
        rendered = rendered.replace(r'\vmatrix', r'\begin{vmatrix}')
        rendered = rendered.replace(r'\cases', r'\begin{cases}')
        rendered = rendered.replace(r'\aligned', r'\begin{aligned}')

        fig = plt.figure(figsize=(0.01, 0.01))
        fig.patch.set_alpha(0)
        fig.text(0, 0, f"${rendered}$", fontsize=fontsize, color='black')

        local_path = os.path.join(output_dir, f"latex_{formula_hash}.png")
        fig.savefig(local_path, dpi=200, bbox_inches='tight', pad_inches=0.05, transparent=True)
        plt.close(fig)

        try:
            shutil.copy2(local_path, cache_path)
        except Exception:
            pass

        return local_path
    except Exception as e:
        print(f"[PDF] LaTeX render error: {e}")
        import traceback
        traceback.print_exc()
        return ""


def clear_latex_cache():
    """清理LaTeX缓存"""
    global _LATEX_CACHE_DIR
    if _LATEX_CACHE_DIR and os.path.exists(_LATEX_CACHE_DIR):
        shutil.rmtree(_LATEX_CACHE_DIR)
        _LATEX_CACHE_DIR = None
        print("[PDF] LaTeX cache cleared")


def get_latex_cache_stats() -> Dict[str, Any]:
    """获取LaTeX缓存统计"""
    cache_dir = _get_latex_cache_dir()
    if not os.path.exists(cache_dir):
        return {"count": 0, "size_mb": 0}

    files = [f for f in os.listdir(cache_dir) if f.endswith('.png')]
    total_size = sum(
        os.path.getsize(os.path.join(cache_dir, f))
        for f in files
    )
    return {
        "count": len(files),
        "size_mb": round(total_size / 1024 / 1024, 2),
        "cache_dir": cache_dir
    }


def _html_to_pdf(html_content: str, output_path: str, latex_dir: str = None) -> bool:
    """使用Playwright将HTML转换为PDF

    Args:
        html_content: HTML内容
        output_path: 输出PDF路径
        latex_dir: LaTeX图片临时目录（用于清理）

    Returns:
        是否成功
    """
    temp_html_path = None
    try:
        from playwright.sync_api import sync_playwright

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 创建临时HTML文件
        temp_html_path = output_path.replace('.pdf', '_temp.html')
        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        with sync_playwright() as p:
            # 启动浏览器
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # 加载HTML文件
            page.goto(f'file:///{temp_html_path.replace(os.sep, "/")}')

            # 直接生成PDF（LaTeX已在HTML中预渲染为图片，无需等待）
            page.pdf(
                path=output_path,
                format='A4',
                margin={
                    'top': '20mm',
                    'bottom': '20mm',
                    'left': '22mm',
                    'right': '22mm'
                },
                print_background=True
            )

            browser.close()

        print(f"[PDF] Successfully generated: {output_path}")
        return True

    except Exception as e:
        print(f"[PDF] Error generating PDF with Playwright: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理临时文件
        if temp_html_path and os.path.exists(temp_html_path):
            os.remove(temp_html_path)
        if latex_dir and os.path.exists(latex_dir):
            try:
                shutil.rmtree(latex_dir, ignore_errors=True)
            except Exception:
                pass


def _parse_answer_analysis(answer_analysis: str) -> tuple:
    """解析 answer_analysis 字段，返回 (答案, 解析)"""
    if not answer_analysis:
        return "", ""
    if "---解析---" in answer_analysis:
        parts = answer_analysis.split("---解析---", 1)
        return parts[0].strip(), parts[1].strip()
    return answer_analysis.strip(), ""


def _escape_for_reportlab(text: str) -> str:
    """转义 ReportLab XML 解析器不支持的字符（仅用于非公式文本）"""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def _process_latex_in_text(text: str, latex_dir: str) -> str:
    """处理文本中的 LaTeX 公式，将 $...$ 转换为可显示的图片"""
    if not text:
        return ""

    # 第一步：用占位符提取所有 LaTeX 公式，避免后续处理干扰
    formulas = []

    def extract_block_formula(match):
        idx = len(formulas)
        formulas.append(('block', match.group(1).strip()))
        return f"__LATEX_PH_{idx}__"

    def extract_inline_formula(match):
        idx = len(formulas)
        formulas.append(('inline', match.group(1).strip()))
        return f"__LATEX_PH_{idx}__"

    # 提取 $$...$$ 块级公式
    text = re.sub(r'\$\$(.+?)\$\$', extract_block_formula, text, flags=re.DOTALL)

    # 提取 $...$ 行内公式（非贪婪匹配，不跨越行）
    text = re.sub(r'\$([^$\n]+?)\$', extract_inline_formula, text)

    # 第二步：转义 HTML 特殊字符（公式已被占位符保护）
    text = _escape_for_reportlab(text)

    # 第三步：替换换行符
    text = text.replace("\n", "<br/>")

    # 第四步：将占位符替换为渲染后的图片
    for idx, (fmt_type, latex) in enumerate(formulas):
        if fmt_type == 'block':
            img_path = _render_latex_to_image(latex, latex_dir, fontsize=16)
            if img_path and os.path.exists(img_path):
                replacement = f'<img src="{img_path}" height="32"/>'
            else:
                replacement = f'<i>{_escape_for_reportlab(latex)}</i>'
        else:
            img_path = _render_latex_to_image(latex, latex_dir, fontsize=14)
            if img_path and os.path.exists(img_path):
                replacement = f'<img src="{img_path}" height="24"/>'
            else:
                replacement = f'<i>{_escape_for_reportlab(latex)}</i>'
        text = text.replace(f"__LATEX_PH_{idx}__", replacement)

    return text


def generate_test_pdf(
    questions: List[Dict[str, Any]],
    output_path: str,
    title: str = "数学试卷",
    show_answer: bool = False,
    question_scores: Optional[Dict[int, int]] = None,
    style_config=None,
) -> str:
    """生成试卷PDF - 使用HTML + Playwright方案

    Args:
        questions: 题目列表
        output_path: 输出路径
        title: 试卷标题
        show_answer: 是否显示答案（向后兼容）
        question_scores: 每题分值
        style_config: PDFStyleConfig样式配置对象
    """
    latex_dir = None
    try:
        # 获取样式配置
        if style_config is None:
            from backend.utils.pdf_templates import get_template
            style_config = get_template("standard")

        # 向后兼容：如果传入show_answer参数，覆盖配置
        if show_answer:
            style_config.show_answer = True
            style_config.show_analysis = True

        # 使用HTML模板生成HTML（LaTeX已预渲染为图片）
        from backend.utils.html_template import generate_test_html

        html_content, latex_dir = generate_test_html(
            questions=questions,
            title=title,
            show_answer=show_answer,
            question_scores=question_scores,
            style_config=style_config
        )

        # 使用Playwright将HTML转换为PDF
        success = _html_to_pdf(html_content, output_path, latex_dir)
        latex_dir = None  # _html_to_pdf会清理

        if not success:
            # 如果Playwright失败，使用reportlab作为备选
            print("[PDF] Playwright failed, falling back to reportlab")
            return _generate_pdf_with_reportlab(
                questions, output_path, title, show_answer, question_scores, style_config
            )

        return output_path
    except Exception as e:
        print(f"[PDF] Error in generate_test_pdf: {e}")
        import traceback
        traceback.print_exc()
        # 清理临时目录
        if latex_dir and os.path.exists(latex_dir):
            try:
                shutil.rmtree(latex_dir, ignore_errors=True)
            except Exception:
                pass
        raise


def _generate_pdf_with_reportlab(
    questions: List[Dict[str, Any]],
    output_path: str,
    title: str = "数学试卷",
    show_answer: bool = False,
    question_scores: Optional[Dict[int, int]] = None,
    style_config=None,
) -> str:
    """使用reportlab生成PDF（备选方案）"""
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

    # 获取样式配置
    if style_config is None:
        from backend.utils.pdf_templates import get_template
        style_config = get_template("standard")

    # 向后兼容：如果传入show_answer参数，覆盖配置
    if show_answer:
        style_config.show_answer = True
        style_config.show_analysis = True

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

    # 创建临时目录用于 LaTeX 图片和题目图片
    latex_dir = os.path.join(os.path.dirname(output_path), "latex_tmp")
    os.makedirs(latex_dir, exist_ok=True)

    # 页面尺寸和边距
    page_sizes = {"A4": A4}
    page_size = page_sizes.get(style_config.page_size, A4)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=page_size,
        topMargin=style_config.margin_top * mm,
        bottomMargin=style_config.margin_bottom * mm,
        leftMargin=style_config.margin_left * mm,
        rightMargin=style_config.margin_right * mm,
    )
    styles = getSampleStyleSheet()

    # 根据配置创建样式
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Title"],
        fontName=font_name,
        fontSize=style_config.title_font_size,
        textColor=colors.HexColor(style_config.title_color),
        spaceAfter=4,
        alignment=1 if style_config.title_align == "center" else 0
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontName=font_name,
        fontSize=style_config.subtitle_font_size,
        alignment=1,
        textColor=colors.HexColor(style_config.subtitle_color),
        spaceAfter=8
    )
    info_style = ParagraphStyle(
        "Info", parent=styles["Normal"],
        fontName=font_name,
        fontSize=style_config.info_font_size,
        alignment=style_config.info_align == "center" and 1 or 0,
        textColor=colors.HexColor(style_config.info_color),
        spaceAfter=8
    )
    meta_style = ParagraphStyle(
        "Meta", parent=styles["Normal"],
        fontName=font_name,
        fontSize=style_config.subtitle_font_size,
        alignment=1,
        textColor=colors.HexColor(style_config.subtitle_color),
        spaceAfter=16
    )
    question_style = ParagraphStyle(
        "Question", parent=styles["Normal"],
        fontName=font_name,
        fontSize=style_config.question_font_size,
        leading=style_config.question_font_size * style_config.question_line_height,
        spaceBefore=style_config.question_spacing,
        spaceAfter=2
    )
    score_style = ParagraphStyle(
        "Score", parent=styles["Normal"],
        fontName=font_name,
        fontSize=style_config.score_font_size,
        textColor=colors.HexColor(style_config.score_color),
        spaceBefore=0,
        spaceAfter=8
    )
    answer_style = ParagraphStyle(
        "Answer", parent=styles["Normal"],
        fontName=font_name,
        fontSize=style_config.answer_font_size,
        textColor=colors.HexColor(style_config.answer_color),
        spaceBefore=6, spaceAfter=4, leftIndent=20
    )
    answer_analysis_style = ParagraphStyle(
        "AnswerAnalysis", parent=styles["Normal"],
        fontName=font_name,
        fontSize=style_config.answer_font_size,
        textColor=colors.HexColor("#555555"),
        spaceBefore=4, spaceAfter=8, leftIndent=20,
        backColor=colors.HexColor("#f5f5f5")
    )
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontName=font_name,
        fontSize=style_config.footer_font_size,
        alignment=1,
        textColor=colors.HexColor("#999999"),
        spaceBefore=20
    )

    # 题型分组标题样式
    section_style = ParagraphStyle(
        "Section", parent=styles["Normal"],
        fontName=font_name,
        fontSize=style_config.section_font_size,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.HexColor(style_config.section_color)
    )

    # 题型描述样式
    section_desc_style = ParagraphStyle(
        "SectionDesc", parent=styles["Normal"],
        fontName=font_name,
        fontSize=style_config.section_desc_font_size,
        textColor=colors.HexColor("#666666")
    )

    # 计算总分和题型统计
    if question_scores:
        total_score = sum(question_scores.values())
    else:
        total_score = len(questions) * 10  # 默认每题10分

    # 统计各题型数量和分值
    section_stats = {}
    for q in questions:
        category = q.get("category", "其他")
        if category not in section_stats:
            section_stats[category] = {"count": 0, "score": 0}
        section_stats[category]["count"] += 1
        q_id = q.get("id")
        section_stats[category]["score"] += question_scores.get(q_id, 10) if question_scores else 10

    story = []

    # 试卷标题
    story.append(Paragraph(title, title_style))

    # 副标题（科目）
    if style_config.show_subtitle:
        subject = questions[0].get("subject", "数学") if questions else "数学"
        story.append(Paragraph(f"数学科目 {subject}", subtitle_style))

    # 考生信息
    if style_config.show_exam_info:
        grade = questions[0].get("grade", "") if questions else ""
        total_questions = len(questions)
        info_text = style_config.exam_info_text or f"考生注意：本试卷共{total_questions}道小题，满分{total_score}分，时量120分钟"
        story.append(Paragraph(info_text, info_style))

    # 分割线
    story.append(Spacer(1, style_config.title_spacing))

    # 题型分组标题映射
    section_names = {
        "选择题": "一、单项选择题",
        "单选题": "一、单项选择题",
        "填空题": "二、填空题",
        "解答题": "三、解答题",
        "判断题": "四、判断题",
        "计算题": "五、计算题",
        "应用题": "六、应用题",
    }

    # 按题型分组（如果启用）
    if style_config.group_by_type:
        from collections import defaultdict
        grouped = defaultdict(list)
        for i, q in enumerate(questions):
            category = q.get("category", "其他")
            grouped[category].append((i, q))

        question_index = 1
        section_num = 1
        for category, items in grouped.items():
            # 添加题型标题
            section_title = section_names.get(category, f"{_to_chinese_num(section_num)}、{category}")

            # 添加题型描述
            if style_config.show_section_desc and category in section_stats:
                stats = section_stats[category]
                section_desc = f"（本大题共{stats['count']}个小题，共{stats['score']}分）"
                section_full = f"{section_title}{section_desc}"
                story.append(Paragraph(f"<b>{section_full}</b>", section_style))
            elif style_config.show_section_header:
                story.append(Paragraph(f"<b>{section_title}</b>", section_style))

            section_num += 1

            for original_idx, q in items:
                q_id = q.get("id", original_idx + 1)
                content = q.get("content", "")
                images = q.get("images", "[]")

                import json
                try:
                    images_list = json.loads(images) if isinstance(images, str) else images
                except Exception:
                    images_list = []

                content_html = _process_content_with_images(content, images_list, latex_dir)
                score = question_scores.get(q_id, 10) if question_scores else 10

                # 构建题目内容（带答案括号）
                question_text = f"{question_index}. {content_html}"
                if style_config.show_answer_bracket and style_config.answer_bracket_position == "right":
                    question_text += "　　　　(　　)"

                story.append(Paragraph(question_text, question_style))

                # 分值显示
                if style_config.score_position != "inline":
                    story.append(Paragraph(f"（{score}分）", score_style))

                # 答题区域
                _add_answer_space(story, style_config, q.get("category"))

                # 答案与解析
                _add_answer_and_analysis(story, q, style_config, latex_dir, answer_style, answer_analysis_style)

                question_index += 1
    else:
        # 不分组，直接输出所有题目
        for i, q in enumerate(questions, 1):
            q_id = q.get("id", i)
            content = q.get("content", "")
            images = q.get("images", "[]")

            import json
            try:
                images_list = json.loads(images) if isinstance(images, str) else images
            except Exception:
                images_list = []

            content_html = _process_content_with_images(content, images_list, latex_dir)
            score = question_scores.get(q_id, 10) if question_scores else 10

            # 构建题目内容
            question_text = f"{i}. {content_html}"
            if style_config.show_answer_bracket and style_config.answer_bracket_position == "right":
                question_text += "　　　　(　　)"

            story.append(Paragraph(question_text, question_style))

            if style_config.score_position != "inline":
                story.append(Paragraph(f"（{score}分）", score_style))

            # 答题区域
            _add_answer_space(story, style_config, q.get("category"))

            # 答案与解析
            _add_answer_and_analysis(story, q, style_config, latex_dir, answer_style, answer_analysis_style)

    # 试卷底部
    story.append(Spacer(1, 20))
    story.append(Paragraph("— 试卷结束 —", footer_style))

    doc.build(story)
    return output_path


def _to_chinese_num(num: int) -> str:
    """数字转中文序号"""
    chinese_nums = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    if 1 <= num <= 10:
        return chinese_nums[num - 1]
    return str(num)


def _add_answer_space(story, style_config, category: str = None):
    """根据配置和题型添加答题区域"""
    from reportlab.platypus import Spacer
    from reportlab.lib.units import mm

    if style_config.answer_space_mode == "none":
        return

    if style_config.answer_space_mode == "fixed":
        space = style_config.answer_space_fixed * mm
        story.append(Spacer(1, space))
        return

    # auto模式：根据题型自动调整
    space_map = {
        "选择题": 15,
        "填空题": 25,
        "解答题": 50,
        "判断题": 15,
        "计算题": 40,
        "应用题": 60,
    }
    space_mm = space_map.get(category, 30)
    story.append(Spacer(1, space_mm * mm))


def _add_answer_and_analysis(
    story, q: Dict, style_config, latex_dir: str,
    answer_style, answer_analysis_style
):
    """添加答案和解析（根据配置）"""
    from reportlab.platypus import Paragraph, Spacer
    from reportlab.lib.units import mm

    if not style_config.show_answer and not style_config.show_analysis:
        story.append(Spacer(1, 8 * mm))
        return

    answer_analysis = q.get("answer_analysis", "")
    answer, analysis = _parse_answer_analysis(answer_analysis)

    if style_config.show_answer and answer:
        answer_processed = _process_latex_in_text(answer, latex_dir)
        story.append(Paragraph(f"<b>答案：</b>{answer_processed}", answer_style))

    if style_config.show_analysis and analysis:
        analysis_processed = _process_latex_in_text(analysis, latex_dir)
        story.append(Paragraph(f"<b>解析：</b>{analysis_processed}", answer_analysis_style))

    if not style_config.show_answer and not style_config.show_analysis:
        story.append(Spacer(1, 8 * mm))


def _process_content_with_images(content: str, images: List[str], latex_dir: str) -> str:
    """处理内容中的图片引用和LaTeX公式"""
    if not content:
        return ""

    # 处理图片引用 {{img:N}} → <img> 标签
    def replace_image(match):
        img_index = int(match.group(1))
        if img_index < len(images):
            img_url = images[img_index]
            try:
                # 使用原始文件扩展名
                ext = os.path.splitext(img_url)[1] or '.png'
                img_filename = f"img_{img_index}_{hash(img_url) % 10000}{ext}"
                img_path = os.path.join(latex_dir, img_filename)
                if not os.path.exists(img_path):
                    if img_url.startswith("uploads/"):
                        from backend.config import settings
                        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        full_path = os.path.join(base_dir, img_url)
                        if os.path.exists(full_path):
                            shutil.copy(full_path, img_path)
                        else:
                            print(f"[PDF] Image file not found: {full_path}")
                            return f"[图片{img_index + 1}]"
                    else:
                        import urllib.request
                        urllib.request.urlretrieve(img_url, img_path)
                # 转换为file://协议的URL
                file_url = "file:///" + img_path.replace("\\", "/")
                return f'<img src="{file_url}" class="question-image"/>'
            except Exception as e:
                print(f"[PDF] Image error: {e}")
                return f"[图片{img_index + 1}]"
        return f"[图片{img_index + 1}]"

    content = re.sub(r'\{\{img:(\d+)\}\}', replace_image, content)

    # 处理LaTeX公式
    content = _process_latex_in_text(content, latex_dir)

    return content

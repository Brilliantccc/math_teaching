"""HTML模板系统 - 用于生成高质量PDF"""

from typing import List, Dict, Any, Optional, Tuple
import os
import re
import json
import tempfile
import shutil


def _escape_html(text: str, preserve_tags: bool = False) -> str:
    """转义HTML特殊字符

    Args:
        text: 要转义的文本
        preserve_tags: 是否保留<img>等HTML标签
    """
    if not text:
        return ""

    # 如果需要保留标签，先提取<img>标签
    img_tags = {}
    if preserve_tags:
        import re
        def extract_img(match):
            placeholder = f"__IMG_TAG_{len(img_tags)}__"
            img_tags[placeholder] = match.group(0)
            return placeholder
        text = re.sub(r'<img\s+[^>]+/>', extract_img, text)

    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')

    # 还原<img>标签
    if preserve_tags:
        for placeholder, img_tag in img_tags.items():
            text = text.replace(placeholder, img_tag)

    return text


def _get_latex_cache_dir() -> str:
    """获取LaTeX缓存目录"""
    from backend.config import settings
    cache_dir = os.path.join(os.path.dirname(settings.UPLOAD_DIR), "latex_cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def _get_latex_hash(latex_str: str) -> str:
    """计算LaTeX公式的哈希值"""
    import hashlib
    normalized = latex_str.strip().replace(" ", "")
    return hashlib.md5(normalized.encode()).hexdigest()[:12]


def _render_latex_to_image(latex_str: str, output_dir: str, fontsize: int = 14) -> str:
    """用matplotlib将LaTeX渲染为图片，返回图片路径（带缓存）"""
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
        # 添加更多常见LaTeX命令支持
        rendered = rendered.replace(r'\square', r'\Box')
        rendered = rendered.replace(r'\parallelogram', r'\square')
        rendered = rendered.replace(r'\degree', r'^\circ')
        rendered = rendered.replace(r'\angle', r'\angle')
        rendered = rendered.replace(r'\because', r'\because')
        rendered = rendered.replace(r'\therefore', r'\therefore')
        rendered = rendered.replace(r'\Rightarrow', r'\Rightarrow')
        rendered = rendered.replace(r'\Leftarrow', r'\Leftarrow')
        rendered = rendered.replace(r'\Leftrightarrow', r'\Leftrightarrow')
        rendered = rendered.replace(r'\cdot', r'\cdot')
        rendered = rendered.replace(r'\times', r'\times')
        rendered = rendered.replace(r'\div', r'\div')
        rendered = rendered.replace(r'\neq', r'\neq')
        rendered = rendered.replace(r'\approx', r'\approx')
        rendered = rendered.replace(r'\equiv', r'\equiv')
        rendered = rendered.replace(r'\pm', r'\pm')
        rendered = rendered.replace(r'\mp', r'\mp')

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
        print(f"[HTML] LaTeX render error: {e}")
        import traceback
        traceback.print_exc()
        return ""


def _preprocess_latex_for_html(text: str, output_dir: str) -> str:
    r"""预处理LaTeX公式，将$...$、$$...$$、\( ... \)、\[ ... \]替换为<img>标签

    Args:
        text: 包含LaTeX公式的文本
        output_dir: 图片输出目录

    Returns:
        替换后的HTML文本
    """
    if not text:
        return ""

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

    # 提取 \[ ... \] 块级公式
    text = re.sub(r'\\\[(.+?)\\\]', extract_block_formula, text, flags=re.DOTALL)

    # 提取 $...$ 行内公式（非贪婪匹配，不跨越行）
    text = re.sub(r'\$([^$\n]+?)\$', extract_inline_formula, text)

    # 提取 \( ... \) 行内公式
    text = re.sub(r'\\\((.+?)\\\)', extract_inline_formula, text)

    # 将占位符替换为渲染后的图片
    for idx, (fmt_type, latex) in enumerate(formulas):
        if fmt_type == 'block':
            img_path = _render_latex_to_image(latex, output_dir, fontsize=16)
            if img_path and os.path.exists(img_path):
                # 使用正斜杠，确保Windows路径兼容
                file_url = "file:///" + img_path.replace("\\", "/")
                replacement = f'<div style="text-align: center; margin: 8px 0;"><img src="{file_url}" style="max-height: 40px;"/></div>'
            else:
                replacement = f'<i>{_escape_html(latex)}</i>'
        else:
            img_path = _render_latex_to_image(latex, output_dir, fontsize=14)
            if img_path and os.path.exists(img_path):
                # 使用正斜杠，确保Windows路径兼容
                file_url = "file:///" + img_path.replace("\\", "/")
                replacement = f'<img src="{file_url}" style="max-height: 24px; vertical-align: middle; margin: 0 2px;"/>'
            else:
                replacement = f'<i>{_escape_html(latex)}</i>'
        text = text.replace(f"__LATEX_PH_{idx}__", replacement)

    return text


def _process_content_html(content: str, images: List[str], output_dir: str = None) -> str:
    """处理题目内容中的图片引用和LaTeX公式

    Args:
        content: 题目内容
        images: 图片列表
        output_dir: LaTeX图片输出目录（如果为None则跳过LaTeX预渲染）

    Returns:
        处理后的HTML内容
    """
    if not content:
        return ""

    # 修复已转义的HTML标签（如 &lt;img → <img）
    content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')

    # 修复 $...$ 公式内部的 \( \) 被KaTeX误解为数学分隔符的问题
    # 只处理 $...$ 和 $$...$$ 公式内部的 \( \)
    def _fix_latex_parens_in_formula(match):
        formula = match.group(0)
        # 数据库中存储的是 \（一个反斜杠）+ 空格 + (
        # 需要替换为普通的 ( 和 )，让KaTeX正常渲染
        import re as re_inner
        # 匹配 \( 或 \ ( ，替换为 (
        formula = re_inner.sub(r'\\\s*\(', '(', formula)
        # 匹配 \) 或 \ ) ，替换为 )
        formula = re_inner.sub(r'\\\s*\)', ')', formula)
        # 修复 < 和 > 被KaTeX误解为HTML标签的问题
        # 在数学模式中，< 和 > 应该被转义为 \lt 和 \gt
        formula = formula.replace('<', '\\lt ')
        formula = formula.replace('>', '\\gt ')
        return formula

    # 只处理 $...$ 和 $$...$$ 公式内部的内容
    content = re.sub(r'\$[^$\n]+?\$', _fix_latex_parens_in_formula, content)
    content = re.sub(r'\$\$[^$]+?\$\$', _fix_latex_parens_in_formula, content, flags=re.DOTALL)

    # 处理图片引用 {{img:N}} → <img> 标签
    def replace_image(match):
        img_index = int(match.group(1))
        if img_index < len(images):
            img_url = images[img_index]
            try:
                # 使用原始文件路径
                if img_url.startswith("uploads/"):
                    from backend.config import settings
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    full_path = os.path.join(base_dir, img_url)
                    if os.path.exists(full_path):
                        # 转换为file://协议的URL
                        file_url = "file:///" + full_path.replace("\\", "/")
                        return f'<img src="{file_url}" class="question-image"/>'
                    else:
                        return f'<span class="image-placeholder">[图片{img_index + 1}]</span>'
                else:
                    return f'<img src="{img_url}" class="question-image"/>'
            except Exception as e:
                print(f"[HTML] Image error: {e}")
                return f'<span class="image-placeholder">[图片{img_index + 1}]</span>'
        return f'<span class="image-placeholder">[图片{img_index + 1}]</span>'

    content = re.sub(r'\{\{img:(\d+)\}\}', replace_image, content)

    # 修复已存在的<img>标签中的Windows路径
    def fix_img_path(match):
        full_match = match.group(0)
        src = match.group(1)
        # 如果是Windows路径（包含反斜杠或冒号），转换为file://协议
        if '\\' in src or (len(src) > 1 and src[1] == ':'):
            file_url = "file:///" + src.replace("\\", "/")
            return full_match.replace(src, file_url)
        return full_match

    content = re.sub(r'<img\s+src="([^"]+)"', fix_img_path, content)

    # KaTeX方案：保留原始LaTeX标记，由浏览器端KaTeX渲染
    # 不再将LaTeX转为图片，保持原始 $...$ 和 $$...$$ 标记

    # 处理选项：将 A. B. C. D. 开头的行包裹在 <div class="options"> 中
    def format_options(text):
        """将选项格式化为块级元素"""
        lines = text.split('\n')
        result_lines = []
        in_options = False

        for line in lines:
            stripped = line.strip()
            # 检查是否是选项行（以 A. B. C. D. 或 A、B、C、D、 开头）
            if re.match(r'^[A-D][.、．]\s*', stripped) or re.match(r'^[A-D]\s*[.、．]\s*', stripped):
                if not in_options:
                    result_lines.append('<div class="options">')
                    in_options = True
                result_lines.append(f'<div class="option">{stripped}</div>')
            else:
                if in_options:
                    result_lines.append('</div>')
                    in_options = False
                result_lines.append(line)

        if in_options:
            result_lines.append('</div>')

        return '\n'.join(result_lines)

    content = format_options(content)

    return content


def _get_katex_base_url() -> str:
    """获取KaTeX本地文件的base URL（file://协议）"""
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    katex_dir = os.path.join(project_root, "static", "vendor", "katex")
    # 转换为file:// URL
    return "file:///" + katex_dir.replace("\\", "/")


def generate_test_html(
    questions: List[Dict[str, Any]],
    title: str = "数学试卷",
    show_answer: bool = False,
    question_scores: Optional[Dict[int, int]] = None,
    style_config=None,
) -> Tuple[str, str]:
    """生成试卷HTML

    Args:
        questions: 题目列表
        title: 试卷标题
        show_answer: 是否显示答案
        question_scores: 每题分值
        style_config: PDFStyleConfig样式配置对象

    Returns:
        Tuple[html_content, latex_dir]: HTML字符串和LaTeX图片临时目录路径
    """
    # 创建临时目录用于LaTeX图片
    latex_dir = tempfile.mkdtemp(prefix='latex_html_')

    # 获取KaTeX本地路径
    katex_base = _get_katex_base_url()

    # 获取样式配置
    if style_config is None:
        from backend.utils.pdf_templates import get_template
        style_config = get_template("standard")

    # 计算总分
    if question_scores:
        total_score = sum(question_scores.values())
    else:
        total_score = len(questions) * 10

    # 统计各题型
    section_stats = {}
    for q in questions:
        question_type = q.get("question_type", "其他")
        if question_type not in section_stats:
            section_stats[question_type] = {"count": 0, "score": 0}
        section_stats[question_type]["count"] += 1
        q_id = q.get("id")
        section_stats[question_type]["score"] += question_scores.get(q_id, 10) if question_scores else 10

    # 题型名称映射
    section_names = {
        "单项选择": "一、单项选择题",
        "多项选择": "二、多项选择题",
        "填空题": "三、填空题",
        "判断题": "四、判断题",
        "计算题": "五、计算题",
        "解答题": "六、解答题",
    }

    # 构建题目HTML
    questions_html = ""
    question_index = 1

    if style_config.group_by_type:
        # 按题型分组，按照指定顺序排列
        from collections import defaultdict, OrderedDict
        grouped = defaultdict(list)
        for q in questions:
            question_type = q.get("question_type", "其他")
            grouped[question_type].append(q)

        # 定义题型顺序：单项选择 → 多项选择 → 填空题 → 判断题 → 计算题 → 解答题 → 其他
        type_order = ["单项选择", "多项选择", "填空题", "判断题", "计算题", "解答题"]
        ordered_grouped = OrderedDict()

        # 先添加定义的题型
        for t in type_order:
            if t in grouped:
                ordered_grouped[t] = grouped[t]

        # 添加其他未定义的题型
        for question_type in grouped:
            if question_type not in ordered_grouped:
                ordered_grouped[question_type] = grouped[question_type]

        grouped = ordered_grouped

        for question_type, items in grouped.items():
            section_title = section_names.get(question_type, question_type)
            stats = section_stats[question_type]

            if style_config.show_section_desc:
                section_desc = f"（本大题共{stats['count']}个小题，共{stats['score']}分）"
                questions_html += f'<div class="section-title">{section_title}{section_desc}</div>\n'
            else:
                questions_html += f'<div class="section-title">{section_title}</div>\n'

            for q in items:
                questions_html += _render_question(q, question_index, style_config, show_answer, question_scores, latex_dir)
                question_index += 1
    else:
        # 不分组
        for q in questions:
            questions_html += _render_question(q, question_index, style_config, show_answer, question_scores, latex_dir)
            question_index += 1

    # 生成完整HTML（使用本地KaTeX文件）
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{_escape_html(title)}</title>

    <!-- KaTeX CSS (本地) -->
    <link rel="stylesheet" href="{katex_base}/dist/katex.min.css">
    <style>
        @page {{
            size: A4;
            margin: {style_config.margin_top}mm {style_config.margin_right}mm {style_config.margin_bottom}mm {style_config.margin_left}mm;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: "Microsoft YaHei", "SimHei", "Helvetica Neue", Arial, sans-serif;
            font-size: {style_config.question_font_size}pt;
            line-height: {style_config.question_line_height};
            color: #333;
            margin: 0;
            padding: 0;
        }}

        /* 标题样式 */
        .title {{
            font-size: {style_config.title_font_size}pt;
            font-weight: bold;
            text-align: center;
            margin-bottom: 8px;
            color: {style_config.title_color};
        }}

        .subtitle {{
            font-size: {style_config.subtitle_font_size}pt;
            text-align: center;
            margin-bottom: 8px;
            color: {style_config.subtitle_color};
        }}

        .exam-info {{
            font-size: {style_config.info_font_size}pt;
            text-align: center;
            color: {style_config.info_color};
            margin-bottom: 16px;
        }}

        /* 分割线 */
        .divider {{
            border-top: 1px solid #333;
            margin: 16px 0;
        }}

        /* 题型标题 */
        .section-title {{
            font-size: {style_config.section_font_size}pt;
            font-weight: bold;
            color: {style_config.section_color};
            margin-top: 20px;
            margin-bottom: 12px;
            page-break-after: avoid;
        }}

        /* 题目样式 */
        .question {{
            margin-bottom: 16px;
            page-break-inside: avoid;
        }}

        .question-number {{
            font-weight: bold;
            margin-right: 4px;
        }}

        .question-content {{
            display: inline;
        }}

        .answer-bracket {{
            float: right;
            color: #666;
        }}

        /* 分值 */
        .score {{
            font-size: {style_config.score_font_size}pt;
            color: {style_config.score_color};
            margin-left: 8px;
        }}

        /* 选项样式 */
        .options {{
            margin-left: 24px;
            margin-top: 8px;
        }}

        .option {{
            margin-bottom: 4px;
        }}

        .option-label {{
            font-weight: bold;
            margin-right: 8px;
        }}

        /* 答题区域 */
        .answer-space {{
            height: {style_config.answer_space_fixed if style_config.answer_space_mode == 'fixed' else 50}mm;
            border-bottom: 1px dashed #ccc;
            margin: 12px 0;
        }}

        /* 答案和解析 */
        .answer {{
            margin-top: 8px;
            padding: 8px 12px;
            background: #f8f9fa;
            border-left: 3px solid #4CAF50;
            font-size: {style_config.answer_font_size}pt;
            color: {style_config.answer_color};
        }}

        .analysis {{
            margin-top: 8px;
            padding: 8px 12px;
            background: #f5f5f5;
            border-left: 3px solid #2196F3;
            font-size: {style_config.answer_font_size}pt;
            color: #555;
        }}

        /* 图片样式 */
        .question-image {{
            max-width: 100%;
            max-height: 200px;
            display: block;
            margin: 8px auto;
        }}

        .image-placeholder {{
            color: #999;
            font-style: italic;
        }}

        /* 页脚 */
        .footer {{
            text-align: center;
            color: #999;
            font-size: 10pt;
            margin-top: 30px;
            padding-top: 10px;
            border-top: 1px solid #eee;
        }}

        /* 打印优化 */
        @media print {{
            body {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            .question {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <h1 class="title">{_escape_html(title)}</h1>

    <div class="subtitle">数学科目 数学</div>

    <div class="exam-info">
        考生注意：本试卷共{len(questions)}道小题，满分{total_score}分，时量120分钟
    </div>

    <div class="divider"></div>

    {questions_html}

    <div class="divider"></div>

    <div class="footer">— 试卷结束 —</div>

    <!-- KaTeX JS (本地) -->
    <script defer src="{katex_base}/dist/katex.min.js"></script>
    <script defer src="{katex_base}/dist/contrib/auto-render.min.js"></script>
    <script>
        // 等待KaTeX加载完成后自动渲染LaTeX公式
        document.addEventListener("DOMContentLoaded", function() {{
            // 渲染行内公式 $...$（仅使用 $ 和 $$ 分隔符，避免与内容中的括号冲突）
            renderMathInElement(document.body, {{
                delimiters: [
                    {{left: "$$", right: "$$", display: true}},
                    {{left: "$", right: "$", display: false}}
                ],
                throwOnError: false
            }});
        }});

        // 如果DOMContentLoaded已经触发，立即执行
        if (document.readyState !== 'loading') {{
            renderMathInElement(document.body, {{
                delimiters: [
                    {{left: "$$", right: "$$", display: true}},
                    {{left: "$", right: "$", display: false}}
                ],
                throwOnError: false
            }});
        }}
    </script>
</body>
</html>"""

    return html, latex_dir


def _render_question(
    q: Dict[str, Any],
    index: int,
    style_config,
    show_answer: bool,
    question_scores: Optional[Dict[int, int]],
    output_dir: str = None
) -> str:
    """渲染单个题目

    Args:
        q: 题目数据
        index: 题号
        style_config: 样式配置
        show_answer: 是否显示答案
        question_scores: 每题分值
        output_dir: LaTeX图片输出目录

    Returns:
        题目HTML字符串
    """
    content = q.get("content", "")
    question_type = q.get("question_type", "")
    images = q.get("images", "[]")

    # 解析图片列表
    try:
        images_list = json.loads(images) if isinstance(images, str) else images
    except Exception:
        images_list = []

    # 处理内容中的图片和LaTeX公式（这会生成包含<img>标签的HTML）
    content_html = _process_content_html(content, images_list, output_dir)

    # 获取分值
    q_id = q.get("id")
    score = question_scores.get(q_id, 10) if question_scores else 10

    # 构建题目HTML
    question_html = f'<div class="question">\n'

    # 题号
    question_html += f'<span class="question-number">{index}.</span>'

    # 分值（放在序号后面）
    if style_config.score_position == "inline":
        question_html += f'<span class="score">（{score}分）</span>'

    # 题目内容（直接插入HTML，不转义）
    question_html += f'<span class="question-content">{content_html}</span>'

    # 答案括号（选择题）
    if style_config.show_answer_bracket and style_config.answer_bracket_position == "right":
        if question_type in ["单项选择", "多项选择"]:
            question_html += '<span class="answer-bracket">(　　)</span>'

    question_html += '\n'

    # 答题区域
    if style_config.answer_space_mode != "none" and not show_answer:
        if question_type in ["填空题", "解答题", "计算题"]:
            space_height = style_config.answer_space_fixed if style_config.answer_space_mode == "fixed" else 50
            question_html += f'<div class="answer-space"></div>\n'

    # 答案和解析（如果显示）
    if show_answer:
        answer_analysis = q.get("answer_analysis", "")
        if answer_analysis:
            answer, analysis = _parse_answer_analysis(answer_analysis)
            if answer:
                # KaTeX方案：保留原始LaTeX标记，由浏览器端KaTeX渲染
                # 不再将LaTeX转为图片，保持原始 $...$ 标记
                question_html += f'<div class="answer"><b>答案：</b>{answer}</div>\n'
            if analysis:
                # KaTeX方案：保留原始LaTeX标记，由浏览器端KaTeX渲染
                # 不再将LaTeX转为图片，保持原始 $...$ 标记
                question_html += f'<div class="analysis"><b>解析：</b>{analysis}</div>\n'

    question_html += '</div>\n'

    return question_html


def _parse_answer_analysis(answer_analysis: str) -> tuple:
    """解析答案和解析"""
    if not answer_analysis:
        return "", ""
    if "---解析---" in answer_analysis:
        parts = answer_analysis.split("---解析---", 1)
        return parts[0].strip(), parts[1].strip()
    return answer_analysis.strip(), ""

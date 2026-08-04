"""PDF试卷模板配置"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class TemplateType(str, Enum):
    """模板类型"""
    STANDARD = "standard"      # 标准试卷
    CONCISE = "concise"        # 简洁版
    DETAILED = "detailed"      # 详解版（含解析）
    PROFESSIONAL = "professional"  # 专业版
    REAL_EXAM = "real_exam"    # 真实试卷（参考真实试卷）


@dataclass
class PDFStyleConfig:
    """PDF样式配置"""

    # 标题样式
    title_font_size: int = 22
    title_color: str = "#000000"
    title_align: str = "center"
    show_title_border: bool = True
    title_spacing: int = 8  # 标题下方间距(mm)

    # 副标题/元信息样式
    subtitle_font_size: int = 14
    subtitle_color: str = "#000000"
    show_subtitle: bool = True  # 是否显示副标题（科目）

    # 考生信息样式
    info_font_size: int = 10
    info_color: str = "#333333"
    info_align: str = "center"
    show_exam_info: bool = True  # 显示"考生注意"信息
    exam_info_text: str = ""  # 自定义考生信息

    # 题型分组样式
    show_section_header: bool = True  # 是否显示题型标题
    section_font_size: int = 12
    section_font_weight: str = "bold"  # bold / normal
    section_color: str = "#000000"
    show_section_desc: bool = True  # 显示题型描述（共X题，每题X分）
    section_desc_font_size: int = 10

    # 题目样式
    question_font_size: int = 11
    question_line_height: float = 1.5
    question_spacing: int = 6  # 题目间距(mm)
    question_number_style: str = "number"  # number / circle

    # 选项样式（选择题）
    option_font_size: int = 11
    option_spacing: int = 20  # 选项间距(mm)
    option_per_line: int = 4  # 每行选项数
    show_answer_bracket: bool = True  # 显示答案括号 ( )
    answer_bracket_position: str = "right"  # right / inline

    # 分值样式
    score_font_size: int = 10
    score_color: str = "#333333"
    score_position: str = "inline"  # inline / separate

    # 填空题样式
    blank_length: int = 30  # 填空下划线长度(mm)

    # 答案样式（详解版）
    answer_font_size: int = 10
    answer_color: str = "#333333"
    show_answer: bool = False
    show_analysis: bool = False

    # 页面设置
    page_size: str = "A4"
    margin_top: int = 20      # mm
    margin_bottom: int = 20
    margin_left: int = 22
    margin_right: int = 22

    # 页眉页脚
    show_header: bool = False
    header_text: str = ""
    header_font_size: int = 10
    show_footer: bool = False
    footer_text: str = ""
    footer_font_size: int = 10
    show_page_number: bool = True

    # 分数栏
    show_score_table: bool = False
    score_table_position: str = "header"  # header / footer

    # 题型分组
    group_by_type: bool = False  # 是否按题型分组

    # 答题区域
    answer_space_mode: str = "auto"  # auto / fixed / none
    answer_space_fixed: int = 50  # mm（fixed模式）
    answer_line_height: int = 8  # 答题线间距(mm)

    # 特殊元素
    show_images: bool = True  # 显示图片
    image_max_width: int = 100  # 图片最大宽度(mm)


# 预设模板配置
TEMPLATES: Dict[str, Dict[str, Any]] = {
    TemplateType.STANDARD: {
        "name": "标准试卷",
        "description": "经典试卷格式，适合日常测试",
        "config": PDFStyleConfig(
            title_font_size=22,
            show_title_border=True,
            show_score_table=True,
            group_by_type=False,
            answer_space_mode="auto",
            show_header=True,
            show_footer=True,
            show_page_number=True,
        )
    },

    TemplateType.CONCISE: {
        "name": "简洁版",
        "description": "紧凑排版，节省纸张",
        "config": PDFStyleConfig(
            title_font_size=18,
            title_spacing=6,
            question_font_size=11,
            question_line_height=1.4,
            question_spacing=4,
            margin_top=15,
            margin_bottom=15,
            margin_left=15,
            margin_right=15,
            show_title_border=False,
            show_score_table=False,
            show_header=False,
            show_exam_info=False,
            group_by_type=False,
            answer_space_mode="fixed",
            answer_space_fixed=25,
        )
    },

    TemplateType.DETAILED: {
        "name": "详解版",
        "description": "包含答案和详细解析",
        "config": PDFStyleConfig(
            title_font_size=22,
            show_title_border=True,
            show_score_table=True,
            show_answer=True,
            show_analysis=True,
            answer_font_size=10,
            answer_color="#333333",
            group_by_type=True,
            show_section_header=True,
            answer_space_mode="none",
            show_header=True,
            show_footer=True,
        )
    },

    TemplateType.PROFESSIONAL: {
        "name": "专业版",
        "description": "正式考试格式，带题型分组",
        "config": PDFStyleConfig(
            title_font_size=24,
            show_title_border=True,
            show_score_table=True,
            group_by_type=True,
            show_section_header=True,
            section_font_size=14,
            question_font_size=12,
            question_line_height=1.6,
            margin_top=30,
            margin_bottom=30,
            show_header=True,
            header_text="机密",
            show_footer=True,
            show_page_number=True,
            answer_space_mode="auto",
        )
    },

    TemplateType.REAL_EXAM: {
        "name": "真实试卷",
        "description": "参考真实试卷排版，适合数学考试",
        "config": PDFStyleConfig(
            # 标题样式 - 参考真实试卷
            title_font_size=22,
            title_align="center",
            title_spacing=4,
            show_title_border=False,

            # 副标题
            subtitle_font_size=16,
            subtitle_color="#000000",
            show_subtitle=True,

            # 考生信息
            info_font_size=10,
            info_color="#333333",
            show_exam_info=True,

            # 题型分组
            group_by_type=True,
            show_section_header=True,
            section_font_size=12,
            show_section_desc=True,
            section_desc_font_size=10,

            # 题目样式
            question_font_size=11,
            question_line_height=1.5,
            question_spacing=4,

            # 选项样式 - 横向排列
            option_font_size=11,
            option_spacing=15,
            option_per_line=4,
            show_answer_bracket=True,
            answer_bracket_position="right",

            # 分值
            score_font_size=10,
            score_position="inline",

            # 填空题
            blank_length=25,

            # 页面设置 - 参考真实试卷边距
            page_size="A4",
            margin_top=20,
            margin_bottom=20,
            margin_left=22,
            margin_right=22,

            # 答题区域
            answer_space_mode="auto",
            answer_line_height=8,

            # 不显示页眉页脚
            show_header=False,
            show_footer=False,
            show_page_number=False,
            show_score_table=False,
        )
    },
}


def get_template(template_type: str) -> PDFStyleConfig:
    """获取模板配置"""
    if template_type in TEMPLATES:
        return TEMPLATES[template_type]["config"]
    return TEMPLATES[TemplateType.STANDARD]["config"]


def get_template_list() -> list:
    """获取所有模板列表"""
    return [
        {
            "id": k,
            "name": v["name"],
            "description": v["description"]
        }
        for k, v in TEMPLATES.items()
    ]


def merge_config(
    base: PDFStyleConfig,
    overrides: Optional[Dict[str, Any]] = None
) -> PDFStyleConfig:
    """合并配置（基础配置 + 用户自定义覆盖）"""
    if not overrides:
        return base

    config_dict = base.__dict__.copy()
    config_dict.update(overrides)
    return PDFStyleConfig(**config_dict)

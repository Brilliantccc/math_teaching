"""元数据路由（无需认证）"""

from fastapi import APIRouter

router = APIRouter()

# ─── 常量数据 ─────────────────────────────────────────────

GRADES = ["初一", "初二", "初三", "高一", "高二", "高三"]

# 标准题目分类
CATEGORIES = {
    "代数": ["整式", "分式", "二次根式", "方程", "不等式"],
    "函数": ["一次函数", "反比例函数", "二次函数", "函数图像"],
    "几何": ["三角形", "四边形", "圆", "相似", "全等", "勾股定理"],
    "统计与概率": ["统计", "概率", "数据分析"],
    "数与计算": ["有理数", "实数", "计算"],
    "图形与变换": ["平移", "旋转", "对称"],
    "综合": ["综合题", "应用题", "探究"],
}

ALL_TAGS = []
GRADE_TAGS = {}
for grade in GRADES:
    GRADE_TAGS[grade] = []
for cat, tags in CATEGORIES.items():
    ALL_TAGS.extend(tags)
    for grade in GRADES:
        GRADE_TAGS[grade].extend(tags)


@router.get("/grades")
async def get_grades():
    """获取年级列表（无需认证）"""
    return {"grades": GRADES}


@router.get("/categories")
async def get_categories():
    """获取分类数据（无需认证）"""
    return {"categories": CATEGORIES}

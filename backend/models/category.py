"""标准题目分类定义"""

# 标准题目分类（初中数学）
STANDARD_CATEGORIES = {
    # 代数类
    "代数": ["代数", "数与式", "方程", "不等式", "整式", "分式", "二次根式"],

    # 函数类
    "函数": ["函数", "一次函数", "二次函数", "反比例函数", "函数图像"],

    # 几何类
    "几何": ["几何", "三角形", "四边形", "圆", "相似", "全等", "勾股定理", "坐标几何"],

    # 统计与概率
    "统计与概率": ["统计", "概率", "数据分析", "统计图"],

    # 数与计算
    "数与计算": ["有理数", "实数", "计算", "数轴", "相反数", "绝对值"],

    # 图形与变换
    "图形与变换": ["平移", "旋转", "对称", "投影", "视图"],

    # 综合题
    "综合": ["综合", "应用题", "探究", "开放题"],
}

# 分类映射：将不规范的分类映射到标准分类
CATEGORY_MAPPING = {
    # 代数相关
    "一元一次方程": "代数",
    "一元二次方程": "代数",
    "二元一次方程组": "代数",
    "不等式": "代数",
    "不等式组": "代数",
    "整式的加减": "代数",
    "整式的乘除": "代数",
    "因式分解": "代数",
    "分式": "代数",
    "二次根式": "代数",

    # 函数相关
    "一次函数": "函数",
    "反比例函数": "函数",
    "二次函数": "函数",
    "函数基础": "函数",

    # 几何相关
    "三角形": "几何",
    "全等三角形": "几何",
    "相似三角形": "几何",
    "四边形": "几何",
    "平行四边形": "几何",
    "矩形": "几何",
    "菱形": "几何",
    "正方形": "几何",
    "圆": "几何",
    "勾股定理": "几何",
    "坐标系": "几何",

    # 统计概率相关
    "数据的分析": "统计与概率",
    "数据的收集": "统计与概率",
    "概率初步": "统计与概率",

    # 数与计算相关
    "有理数": "数与计算",
    "有理数的运算": "数与计算",
    "实数": "数与计算",
    "科学记数法": "数与计算",
}


def normalize_category(category: str) -> str:
    """
    将分类标准化为标准分类

    Args:
        category: 原始分类

    Returns:
        标准分类名称
    """
    if not category:
        return ""

    category = category.strip()

    # 直接匹配标准分类
    if category in STANDARD_CATEGORIES:
        return category

    # 从映射表中查找
    if category in CATEGORY_MAPPING:
        return CATEGORY_MAPPING[category]

    # 模糊匹配（检查是否包含标准分类名称）
    for std_cat in STANDARD_CATEGORIES.keys():
        if std_cat in category or category in std_cat:
            return std_cat

    # 返回原值（无法标准化）
    return category


def get_all_standard_categories() -> list:
    """获取所有标准分类"""
    return list(STANDARD_CATEGORIES.keys())


def get_category_keywords(category: str) -> list:
    """获取分类的关键词"""
    return STANDARD_CATEGORIES.get(category, [])

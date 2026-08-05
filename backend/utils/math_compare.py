"""
数学表达式比较工具

支持多种等价表达形式的比较，包括：
- 代数表达式化简
- 数值等价比较
- 多种输入格式支持（LaTeX、普通文本等）
"""

import re
import sys
from typing import Optional, Tuple

# 尝试导入 sympy，如果不可用则降级到简单比较
try:
    from sympy import (
        sympify, simplify, parse_expr, Symbol,
        Rational, Float, pi, E, sqrt, Abs
    )
    from sympy.parsing.sympy_parser import (
        parse_expr, standard_transformations,
        implicit_multiplication_application,
        convert_xor
    )
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False


def normalize_latex_to_sympy(expr: str) -> str:
    """
    将 LaTeX 格式的数学表达式转换为 sympy 可解析的格式

    支持的 LaTeX 语法：
    - \frac{a}{b} -> a/b
    - \sqrt{x} -> sqrt(x)
    - x^{n} -> x**n
    - x^2 -> x**2
    - \times -> *
    - \div -> /
    - \pi -> pi
    - \cdot -> *
    """
    s = expr.strip()

    # 处理分式 \frac{a}{b}
    def replace_frac(match):
        numerator = match.group(1)
        denominator = match.group(2)
        return f"({numerator})/({denominator})"

    # 递归处理嵌套的 frac
    while r'\frac' in s:
        s = re.sub(r'\\frac\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}',
                   replace_frac, s)

    # 处理根号 \sqrt{x} 和 \sqrt[n]{x}
    def replace_sqrt(match):
        n = match.group(1) or '2'
        x = match.group(2)
        if n == '2':
            return f"sqrt({x})"
        return f"({x})**(1/{n})"

    s = re.sub(r'\\sqrt(?:\[([^\]]*)\])?\{([^{}]*)\}', replace_sqrt, s)

    # 处理上标和下标
    s = re.sub(r'\^{([^{}]*)}', r'**(\1)', s)
    s = re.sub(r'\^(\w)', r'**\1', s)
    s = re.sub(r'_{([^{}]*)}', r'_(\1)', s)

    # 处理常见的 LaTeX 命令
    replacements = {
        r'\times': '*',
        r'\cdot': '*',
        r'\div': '/',
        r'\pi': 'pi',
        r'\e': 'E',
        r'\infty': 'oo',
        r'\sin': 'sin',
        r'\cos': 'cos',
        r'\tan': 'tan',
        r'\log': 'log',
        r'\ln': 'ln',
        r'\left(': '(',
        r'\right)': ')',
        r'\left[': '[',
        r'\right]': ']',
        r'\left|': 'Abs(',
        r'\right|': ')',
        r'\,': ' ',
        r'\;': ' ',
        r'\!': '',
        r'\quad': ' ',
        r'\qquad': ' ',
    }

    for old, new in replacements.items():
        s = s.replace(old, new)

    # 移除剩余的 LaTeX 命令（如 \text, \mathrm 等）
    s = re.sub(r'\\[a-zA-Z]+\{([^{}]*)\}', r'\1', s)
    s = re.sub(r'\\[a-zA-Z]+', '', s)

    return s.strip()


def normalize_answer(expr: str) -> str:
    """
    标准化答案表达式

    处理常见的输入变体：
    - 空格处理
    - 乘号变体 (*, ×, ·, 省略)
    - 括号变体
    - 分数与小数
    """
    s = expr.strip()

    # 如果是 LaTeX 格式，先转换
    if '\\' in s or '{' in s:
        s = normalize_latex_to_sympy(s)

    # 统一乘号
    s = s.replace('×', '*')
    s = s.replace('·', '*')
    s = s.replace('∙', '*')

    # 统一除号
    s = s.replace('÷', '/')

    # 处理中文括号
    s = s.replace('（', '(').replace('）', ')')
    s = s.replace('【', '[').replace('】', ']')

    # 处理带分数 (如 "1 1/2" -> "1 + 1/2")
    def replace_mixed(match):
        whole = match.group(1)
        num = match.group(2)
        den = match.group(3)
        return f"({whole}+{num}/{den})"

    s = re.sub(r'(\d+)\s+(\d+)/(\d+)', replace_mixed, s)

    # 移除多余空格
    s = re.sub(r'\s+', '', s)

    return s


def try_parse_as_number(expr: str) -> Optional[float]:
    """
    尝试将表达式解析为数值

    支持：
    - 整数、小数
    - 分数 (1/2, 3/4)
    - 百分比 (50%)
    - 带分数 (1 1/2)
    """
    s = expr.strip()

    # 处理百分比
    if s.endswith('%'):
        try:
            return float(s[:-1]) / 100
        except ValueError:
            pass

    # 处理带分数 (如 "1 1/2" -> 1.5)
    match = re.match(r'^(\d+)\s+(\d+)/(\d+)$', s)
    if match:
        whole = int(match.group(1))
        num = int(match.group(2))
        den = int(match.group(3))
        if den != 0:
            return whole + num / den

    # 处理分数 (如 "1/2")
    match = re.match(r'^(-?\d+)/(-?\d+)$', s)
    if match:
        num = int(match.group(1))
        den = int(match.group(2))
        if den != 0:
            return num / den

    # 尝试直接转换为浮点数
    try:
        return float(s)
    except ValueError:
        return None


def compare_math_expressions(user_answer: str, correct_answer: str) -> Tuple[bool, str]:
    """
    比较两个数学表达式是否等价

    返回: (是否正确, 比较说明)
    """
    # 首先检查是否是简单的选择题答案（单个字母）
    user_stripped = user_answer.strip()
    correct_stripped = correct_answer.strip()

    # 移除 LaTeX 格式的答案前缀（如 "$\text{答案}$是D"）
    def extract_choice_from_latex(s):
        import re
        # 移除所有 LaTeX 格式（$...$）
        s = re.sub(r'\$[^$]*\$', '', s)
        # 移除常见前缀（包括中文和全角字符）
        prefixes = ['答案：', '答案:', '正确答案：', '正确答案:', '答案是', '答案为', '答案是', '是']
        for prefix in prefixes:
            if s.startswith(prefix):
                s = s[len(prefix):]
                break
        return s.strip()

    correct_stripped = extract_choice_from_latex(correct_stripped)

    # 如果是单个字母选项（如 A, B, C, D），忽略大小写比较
    if len(user_stripped) <= 2 and len(correct_stripped) <= 2:
        if user_stripped.upper() == correct_stripped.upper():
            return True, "选项匹配"

    # 标准化输入
    user_norm = normalize_answer(user_answer)
    correct_norm = normalize_answer(correct_answer)

    # 1. 首先尝试数值比较
    user_num = try_parse_as_number(user_norm)
    correct_num = try_parse_as_number(correct_norm)

    if user_num is not None and correct_num is not None:
        # 使用相对误差比较浮点数
        if correct_num == 0:
            is_close = abs(user_num) < 1e-9
        else:
            is_close = abs(user_num - correct_num) / max(abs(correct_num), 1) < 1e-9
        if is_close:
            return True, "数值相等"
        # 如果数值不等，继续尝试符号比较

    # 2. 如果 sympy 可用，进行符号化简比较
    if SYMPY_AVAILABLE:
        try:
            # 定义转换
            transformations = standard_transformations + (
                implicit_multiplication_application,
                convert_xor,
            )

            # 尝试解析表达式
            try:
                user_expr = parse_expr(user_norm, transformations=transformations)
                correct_expr = parse_expr(correct_norm, transformations=transformations)

                # 化简后比较
                diff = simplify(user_expr - correct_expr)
                if diff == 0:
                    return True, "数学等价（符号化简）"

                # 尝试数值代入比较
                from sympy import symbols, N
                x = symbols('x')
                test_points = [1, 2, 3, -1, -2, 0.5, 0.1]

                # 找出表达式中的自由变量
                user.free_symbols if hasattr(user_expr, 'free_symbols') else set()
                correct.free_symbols if hasattr(correct_expr, 'free_symbols') else set()

                all_symbols = user_expr.free_symbols | correct_expr.free_symbols

                if all_symbols:
                    # 使用数值代入验证
                    differences = []
                    for test_val in [1, 2, 3, -1, -2, 0.5, 10, -10]:
                        subs_dict = {s: test_val for s in all_symbols}
                        try:
                            u_val = complex(N(user_expr.subs(subs_dict)))
                            c_val = complex(N(correct_expr.subs(subs_dict)))
                            if abs(u_val - c_val) > 1e-9:
                                differences.append(False)
                        except:
                            pass

                    if not differences or all(differences):
                        return True, "数学等价（数值验证）"

            except (SyntaxError, TypeError, ValueError) as e:
                # 解析失败，继续尝试其他方法
                pass

        except Exception as e:
            # sympy 出错，降级处理
            pass

    # 3. 简单的字符串规范化比较
    # 移除所有空格和常见等价符号后比较
    def simplify_for_compare(s):
        s = re.sub(r'\s+', '', s)
        s = s.replace('*', '').replace('·', '').replace('×', '')
        s = s.replace('(', '').replace(')', '')
        s = s.replace('（', '').replace('）', '')
        return s.lower()

    user_simple = simplify_for_compare(user_answer)
    correct_simple = simplify_for_compare(correct_answer)

    if user_simple == correct_simple:
        return True, "内容相同"

    # 4. 处理常见的等价表达
    # 移除末尾的单位
    def remove_units(s):
        units = ['cm', 'm', 'mm', 'km', 'kg', 'g', '°', '度', '元', '个', '只']
        for unit in units:
            if s.endswith(unit):
                s = s[:-len(unit)]
        return s

    user_no_unit = remove_units(user_norm)
    correct_no_unit = remove_units(correct_norm)

    if user_no_unit == correct_no_unit:
        return True, "数值相等（忽略单位）"

    # 5. 如果都不匹配，返回错误
    return False, "表达式不等价"


def check_answer(user_answer: str, correct_answer: str, question_type: str = "fill") -> dict:
    """
    检查答案是否正确

    参数:
        user_answer: 用户输入的答案
        correct_answer: 标准答案
        question_type: 题目类型 (fill, choice, judge, calculate)

    返回:
        {
            "is_correct": bool,
            "message": str,
            "user_answer": str,
            "correct_answer": str
        }
    """
    # 选择题和判断题使用宽松匹配（不区分大小写，忽略空格和标点）
    if question_type in ['choice', 'judge']:
        # 标准化：转小写，移除空格和常见标点
        def normalize_choice(s):
            s = s.strip().lower()
            s = re.sub(r'[\s.,;!?，。；！？、·.]', '', s)
            return s

        user_norm = normalize_choice(user_answer)
        correct_norm = normalize_choice(correct_answer)

        # 支持多选题（如 "AB" 或 "A,B" 或 "A B"）
        is_correct = set(user_norm) == set(correct_norm) if len(correct_norm) > 1 else user_norm == correct_norm

        return {
            "is_correct": is_correct,
            "message": "正确" if is_correct else "错误",
            "user_answer": user_answer,
            "correct_answer": correct_answer
        }

    # 填空题和计算题使用智能比较
    is_correct, message = compare_math_expressions(user_answer, correct_answer)

    return {
        "is_correct": is_correct,
        "message": message,
        "user_answer": user_answer,
        "correct_answer": correct_answer
    }


# 测试函数
if __name__ == "__main__":
    test_cases = [
        ("x^2", "x**2", True),
        ("1/2", "0.5", True),
        ("50%", "0.5", True),
        ("\\frac{1}{2}", "1/2", True),
        ("\\sqrt{2}", "sqrt(2)", True),
        ("2x", "2*x", True),
        ("x^2 + 2x + 1", "(x+1)^2", True),
        ("1 1/2", "3/2", True),
        ("2+3", "5", True),
        ("x", "y", False),
    ]

    print("Math Expression Comparison Test:")
    print("-" * 50)

    for user, correct, expected in test_cases:
        result, msg = compare_math_expressions(user, correct)
        status = "PASS" if result == expected else "FAIL"
        print(f"{status}: '{user}' vs '{correct}'")
        print(f"  Result: {result}, Message: {msg}")
        print()

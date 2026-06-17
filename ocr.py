"""
OCR 识别模块
使用 Tesseract 识别图片中的数学题目
"""

import os
import logging
import pytesseract
from PIL import Image, ImageFilter, ImageEnhance

logger = logging.getLogger(__name__)


def setup_tesseract(tesseract_path=None):
    """
    配置 Tesseract 路径
    优先使用传入的路径，然后尝试常见路径
    """
    # 尝试的路径列表
    paths_to_try = []

    # 1. 如果提供了路径参数，优先使用
    if tesseract_path:
        paths_to_try.append(tesseract_path)

    # 2. 从环境变量获取
    env_path = os.environ.get('TESSERACT_PATH')
    if env_path:
        paths_to_try.append(env_path)

    # 3. 常见安装路径
    common_paths = [
        r"D:\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/opt/homebrew/bin/tesseract",
    ]
    paths_to_try.extend(common_paths)

    # 4. 尝试所有路径
    for path in paths_to_try:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            logger.info(f"Using Tesseract at: {path}")
            return True

    logger.warning("Tesseract not found. OCR functionality will be disabled.")
    return False


def preprocess_image(image_path):
    """图片预处理，提高 OCR 识别率"""
    img = Image.open(image_path)

    # 转灰度
    if img.mode != "L":
        img = img.convert("L")

    # 增强对比度
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)

    # 锐化
    img = img.filter(ImageFilter.SHARPEN)

    # 二值化
    threshold = 128
    img = img.point(lambda x: 255 if x > threshold else 0, "1")

    return img


def recognize_text(image_path, lang="chi_sim+eng", tesseract_path=None):
    """
    识别图片中的文本
    lang: 语言包，默认中文简体+英文
    tesseract_path: Tesseract可执行文件路径（可选）
    返回: 识别出的文本
    """
    if not setup_tesseract(tesseract_path):
        return "OCR不可用：未找到Tesseract"

    try:
        img = preprocess_image(image_path)
        text = pytesseract.image_to_string(img, lang=lang)
        return text.strip()
    except Exception as e:
        logger.error(f"OCR recognition failed: {str(e)}")
        return f"识别失败: {str(e)}"


def recognize_question(image_path):
    """
    识别图片中的数学题目，返回结构化数据
    返回: {"text": 识别文本, "success": bool}
    """
    try:
        text = recognize_text(image_path)
        if not text:
            return {"text": "", "success": False, "error": "未识别到文字"}

        # 清理文本
        text = clean_ocr_text(text)

        return {"text": text, "success": True}
    except Exception as e:
        return {"text": "", "success": False, "error": str(e)}


def clean_ocr_text(text):
    """清理 OCR 识别结果"""
    if not text:
        return ""

    # 移除多余空行
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned.append(line)

    return "\n".join(cleaned)

"""OCR文字识别工具"""

import os
import subprocess
import tempfile
from typing import Dict, Any


def recognize_question(image_path: str) -> Dict[str, Any]:
    """从图片识别数学题目"""
    from backend.config import settings

    tesseract_path = settings.TESSERACT_PATH
    if not os.path.exists(tesseract_path):
        raise FileNotFoundError(f"Tesseract未找到: {tesseract_path}")

    try:
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = tmp.name

        cmd = [tesseract_path, image_path, tmp_path.replace(".txt", ""), "-l", "chi_sim+eng"]
        subprocess.run(cmd, check=True, capture_output=True)

        with open(tmp_path, "r", encoding="utf-8") as f:
            text = f.read()
        os.unlink(tmp_path)

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return {
            "content": "\n".join(lines),
            "answer": "",
            "analysis": "",
            "tags": [],
            "difficulty": 1,
            "category": "",
        }
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"OCR识别失败: {e.stderr}")
    except Exception as e:
        raise RuntimeError(f"OCR处理错误: {str(e)}")

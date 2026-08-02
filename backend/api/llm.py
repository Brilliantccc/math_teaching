"""LLM辅助功能路由"""

import base64
import io
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from PIL import Image

from backend.core.deps import get_current_user
from backend.core.exceptions import BadRequestException
from backend.models.user import User
from backend.services.llm_service import llm_service
from backend.config import settings


def resize_image(image_data: bytes, max_size: int = 2048) -> bytes:
    """压缩图片到合理尺寸"""
    try:
        img = Image.open(io.BytesIO(image_data))
        # 转换为RGB（处理RGBA、P等模式）
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        w, h = img.size
        if max(w, h) > max_size:
            ratio = max_size / max(w, h)
            new_w, new_h = int(w * ratio), int(h * ratio)
            img = img.resize((new_w, new_h), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85)
        return buf.getvalue()
    except Exception as e:
        print(f"[LLM] Image resize error: {e}, using original")
        return image_data

router = APIRouter()

EXTRACT_PROMPT = """识别图片中的数学题，返回JSON数组。

每个题目包含：
- content: 题干内容
- answer_analysis: 答案和解析
- difficulty: 难度(1简单/2中等/3困难)
- category: 分类

重要规则：
1. 中文必须用 \\text{} 包裹在 $ 内，如 $\\text{已知}$
2. 公式直接写在 $ 内，如 $\\frac{1}{2}$
3. 换行用 \\n 表示

返回格式：JSON数组，如
[{"content":"$\\text{题目内容}$","answer_analysis":"$\\text{答案}$\\n---解析---\\n$\\text{解析}$","difficulty":1,"category":"代数"}]

只返回JSON，不要其他文字"""

ANALYSIS_PROMPT = """根据题目生成答案和解析。

题目：{content}

重要规则：
1. 中文必须用 \\text{} 包裹在 $ 内，如 $\\text{已知}$
2. 公式直接写在 $ 内，如 $\\frac{1}{2}$
3. 答案和解析之间用 ---解析--- 分隔

返回JSON格式：{{"answer_analysis": "$\\text{答案}$\\n---解析---\\n$\\text{解析内容}$"}}

只返回JSON，不要其他文字。"""


@router.get("/status")
async def get_status():
    """获取LLM状态（无需认证）"""
    return {
        "configured": llm_service.is_configured(),
        "model": llm_service.model_id or "未配置",
    }


@router.post("/extract")
async def extract_from_image(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """从图片提取题目"""
    if not llm_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="LLM未配置，请设置 LLM_MODEL_ID、LLM_API_KEY、LLM_BASE_URL"
        )

    if not image.filename:
        raise HTTPException(status_code=400, detail="无效文件")

    ext = image.filename.rsplit(".", 1)[-1].lower()
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp'}
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="不支持的图片格式")

    image_data = await image.read()
    if len(image_data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片不能超过10MB")

    try:
        # 压缩图片
        resized_data = resize_image(image_data)
        print(f"[LLM] Image resized: {len(image_data)} -> {len(resized_data)} bytes")
        image_b64 = base64.b64encode(resized_data).decode()
        result_text = llm_service.chat_with_image(image_b64, EXTRACT_PROMPT)
        print(f"[LLM] Raw response length: {len(result_text)}")
        print(f"[LLM] Raw response: {result_text[:1000]}")
        result = llm_service.parse_json(result_text)
        print(f"[LLM] Parsed result: {result}")
        # 确保返回数组格式
        if isinstance(result, dict):
            result = [result]
        return {"success": True, "data": result}
    except ValueError as e:
        print(f"[LLM] Parse error: {e}")
        raise HTTPException(status_code=400, detail=f"JSON解析失败: {str(e)}")
    except Exception as e:
        print(f"[LLM] Error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")


@router.post("/batch-extract")
async def batch_extract_from_images(
    images: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """批量从图片提取题目"""
    if not llm_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="LLM未配置，请设置 LLM_MODEL_ID、LLM_API_KEY、LLM_BASE_URL"
        )

    if not images:
        raise HTTPException(status_code=400, detail="请上传至少一张图片")

    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp'}
    results = []
    errors = []

    for idx, image in enumerate(images):
        if not image.filename:
            errors.append({"index": idx, "error": "无效文件"})
            continue

        ext = image.filename.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            errors.append({"index": idx, "error": f"不支持的图片格式: {ext}"})
            continue

        image_data = await image.read()
        if len(image_data) > 10 * 1024 * 1024:
            errors.append({"index": idx, "error": "图片不能超过10MB"})
            continue

        try:
            resized_data = resize_image(image_data)
            image_b64 = base64.b64encode(resized_data).decode()
            result_text = llm_service.chat_with_image(image_b64, EXTRACT_PROMPT)
            print(f"[LLM] Batch {idx} response: {result_text[:500]}")
            result = llm_service.parse_json(result_text)
            # 确保返回数组格式
            if isinstance(result, dict):
                result = [result]
            results.append({"index": idx, "filename": image.filename, "data": result})
        except Exception as e:
            print(f"[LLM] Batch {idx} error: {e}")
            errors.append({"index": idx, "filename": image.filename, "error": str(e)})

    return {"success": True, "data": results, "errors": errors}


@router.post("/analyze")
async def generate_analysis(
    data: dict,
    current_user: User = Depends(get_current_user)
):
    """生成答案解析"""
    if not llm_service.is_configured():
        raise HTTPException(status_code=503, detail="LLM未配置")

    content = data.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="请提供题目内容")

    try:
        prompt = ANALYSIS_PROMPT.format(content=content)
        result_text = llm_service.chat([{"role": "user", "content": prompt}])
        result = llm_service.parse_json(result_text)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""LLM辅助功能路由"""

import asyncio
import base64
import io
import os
import re
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from PIL import Image

from backend.core.deps import get_current_user
from backend.core.exceptions import BadRequestException
from backend.models.user import User
from backend.services.llm_service import llm_service
from backend.config import settings
from backend.prompts import EXTRACT_PROMPT, ANALYSIS_PROMPT
from backend.schemas.llm import AnalyzeRequest, LLMStatusResponse, ExtractResponse, BatchExtractResponse


def normalize_latex(text: str) -> str:
    """
    规范化 LaTeX 代码，确保格式统一

    规则：
    1. 修复双反斜杠：\\\\text -> \text
    2. 中文文本必须用 \text{} 包裹
    3. 修复常见的 LaTeX 命令格式
    """
    if not text:
        return text

    # 第一步：修复双反斜杠（数据库存储时可能被转义）
    # 先处理四重反斜杠，再处理双重反斜杠
    text = re.sub(r'\\\\\\\\([a-zA-Z]+)', r'\\\1', text)
    text = re.sub(r'\\\\([a-zA-Z]+)', r'\\1', text)

    # 第二步：确保 \text{} 命令格式正确
    # 修复 \text{xxx} 格式（确保花括号匹配）
    text = re.sub(r'\\text\{([^}]*?)\}', r'\\text{\1}', text)

    # 第三步：修复常见错误
    # 修复 \geq 和 \leq（确保后面有空格或符号）
    text = re.sub(r'\\geq(?![a-zA-Z])', r'\\geq ', text)
    text = re.sub(r'\\leq(?![a-zA-Z])', r'\\leq ', text)

    # 第四步：清理多余的空格和换行
    text = re.sub(r'\n\s*\n', '\n', text)
    text = text.strip()

    return text


def normalize_answer_analysis(answer_analysis: str) -> str:
    """
    规范化答案与解析格式

    格式要求：
    $\text{答案}$：答案内容
    ---解析---
    $\text{解析内容}$（如果解析很长，可以用多个 $\text{}$ 块）
    """
    if not answer_analysis:
        return answer_analysis

    # 清理字面的换行符（两个字符：反斜杠+n）
    answer_analysis = answer_analysis.replace('\\n', '')

    # 规范化 LaTeX
    answer_analysis = normalize_latex(answer_analysis)

    # 确保答案格式正确
    # 修复 $\text{答案}$：格式
    answer_analysis = re.sub(
        r'\$\\text\{答案\}\$[：:]',
        r'$\\text{答案}$：',
        answer_analysis
    )

    # 确保解析分隔符正确
    answer_analysis = re.sub(r'---解析---', '\n---解析---\n', answer_analysis)

    return answer_analysis


def resize_image(image_data: bytes, max_size: int = 1280) -> bytes:
    """压缩图片到合理尺寸（1280px足够AI识别，速度更快）"""
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


def crop_image_region(image_data: bytes, region: List[float]) -> Optional[bytes]:
    """
    根据坐标裁剪图片区域

    Args:
        image_data: 原始图片数据
        region: [x1, y1, x2, y2] 坐标（0-1之间的比例值）

    Returns:
        裁剪后的图片数据，失败返回None
    """
    try:
        if not region or len(region) != 4:
            return None

        img = Image.open(io.BytesIO(image_data))
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')

        w, h = img.size
        x1, y1, x2, y2 = region

        # 确保坐标在0-1范围内
        x1 = max(0, min(1, x1))
        y1 = max(0, min(1, y1))
        x2 = max(0, min(1, x2))
        y2 = max(0, min(1, y2))

        # 转换为像素坐标
        left = int(x1 * w)
        top = int(y1 * h)
        right = int(x2 * w)
        bottom = int(y2 * h)

        # 确保裁剪区域有效
        if right <= left or bottom <= top:
            print(f"[LLM] Invalid crop region: {region}")
            return None

        # 裁剪图片
        cropped = img.crop((left, top, right, bottom))

        # 保存为JPEG
        buf = io.BytesIO()
        cropped.save(buf, format='JPEG', quality=90)
        return buf.getvalue()

    except Exception as e:
        print(f"[LLM] Crop error: {e}")
        return None


def save_cropped_image(image_data: bytes, filename_prefix: str) -> Optional[str]:
    """
    保存裁剪后的图片到服务器

    Args:
        image_data: 图片数据
        filename_prefix: 文件名前缀

    Returns:
        保存后的相对路径，失败返回None
    """
    try:
        filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.jpg"
        upload_path = os.path.join(settings.UPLOAD_DIR, filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)

        with open(upload_path, "wb") as f:
            f.write(image_data)

        return f"uploads/{filename}"
    except Exception as e:
        print(f"[LLM] Save image error: {e}")
        return None

router = APIRouter()


@router.get("/status", response_model=LLMStatusResponse)
async def get_status():
    """获取LLM状态（无需认证）"""
    return LLMStatusResponse(
        configured=llm_service.is_configured(),
        model=llm_service.model_id or "未配置"
    )


@router.post("/extract")
async def extract_from_image(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """从图片提取题目，并裁剪每道题的示意图"""
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

    max_retries = 5
    last_error = None

    for attempt in range(max_retries):
        try:
            # 压缩图片用于AI识别
            resized_data = resize_image(image_data)
            print(f"[LLM] Image resized: {len(image_data)} -> {len(resized_data)} bytes")
            image_b64 = base64.b64encode(resized_data).decode()

            # 逐步增加 max_tokens，首次用4096足够
            max_tokens = 4096 * (attempt + 1)  # 4096, 8192, 12288, 16384, 20480
            print(f"[LLM] Attempt {attempt + 1}/{max_retries}, max_tokens={max_tokens}")

            result_text = await llm_service.chat_with_image(
                image_b64,
                EXTRACT_PROMPT,
                max_tokens=max_tokens,
                temperature=0.3,
            )
            print(f"[LLM] Raw response length: {len(result_text)}")
            print(f"[LLM] Raw response: {result_text[:1000]}")

            # 检查空响应
            if not result_text or not result_text.strip():
                print(f"[LLM] Empty response, retrying...")
                last_error = ValueError("LLM返回空响应")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                raise last_error

            # 先尝试解析JSON，成功就不需要重试
            try:
                result = llm_service.parse_json(result_text)
                print(f"[LLM] Parsed result: {result}")
            except ValueError as parse_err:
                # JSON解析失败，检查是否被截断
                # 清理markdown代码块后再检测
                cleaned = result_text.strip()
                if cleaned.startswith('```'):
                    # 去掉首尾的 ```
                    lines = cleaned.split('\n')
                    lines = [l for l in lines if not l.strip().startswith('```')]
                    cleaned = '\n'.join(lines)

                if cleaned.rstrip().endswith((']', '}')):
                    # 以 ] 或 } 结尾，说明响应完整但JSON格式有问题
                    print(f"[LLM] JSON parse failed but response looks complete: {parse_err}")
                    raise ValueError(f"JSON解析失败: {result_text[:200]}")
                else:
                    # 被截断了，发送补全请求
                    print(f"[LLM] Response truncated, requesting completion...")
                    try:
                        completion_prompt = f"请补全以下JSON的剩余部分，不要添加任何解释，只返回缺失的部分：\n\n{result_text[-200:]}"
                        completion_text = await llm_service.chat(
                            [{"role": "user", "content": completion_prompt}],
                            max_tokens=2048,
                            temperature=0.3,
                        )
                        # 拼接原始响应和补全内容
                        full_text = result_text + completion_text
                        print(f"[LLM] Completed response: {full_text[:500]}")
                        result = llm_service.parse_json(full_text)
                        print(f"[LLM] Parsed result after completion: {result}")
                    except Exception as completion_err:
                        print(f"[LLM] Completion failed: {completion_err}")
                        last_error = ValueError("响应截断且补全失败")
                        if attempt < max_retries - 1:
                            continue
                        raise last_error
            # 确保返回数组格式
            if isinstance(result, dict):
                result = [result]

            # 逐道题处理，单题失败不影响其他
            valid_items = []
            for idx, item in enumerate(result):
                try:
                    # 验证必须字段
                    if not item.get("content"):
                        print(f"[LLM] Item {idx} missing content, skipping")
                        continue

                    # 规范化 LaTeX 代码
                    if item.get("content"):
                        item["content"] = normalize_latex(item["content"])
                    if item.get("answer_analysis"):
                        item["answer_analysis"] = normalize_answer_analysis(item["answer_analysis"])

                    # 不再裁剪图片，只保留图片描述
                    item.pop("image_regions", None)
                    valid_items.append(item)
                except Exception as item_error:
                    print(f"[LLM] Item {idx} processing error: {item_error}")
                    # 单题处理失败，跳过继续

            if valid_items:
                return {"success": True, "data": valid_items, "has_image": True}

        except ValueError as e:
            last_error = e
            print(f"[LLM] Parse error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)  # 等待1秒后重试（异步）
        except Exception as e:
            print(f"[LLM] Error: {type(e).__name__}: {e}")
            raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")

    # 所有重试都失败
    raise HTTPException(status_code=400, detail=f"JSON解析失败（已重试{max_retries}次）: {str(last_error)}")


@router.post("/batch-extract")
async def batch_extract_from_images(
    images: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """批量从图片提取题目（容错处理：单张失败不影响其他）"""
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
            result_text = await llm_service.chat_with_image(image_b64, EXTRACT_PROMPT)
            print(f"[LLM] Batch {idx} response: {result_text[:500]}")

            # 尝试解析 JSON，失败时重试
            try:
                result = llm_service.parse_json(result_text)
            except ValueError:
                print(f"[LLM] Batch {idx} JSON parse failed, retrying...")
                # 重试一次
                result_text = await llm_service.chat_with_image(image_b64, EXTRACT_PROMPT)
                result = llm_service.parse_json(result_text)

            # 确保返回数组格式
            if isinstance(result, dict):
                result = [result]

            # 逐道题处理，单题失败不影响其他
            valid_items = []
            for item_idx, item in enumerate(result):
                try:
                    # 验证必须字段
                    if not item.get("content"):
                        print(f"[LLM] Batch {idx} item {item_idx} missing content, skipping")
                        continue

                    image_regions = item.get("image_regions", [])
                    cropped_images = []

                    for region_idx, region in enumerate(image_regions):
                        if region and len(region) == 4:
                            cropped_data = crop_image_region(image_data, region)
                            if cropped_data:
                                filename_prefix = f"batch_{idx}_{item_idx}_{region_idx}"
                                image_path = save_cropped_image(cropped_data, filename_prefix)
                                if image_path:
                                    cropped_images.append(image_path)
                                    print(f"[LLM] Batch cropped image saved: {image_path}")

                    # 检查：如果声称有图但裁剪全部失败，跳过该题
                    if image_regions and not cropped_images:
                        print(f"[LLM] Batch {idx} item {item_idx} has image_regions but crop failed, skipping")
                        continue

                    item["cropped_images"] = cropped_images
                    item.pop("image_regions", None)
                    valid_items.append(item)
                except Exception as item_error:
                    print(f"[LLM] Batch {idx} item {item_idx} error: {item_error}")
                    # 单题处理失败，跳过继续

            if valid_items:
                results.append({"index": idx, "filename": image.filename, "data": valid_items})
            else:
                errors.append({"index": idx, "filename": image.filename, "error": "该图片未能识别出有效题目"})

        except Exception as e:
            print(f"[LLM] Batch {idx} error: {e}")
            errors.append({"index": idx, "filename": image.filename, "error": str(e)})

    return {"success": True, "data": results, "errors": errors}


@router.post("/analyze")
async def generate_analysis(
    data: AnalyzeRequest,
    current_user: User = Depends(get_current_user)
):
    """生成答案解析"""
    if not llm_service.is_configured():
        raise HTTPException(status_code=503, detail="LLM未配置")

    if not data.content:
        raise HTTPException(status_code=400, detail="请提供题目内容")

    # 获取图片描述（可选）
    if data.image_descriptions:
        image_descriptions_text = "\n".join([f"- {desc}" for desc in data.image_descriptions])
    else:
        image_descriptions_text = "无图片描述"

    try:
        prompt = ANALYSIS_PROMPT.format(content=data.content, image_descriptions=image_descriptions_text)
        print(f"[LLM] Analyze prompt: {prompt[:200]}...")
        result_text = await llm_service.chat([{"role": "user", "content": prompt}])
        print(f"[LLM] Analyze raw response: {result_text[:500]}")
        result = llm_service.parse_json(result_text)
        print(f"[LLM] Analyze parsed result: {result}")

        # 规范化答案解析
        if isinstance(result, dict) and result.get("answer_analysis"):
            result["answer_analysis"] = normalize_answer_analysis(result["answer_analysis"])

        return {"success": True, "data": result}
    except Exception as e:
        print(f"[LLM] Analyze error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

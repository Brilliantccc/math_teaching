"""LLM辅助功能路由"""

import base64

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from backend.core.deps import get_current_user
from backend.core.exceptions import BadRequestException
from backend.models.user import User
from backend.services.llm_service import llm_service
from backend.config import settings

router = APIRouter()

EXTRACT_PROMPT = """识别图片中的数学题目，返回JSON：
{
    "title": "标题",
    "content": "内容（LaTeX格式）",
    "answer": "答案",
    "analysis": "解析",
    "tags": ["知识点"],
    "difficulty": 1,
    "category": "分类"
}
数学公式用 $...$，只返回JSON。"""

ANALYSIS_PROMPT = """根据题目生成答案和解析（JSON）：
题目：{content}
返回：{{"answer": "答案", "analysis": "解析"}}
数学公式用LaTeX，只返回JSON。"""


@router.get("/status")
async def get_status(current_user: User = Depends(get_current_user)):
    """获取LLM状态"""
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
        image_b64 = base64.b64encode(image_data).decode()
        result_text = llm_service.chat_with_image(image_b64, EXTRACT_PROMPT)
        result = llm_service.parse_json(result_text)
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")


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

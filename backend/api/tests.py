"""组卷管理路由"""

import os
import json
import uuid
import random
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from backend.core.deps import get_db, get_current_user
from backend.core.exceptions import NotFoundException
from backend.models.user import User
from backend.models.test import Test
from backend.models.question import Question
from backend.schemas.test import (
    TestCreate, TestResponse, TestListResponse,
    AutoGenerateRequest, PreviewPdfRequest, PDFExportRequest
)
from backend.config import settings

router = APIRouter()

# 内存存储PDF导出任务状态（生产环境建议用Redis）
_pdf_tasks = {}


# ============ 固定路径路由（必须在 /{t_id} 之前定义，避免路由冲突） ============

@router.get("", response_model=TestListResponse)
async def get_tests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取组卷列表"""
    result = await db.execute(
        select(Test).order_by(Test.created_at.desc())
    )
    tests = result.scalars().all()

    return TestListResponse(
        tests=[TestResponse(**t.to_dict()) for t in tests]
    )


@router.post("", response_model=dict)
async def create_test(
    data: TestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建组卷"""
    name = data.name or f"试卷_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    question_ids = json.dumps(data.question_ids, ensure_ascii=False)

    # 处理每道题的分值
    question_scores = {}
    if data.question_scores:
        question_scores = data.question_scores
    else:
        # 使用统一分值
        for qid in data.question_ids:
            question_scores[qid] = data.score_per_question

    test = Test(
        name=name,
        question_ids=question_ids,
        score_per_question=data.score_per_question,
        question_scores=json.dumps(question_scores, ensure_ascii=False),
        created_by=current_user.id
    )
    db.add(test)
    await db.commit()
    await db.refresh(test)

    return {"id": test.id, "message": "试卷已保存"}


# ============ 模板系统 ============

@router.get("/templates")
async def get_pdf_templates():
    """获取PDF模板列表（无需认证）"""
    from backend.utils.pdf_templates import get_template_list
    return {"templates": get_template_list()}


@router.get("/templates/{template_id}")
async def get_pdf_template_detail(
    template_id: str
):
    """获取PDF模板详情（无需认证）"""
    from backend.utils.pdf_templates import get_template, TEMPLATES
    from backend.core.exceptions import NotFoundException

    if template_id not in TEMPLATES:
        raise NotFoundException("模板")

    template_info = TEMPLATES[template_id]
    config = template_info["config"]

    return {
        "id": template_id,
        "name": template_info["name"],
        "description": template_info["description"],
        "config": {
            "title_font_size": config.title_font_size,
            "question_font_size": config.question_font_size,
            "show_score_table": config.show_score_table,
            "show_header": config.show_header,
            "show_footer": config.show_footer,
            "group_by_type": config.group_by_type,
            "answer_space_mode": config.answer_space_mode,
        }
    }


@router.post("/auto", response_model=dict)
async def auto_generate_test(
    data: AutoGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """自动生成组卷"""
    # 解析年级参数（支持逗号分隔的多个年级）
    grade_list = []
    if data.grade:
        grade_list = [g.strip() for g in data.grade.split(',') if g.strip()]

    # 如果指定了按题型配置数量
    if data.question_type_counts:
        selected_ids = []
        for q_type, count in data.question_type_counts.items():
            if count <= 0:
                continue

            query = select(Question).where(Question.question_type == q_type)

            # 应用其他筛选条件
            if data.tags:
                tag_conditions = [Question.tags.contains(t) for t in data.tags]
                query = query.where(or_(*tag_conditions))
            if data.difficulties:
                query = query.where(Question.difficulty.in_(data.difficulties))
            if grade_list:
                query = query.where(Question.grade.in_(grade_list))

            result = await db.execute(query)
            questions = result.scalars().all()

            # 随机抽样
            selected = random.sample(questions, min(count, len(questions)))
            selected_ids.extend([q.id for q in selected])

        return {"question_ids": selected_ids, "count": len(selected_ids)}

    # 传统模式：按总数生成
    query = select(Question)

    if data.tags:
        tag_conditions = [Question.tags.contains(t) for t in data.tags]
        query = query.where(or_(*tag_conditions))
    if data.difficulties:
        query = query.where(Question.difficulty.in_(data.difficulties))
    if grade_list:
        query = query.where(Question.grade.in_(grade_list))
    if data.question_type:
        query = query.where(Question.question_type == data.question_type)

    result = await db.execute(query)
    all_questions = result.scalars().all()

    # 随机抽样
    selected = random.sample(all_questions, min(data.count, len(all_questions)))
    q_ids = [q.id for q in selected]

    return {"question_ids": q_ids, "count": len(q_ids)}


@router.post("/preview/pdf")
async def export_preview_pdf(
    data: PreviewPdfRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """预览导出PDF"""
    if not data.question_ids:
        raise HTTPException(status_code=400, detail="没有题目")

    result = await db.execute(
        select(Question).where(Question.id.in_(data.question_ids))
    )
    questions = result.scalars().all()
    questions_data = [q.to_dict() for q in questions]

    from backend.utils.pdf_utils import generate_test_pdf
    output_path = os.path.join(settings.UPLOAD_DIR, f"preview_{uuid.uuid4().hex}.pdf")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        generate_test_pdf(
            questions_data, output_path,
            title=data.title,
            question_scores=data.question_scores
        )
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=f"{data.title}.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成PDF失败: {str(e)}")


# ============ 异步PDF导出功能 ============

def _generate_pdf_task(
    task_id: str,
    t_id: int,
    question_ids: list,
    title: str,
    question_scores: Optional[dict] = None
):
    """后台生成PDF的任务"""
    import asyncio
    from backend.utils.pdf_utils import generate_test_pdf

    # 更新状态为处理中
    _pdf_tasks[task_id] = {
        "status": "processing",
        "progress": 10,
        "t_id": t_id,
        "created_at": datetime.now().isoformat(),
        "output_path": None,
        "download_url": None,
        "error": None
    }

    try:
        from backend.config import settings

        _pdf_tasks[task_id]["progress"] = 30

        # 生成PDF
        output_path = os.path.join(
            settings.UPLOAD_DIR,
            f"test_{t_id}_{task_id[:8]}.pdf"
        )
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        _pdf_tasks[task_id]["progress"] = 50

        # 同步获取题目数据
        from backend.models.question import Question
        from backend.database import async_session

        async def fetch_questions():
            async with async_session() as session:
                result = await session.execute(
                    select(Question).where(Question.id.in_(question_ids))
                )
                return [q.to_dict() for q in result.scalars().all()]

        # 使用 asyncio.run 获取数据
        try:
            loop = asyncio.get_running_loop()
            # 如果有运行中的循环，使用线程池
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                questions_data = pool.submit(asyncio.run, fetch_questions()).result()
        except RuntimeError:
            questions_data = asyncio.run(fetch_questions())

        _pdf_tasks[task_id]["progress"] = 70

        generate_test_pdf(
            questions_data, output_path,
            title=title or "数学试卷",
            question_scores=question_scores
        )

        _pdf_tasks[task_id].update({
            "status": "completed",
            "progress": 100,
            "output_path": output_path,
            "download_url": f"/api/tests/pdf/download/{task_id}"
        })

    except Exception as e:
        _pdf_tasks[task_id].update({
            "status": "failed",
            "error": str(e),
            "progress": 0
        })
        print(f"[PDF] Task {task_id} failed: {e}")


@router.post("/async")
async def create_async_pdf_task(
    data: PreviewPdfRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """创建异步PDF导出任务"""
    if not data.question_ids:
        raise HTTPException(status_code=400, detail="没有题目")

    task_id = uuid.uuid4().hex

    # 启动后台任务
    background_tasks.add_task(
        _generate_pdf_task,
        task_id=task_id,
        t_id=0,  # 预览模式无t_id
        question_ids=data.question_ids,
        title=data.title or "数学试卷",
        question_scores=data.question_scores
    )

    return {
        "task_id": task_id,
        "status": "processing",
        "message": "PDF生成任务已创建"
    }


@router.get("/task/{task_id}")
async def get_pdf_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """查询PDF任务状态"""
    if task_id not in _pdf_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = _pdf_tasks[task_id]
    return {
        "task_id": task_id,
        "status": task["status"],
        "progress": task["progress"],
        "download_url": task.get("download_url"),
        "error": task.get("error")
    }


@router.get("/download/{task_id}")
async def download_task_pdf(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """下载异步任务生成的PDF"""
    if task_id not in _pdf_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = _pdf_tasks[task_id]
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")

    if not task["output_path"] or not os.path.exists(task["output_path"]):
        raise HTTPException(status_code=404, detail="PDF文件不存在")

    return FileResponse(
        task["output_path"],
        media_type="application/pdf",
        filename=f"{task.get('title', '试卷')}.pdf"
    )


@router.delete("/task/{task_id}")
async def delete_pdf_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除PDF任务及文件"""
    if task_id not in _pdf_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = _pdf_tasks.pop(task_id)

    # 删除生成的PDF文件
    if task.get("output_path") and os.path.exists(task["output_path"]):
        os.remove(task["output_path"])

    return {"message": "任务已删除"}


@router.get("/cache/stats")
async def get_latex_cache_stats(
    current_user: User = Depends(get_current_user)
):
    """获取LaTeX缓存统计"""
    from backend.utils.pdf_utils import get_latex_cache_stats
    return get_latex_cache_stats()


@router.post("/cache/clear")
async def clear_latex_cache_endpoint(
    current_user: User = Depends(get_current_user)
):
    """清理LaTeX缓存"""
    from backend.utils.pdf_utils import clear_latex_cache
    clear_latex_cache()
    return {"message": "缓存已清理"}


@router.post("/preview")
async def preview_pdf_with_template(
    data: PDFExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """使用模板预览PDF"""
    if not data.question_ids:
        raise HTTPException(status_code=400, detail="没有题目")

    # 获取题目
    result = await db.execute(
        select(Question).where(Question.id.in_(data.question_ids))
    )
    questions = result.scalars().all()
    if not questions:
        raise HTTPException(status_code=404, detail="题目不存在")

    questions_data = [q.to_dict() for q in questions]

    # 获取模板配置
    from backend.utils.pdf_templates import get_template, merge_config
    base_config = get_template(data.template)

    # 合并用户自定义配置
    final_config = merge_config(base_config, data.style_overrides)

    # 生成PDF
    from backend.utils.pdf_utils import generate_test_pdf
    output_path = os.path.join(
        settings.UPLOAD_DIR,
        f"preview_{uuid.uuid4().hex}.pdf"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        generate_test_pdf(
            questions_data, output_path,
            title=data.title,
            question_scores=data.question_scores,
            style_config=final_config
        )
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=f"{data.title}_预览.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成PDF失败: {str(e)}")


# ============ 参数化路由（放在最后） ============

@router.delete("/{t_id}")
async def delete_test(
    t_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除组卷"""
    test = await db.get(Test, t_id)
    if not test:
        raise NotFoundException("试卷")
    await db.delete(test)
    await db.commit()
    return {"message": "已删除"}


@router.get("/{t_id}", response_model=TestResponse)
async def get_test(
    t_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取组卷详情"""
    test = await db.get(Test, t_id)
    if not test:
        raise NotFoundException("试卷")

    data = test.to_dict()
    q_ids = json.loads(test.question_ids)

    if q_ids:
        result = await db.execute(
            select(Question).where(Question.id.in_(q_ids))
        )
        questions = result.scalars().all()
        q_map = {q.id: q for q in questions}
        data["questions"] = [q_map[qid].to_dict() for qid in q_ids if qid in q_map]
    else:
        data["questions"] = []

    return TestResponse(**data)


@router.get("/{t_id}/pdf")
async def export_test_pdf(
    t_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出组卷PDF"""
    test = await db.get(Test, t_id)
    if not test:
        raise NotFoundException("试卷")

    q_ids = json.loads(test.question_ids)
    if not q_ids:
        raise HTTPException(status_code=400, detail="试卷没有题目")

    result = await db.execute(
        select(Question).where(Question.id.in_(q_ids))
    )
    questions = result.scalars().all()
    questions_data = [q.to_dict() for q in questions]

    # 解析question_scores
    question_scores = {}
    if test.question_scores:
        try:
            question_scores = json.loads(test.question_scores)
            # 将字符串key转换为int
            question_scores = {int(k): v for k, v in question_scores.items()}
        except:
            pass

    # 生成PDF（需要导入pdf_utils）
    from backend.utils.pdf_utils import generate_test_pdf
    output_path = os.path.join(settings.UPLOAD_DIR, f"test_{t_id}_{uuid.uuid4().hex}.pdf")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        generate_test_pdf(
            questions_data, output_path,
            title=test.name or "数学试卷",
            question_scores=question_scores if question_scores else None
        )
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=f"{test.name or '试卷'}.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成PDF失败: {str(e)}")

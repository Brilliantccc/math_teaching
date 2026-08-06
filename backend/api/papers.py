"""试卷管理路由"""

import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.core.deps import get_db, get_current_user
from backend.core.exceptions import NotFoundException
from backend.models.user import User
from backend.models.paper import Paper
from backend.models.question import Question
from backend.schemas.paper import PaperResponse, PaperListResponse, AddPaperQuestionRequest
from backend.config import settings
from backend.utils.math_compare import extract_answer_from_analysis

router = APIRouter()

ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp'}
ALLOWED_PDF_EXTENSIONS = {'pdf'}


@router.get("", response_model=PaperListResponse)
async def get_papers(
    grade: str = Query(default=''),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取试卷列表"""
    query = select(Paper)
    if grade:
        query = query.where(Paper.grade == grade)

    result = await db.execute(query.order_by(Paper.created_at.desc()))
    papers = result.scalars().all()

    return PaperListResponse(
        papers=[PaperResponse(**p.to_dict()) for p in papers]
    )


@router.post("", response_model=dict)
async def create_paper(
    name: str = Form(default=''),
    grade: str = Form(default='初一上'),
    source: str = Form(default=''),
    pdf: Optional[UploadFile] = File(default=None),
    image: Optional[UploadFile] = File(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新试卷"""
    image_path = ""
    pdf_path = ""

    # 处理PDF上传
    if pdf and pdf.filename:
        ext = pdf.filename.rsplit(".", 1)[-1].lower()
        if ext in ALLOWED_PDF_EXTENSIONS:
            filename = f"paper_{uuid.uuid4().hex}_{pdf.filename}"
            upload_path = os.path.join(settings.UPLOAD_DIR, filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            with open(upload_path, "wb") as f:
                content = await pdf.read()
                f.write(content)
            pdf_path = f"uploads/{filename}"

    # 处理图片上传
    if image and image.filename:
        ext = image.filename.rsplit(".", 1)[-1].lower()
        if ext in ALLOWED_IMAGE_EXTENSIONS:
            filename = f"paper_{uuid.uuid4().hex}_{image.filename}"
            upload_path = os.path.join(settings.UPLOAD_DIR, filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            with open(upload_path, "wb") as f:
                content = await image.read()
                f.write(content)
            image_path = f"uploads/{filename}"

    if not pdf_path and not image_path:
        raise HTTPException(status_code=400, detail="请上传试卷文件（PDF或图片）")

    paper = Paper(
        name=name, grade=grade, image_path=image_path,
        pdf_path=pdf_path, source=source, created_by=current_user.id
    )
    db.add(paper)
    await db.commit()
    await db.refresh(paper)

    return {"id": paper.id, "pdf_path": pdf_path, "image_path": image_path, "message": "试卷已上传"}


@router.get("/{p_id}", response_model=PaperResponse)
async def get_paper(
    p_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取试卷详情"""
    paper = await db.get(Paper, p_id)
    if not paper:
        raise NotFoundException("试卷")

    data = paper.to_dict()

    # 获取关联题目
    result = await db.execute(
        select(Question)
        .where(Question.paper_id == p_id)
        .order_by(Question.paper_question_number)
    )
    questions = result.scalars().all()
    data["questions"] = [q.to_dict() for q in questions]

    return PaperResponse(**data)


@router.delete("/{p_id}", response_model=dict)
async def delete_paper(
    p_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除试卷"""
    paper = await db.get(Paper, p_id)
    if not paper:
        raise NotFoundException("试卷")

    # 解除关联题目的引用
    result = await db.execute(
        select(Question).where(Question.paper_id == p_id)
    )
    questions = result.scalars().all()
    for q in questions:
        q.paper_id = None
        q.paper_question_number = None

    await db.delete(paper)
    await db.commit()
    return {"message": "试卷已删除"}


@router.get("/{p_id}/download")
async def download_paper(
    p_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载试卷PDF"""
    paper = await db.get(Paper, p_id)
    if not paper:
        raise NotFoundException("试卷")

    if paper.pdf_path:
        full_path = os.path.join(settings.UPLOAD_DIR, os.path.basename(paper.pdf_path))
        if os.path.exists(full_path):
            return FileResponse(
                full_path,
                media_type="application/pdf",
                filename=f"{paper.name}.pdf"
            )

    raise HTTPException(status_code=404, detail="该试卷没有PDF文件")


@router.post("/{p_id}/answer", response_model=dict)
async def upload_paper_answer(
    p_id: int,
    answer_pdf: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传答案PDF"""
    paper = await db.get(Paper, p_id)
    if not paper:
        raise NotFoundException("试卷")

    if not answer_pdf.filename or answer_pdf.filename.rsplit(".", 1)[-1].lower() not in ALLOWED_PDF_EXTENSIONS:
        raise HTTPException(status_code=400, detail="请上传PDF格式的答案")

    filename = f"answer_{uuid.uuid4().hex}_{answer_pdf.filename}"
    upload_path = os.path.join(settings.UPLOAD_DIR, filename)
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    with open(upload_path, "wb") as f:
        content = await answer_pdf.read()
        f.write(content)

    paper.answer_pdf_path = f"uploads/{filename}"
    await db.commit()

    return {"message": "答案已上传", "answer_pdf_path": paper.answer_pdf_path}


@router.get("/{p_id}/answer/download")
async def download_paper_answer(
    p_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载答案PDF"""
    paper = await db.get(Paper, p_id)
    if not paper:
        raise NotFoundException("试卷")

    if paper.answer_pdf_path:
        full_path = os.path.join(settings.UPLOAD_DIR, os.path.basename(paper.answer_pdf_path))
        if os.path.exists(full_path):
            return FileResponse(
                full_path,
                media_type="application/pdf",
                filename=f"{paper.name}_答案.pdf"
            )

    raise HTTPException(status_code=404, detail="该试卷没有上传答案")


@router.post("/{p_id}/questions", response_model=dict)
async def add_paper_question(
    p_id: int,
    data: AddPaperQuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """向试卷添加题目"""
    paper = await db.get(Paper, p_id)
    if not paper:
        raise NotFoundException("试卷")

    # 从 answer_analysis 中提取标准答案
    correct_answer = extract_answer_from_analysis(data.answer_analysis or '')

    question = Question(
        title=data.title,
        content=data.content,
        tags=data.tags,
        difficulty=data.difficulty,
        answer_analysis=data.answer_analysis,
        correct_answer=correct_answer,
        paper_question_number=data.paper_question_number,
        grade=data.grade,
        source=f"{paper.name} 第{data.paper_question_number or '?'}题",
        image_path=paper.image_path,
        paper_id=p_id,
        created_by=current_user.id
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)

    return {"id": question.id, "message": "题目已添加"}

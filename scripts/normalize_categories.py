"""
题目分类标准化脚本

使用方法：
    cd math-question-bank
    python -m scripts.normalize_categories
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import async_session
from backend.models.question import Question
from backend.models.category import normalize_category, STANDARD_CATEGORIES
from sqlalchemy import select, func


async def get_current_categories():
    """获取当前所有分类"""
    async with async_session() as db:
        result = await db.execute(
            select(
                Question.category,
                func.count(Question.id).label('count')
            )
            .where(Question.category != '')
            .group_by(Question.category)
            .order_by(func.count(Question.id).desc())
        )
        return [(row[0], row[1]) for row in result.all()]


async def normalize_all_categories(dry_run=True):
    """标准化所有题目的分类"""
    async with async_session() as db:
        result = await db.execute(select(Question))
        questions = result.scalars().all()

        updated = 0
        unchanged = 0
        skipped = 0
        changes = []

        for q in questions:
            if not q.category:
                skipped += 1
                continue

            normalized = normalize_category(q.category)
            if normalized != q.category:
                old_category = q.category
                if not dry_run:
                    q.category = normalized
                updated += 1
                changes.append({
                    "id": q.id,
                    "old": old_category,
                    "new": normalized
                })
            else:
                unchanged += 1

        if not dry_run:
            await db.commit()

        return {
            "total": len(questions),
            "updated": updated,
            "unchanged": unchanged,
            "skipped": skipped,
            "changes": changes
        }


async def main():
    """主函数"""
    print("=" * 60)
    print("题目分类标准化工具")
    print("=" * 60)

    # 显示标准分类
    print("\n【标准分类】")
    for cat, keywords in STANDARD_CATEGORIES.items():
        print(f"  {cat}: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}")

    # 显示当前分类
    print("\n【数据库当前分类】")
    categories = await get_current_categories()
    for name, count in categories:
        normalized = normalize_category(name)
        status = "✓" if normalized == name else f"→ {normalized}"
        print(f"  {name}: {count} 题 {status}")

    # 询问是否执行
    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        print("\n【执行标准化】")
        result = await normalize_all_categories(dry_run=False)
        print(f"  总题数: {result['total']}")
        print(f"  已更新: {result['updated']}")
        print(f"  未改变: {result['unchanged']}")
        print(f"  已跳过: {result['skipped']}")
        if result['changes']:
            print("\n  变更详情:")
            for change in result['changes'][:20]:
                print(f"    ID {change['id']}: {change['old']} → {change['new']}")
            if len(result['changes']) > 20:
                print(f"    ... 还有 {len(result['changes']) - 20} 条变更")
    else:
        print("\n【预览模式】使用 --apply 参数执行实际更新")
        result = await normalize_all_categories(dry_run=True)
        print(f"  总题数: {result['total']}")
        print(f"  将更新: {result['updated']}")
        print(f"  未改变: {result['unchanged']}")
        print(f"  已跳过: {result['skipped']}")
        if result['changes']:
            print("\n  预览变更:")
            for change in result['changes'][:20]:
                print(f"    ID {change['id']}: {change['old']} → {change['new']}")
            if len(result['changes']) > 20:
                print(f"    ... 还有 {len(result['changes']) - 20} 条变更")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

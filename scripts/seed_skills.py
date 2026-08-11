#!/usr/bin/env python3
"""Seed the initial skill catalog."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.config import get_settings
from app.db.client import close_mongodb_connection, connect_to_mongodb, get_database
from app.db.repositories.skill_repository import SkillRepository
from app.models.skill import SkillCreate

INITIAL_SKILLS = [
    SkillCreate(
        skill_id="javascript",
        name="JavaScript",
        category="technical",
        description="Core JavaScript programming",
        verification_sources=["https://developer.mozilla.org/en-US/docs/Web/JavaScript"],
    ),
    SkillCreate(
        skill_id="javascript.arrays",
        name="JavaScript Arrays",
        category="technical",
        parent_skill_id="javascript",
        prerequisites=["javascript"],
    ),
    SkillCreate(
        skill_id="python",
        name="Python",
        category="technical",
        description="Core Python programming",
        verification_sources=["https://docs.python.org/3/"],
    ),
    SkillCreate(
        skill_id="dsa",
        name="Data Structures & Algorithms",
        category="dsa",
        description="Core DSA competency",
    ),
    SkillCreate(
        skill_id="dsa.arrays",
        name="Arrays",
        category="dsa",
        parent_skill_id="dsa",
        prerequisites=["dsa"],
    ),
    SkillCreate(
        skill_id="dsa.strings",
        name="Strings",
        category="dsa",
        parent_skill_id="dsa",
        prerequisites=["dsa"],
    ),
    SkillCreate(
        skill_id="dsa.hashing",
        name="Hashing",
        category="dsa",
        parent_skill_id="dsa",
        prerequisites=["dsa.arrays"],
    ),
    SkillCreate(
        skill_id="dsa.recursion",
        name="Recursion",
        category="dsa",
        parent_skill_id="dsa",
        prerequisites=["dsa"],
    ),
    SkillCreate(
        skill_id="dsa.linked_lists",
        name="Linked Lists",
        category="dsa",
        parent_skill_id="dsa",
        prerequisites=["dsa"],
    ),
    SkillCreate(
        skill_id="dsa.trees",
        name="Trees",
        category="dsa",
        parent_skill_id="dsa",
        prerequisites=["dsa.recursion"],
    ),
    SkillCreate(
        skill_id="aptitude",
        name="Aptitude",
        category="aptitude",
        description="General aptitude assessment",
    ),
    SkillCreate(
        skill_id="aptitude.quantitative",
        name="Quantitative Aptitude",
        category="aptitude",
        parent_skill_id="aptitude",
    ),
    SkillCreate(
        skill_id="aptitude.logical",
        name="Logical Reasoning",
        category="aptitude",
        parent_skill_id="aptitude",
    ),
    SkillCreate(
        skill_id="aptitude.verbal",
        name="Verbal Reasoning",
        category="aptitude",
        parent_skill_id="aptitude",
    ),
    SkillCreate(
        skill_id="communication",
        name="Communication",
        category="soft",
        description="Professional communication skills",
    ),
    SkillCreate(
        skill_id="soft_skills",
        name="Soft Skills",
        category="soft",
        description="Workplace behavioral competencies",
    ),
]


async def seed() -> None:
    settings = get_settings()
    await connect_to_mongodb(settings)
    db = get_database()
    repo = SkillRepository(db)

    for skill in INITIAL_SKILLS:
        result = await repo.upsert(skill)
        print(f"Seeded: {result.skill_id}")

    count = await repo.count()
    print(f"Total skills in catalog: {count}")
    await close_mongodb_connection()


if __name__ == "__main__":
    asyncio.run(seed())

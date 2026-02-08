"""Seed the database with test users."""

import asyncio

from sqlalchemy import select

from src.auth.security import hash_password
from src.models.database import async_session
from src.models.user import StudentProfile, User

USERS = [
    {
        "email": "admin@eduagi.com",
        "password": "admin123!",
        "name": "Admin User",
        "role": "admin",
    },
    {
        "email": "teacher@eduagi.com",
        "password": "teacher123!",
        "name": "Ms. Johnson",
        "role": "teacher",
    },
    {
        "email": "student@eduagi.com",
        "password": "student123!",
        "name": "Alex Student",
        "role": "student",
        "profile": {
            "learning_style": "visual",
            "pace": "moderate",
            "grade_level": "10th",
            "strengths": ["math", "science"],
            "weaknesses": ["history"],
        },
    },
    {
        "email": "maria@eduagi.com",
        "password": "maria123!",
        "name": "Maria Garcia",
        "role": "student",
        "profile": {
            "learning_style": "auditory",
            "pace": "fast",
            "grade_level": "11th",
            "strengths": ["english", "art"],
            "weaknesses": ["physics", "calculus"],
        },
    },
    {
        "email": "james@eduagi.com",
        "password": "james123!",
        "name": "James Chen",
        "role": "student",
        "profile": {
            "learning_style": "kinesthetic",
            "pace": "slow",
            "grade_level": "9th",
            "strengths": ["programming", "logic"],
            "weaknesses": ["writing", "biology"],
        },
    },
]


async def seed():
    async with async_session() as session:
        created = 0
        skipped = 0

        for u in USERS:
            result = await session.execute(select(User).where(User.email == u["email"]))
            if result.scalars().first():
                print(f"  skip  {u['email']} (already exists)")
                skipped += 1
                continue

            user = User(
                email=u["email"],
                password_hash=hash_password(u["password"]),
                name=u["name"],
                role=u.get("role", "student"),
                is_active=True,
            )
            session.add(user)
            await session.flush()

            profile_data = u.get("profile", {})
            profile = StudentProfile(
                user_id=user.id,
                learning_style=profile_data.get("learning_style", "balanced"),
                pace=profile_data.get("pace", "moderate"),
                grade_level=profile_data.get("grade_level"),
                strengths=profile_data.get("strengths"),
                weaknesses=profile_data.get("weaknesses"),
            )
            session.add(profile)
            await session.flush()

            print(f"  added {u['email']} ({u.get('role', 'student')})")
            created += 1

        await session.commit()
        print(f"\nDone: {created} created, {skipped} skipped")


if __name__ == "__main__":
    print("Seeding users...\n")
    asyncio.run(seed())

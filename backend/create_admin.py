"""
Script de création du compte admin initial.
À exécuter une seule fois après le premier démarrage :

  docker compose exec backend python create_admin.py
"""
import asyncio
import os
import uuid
import bcrypt
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.models import User

DATABASE_URL = os.environ["DATABASE_URL"]

async def main():
    username = os.environ.get("ADMIN_USERNAME", "admin")
    password = os.environ.get("ADMIN_PASSWORD", "changeme")
    email    = os.environ.get("ADMIN_EMAIL", "admin@foodtracker.local")

    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        existing = (await session.execute(select(User).where(User.username == username))).scalar_one_or_none()
        if existing:
            print(f"L'utilisateur '{username}' existe déjà.")
            return

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User(id=uuid.uuid4(), username=username, email=email, hashed_password=hashed, is_admin=True)
        session.add(user)
        await session.commit()
        print(f"Admin '{username}' créé avec succès.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())

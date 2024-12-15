from typing import Optional

from database.models import async_session
from database.models import User, Admin, Task
from sqlalchemy import select, update, delete, desc

async def set_user(tg_id):
    async with async_session() as session:
        async with session.begin():
            user = await session.scalar(select(User).where(User.tg_id == tg_id))
            if not user:
                user = User(tg_id=tg_id)
                session.add(user)
            await session.commit()

async def get_all_users(only_clients: bool = False):
    async with async_session() as session:
        async with session.begin():
            query = select(User.tg_id)
            if only_clients:
                query = query.where(User.is_client == 1)

            result = await session.execute(query)
            user_ids = result.scalars().all()
            return user_ids

async def mark_user_as_client(tg_id: int):
    async with async_session() as session:
        async with session.begin():
            stmt = select(User).where(User.tg_id == tg_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                user.is_client = True
                session.add(user)

async def add_task(run_at: str,
                   news_text: str,
                   button_text: str | None = None,
                   button_url: str | None = None,
                   file_data: Optional[str] | None = None):
    async with async_session() as session:
        async with session.begin():
            task = Task(
                run_at=run_at,
                news_text=news_text,
                button_text=button_text,
                button_url=button_url,
                file_data=file_data
            )
            session.add(task)

async def get_task(run_at: str):
    async with async_session() as session:
        async with session.begin():
            stmt = select(Task).where(Task.run_at == run_at)
            result = await session.execute(stmt)
            task = result.scalar_one_or_none()

            if task:
                return {
                    "id": task.id,
                    "run_at": task.run_at,
                    "news_text": task.news_text,
                    "button_text": task.button_text,
                    "button_url": task.button_url,
                    "file_data": task.file_data,
                    "is_executed": task.is_executed,
                }
            return None

async def remove_task(task_id: int):
    async with async_session() as session:
        async with session.begin():
            stmt = select(Task).where(Task.id == task_id)
            result = await session.execute(stmt)
            task = result.scalar_one_or_none()

            if task:
                await session.delete(task)
from sqlalchemy import ForeignKey, String, BigInteger, Integer, Boolean, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

engine = create_async_engine(url="sqlite+aiosqlite:///db.sqlite3", echo=False)

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    is_client: Mapped[int] = mapped_column(Boolean, default=False)

class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)

class Task(Base):
    __tablename__ = 'tasks'

    id: Mapped[int] = mapped_column(primary_key=True)
    run_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    news_text: Mapped[str] = mapped_column(String, nullable=False)
    button_text: Mapped[str] = mapped_column(String, nullable=True)
    button_url: Mapped[str] = mapped_column(String, nullable=True)
    file_data: Mapped[str] = mapped_column(String, nullable=True)
    is_executed: Mapped[bool] = mapped_column(Boolean, default=False)

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
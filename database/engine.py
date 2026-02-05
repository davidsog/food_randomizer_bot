import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from database.models import Base

# Пока используем SQLite (файл db.sqlite3 создастся сам)
# В будущем здесь будет проверка: если на сервере -> подключаем Postgres
DB_URL = "sqlite+aiosqlite:///db.sqlite3"

engine = create_async_engine(DB_URL, echo=True)

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Функция создания таблиц (запустим её при старте бота)
async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Функция удаления таблиц (понадобится, если захотим сбросить всё)
async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
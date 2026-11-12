import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from app.config import settings

# Configure engine with connection settings for SQLite or PostgreSQL
is_sqlite = "sqlite" in settings.DATABASE_URL
engine_kwargs = {}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    **engine_kwargs
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db():
    """Dependency yielding an active asynchronous database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initializes and migrates all registered database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # SQLite lightweight schema evolution: ensure new columns exist
        if is_sqlite:
            # Users table: add name if missing
            try:
                await conn.execute(text("ALTER TABLE users ADD COLUMN name VARCHAR(128)"))
            except Exception:
                pass
            
            # GenerationJobs table: add configuration if missing
            try:
                await conn.execute(text("ALTER TABLE generation_jobs ADD COLUMN configuration JSON"))
            except Exception:
                pass

            # GeneratedAssets table: add original_prompt, thumbnail_path, metadata if missing
            try:
                await conn.execute(text("ALTER TABLE generated_assets ADD COLUMN original_prompt TEXT"))
            except Exception:
                pass
            try:
                await conn.execute(text("ALTER TABLE generated_assets ADD COLUMN thumbnail_path VARCHAR(512)"))
            except Exception:
                pass
            try:
                await conn.execute(text("ALTER TABLE generated_assets ADD COLUMN metadata JSON"))
            except Exception:
                pass

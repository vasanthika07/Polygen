import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from app.config import settings

# Configure engine with connection settings for SQLite or PostgreSQL
db_url = settings.RESOLVED_DATABASE_URL if hasattr(settings, "RESOLVED_DATABASE_URL") else settings.DATABASE_URL
is_sqlite = "sqlite" in db_url
engine_kwargs = {}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_async_engine(
    db_url,
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

    # Ensure default verified demo user exists for seamless authentication
    async with AsyncSessionLocal() as session:
        try:
            from app.models.user import User
            from app.core.security import get_password_hash
            from sqlalchemy.future import select
            from sqlalchemy import func

            res = await session.execute(
                select(User).where(func.lower(User.email) == "demo_creator@polygen.ai")
            )
            demo_user = res.scalars().first()
            if not demo_user:
                demo_user = User(
                    id="usr_demo_creator_polygen_2026",
                    name="Demo Creator",
                    username="demo_creator",
                    email="demo_creator@polygen.ai",
                    password_hash=get_password_hash("PolyGen2026Secure!"),
                )
                session.add(demo_user)
                await session.commit()
            else:
                from app.core.security import verify_password
                if not verify_password("PolyGen2026Secure!", demo_user.password_hash):
                    demo_user.password_hash = get_password_hash("PolyGen2026Secure!")
                    await session.commit()
        except Exception:
            pass

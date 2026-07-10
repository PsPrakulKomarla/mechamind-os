from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


def _engine_kwargs():
    url = settings.DATABASE_URL
    if url.startswith("sqlite"):
        return {
            "echo": settings.DB_ECHO,
            "future": True,
            "connect_args": {"check_same_thread": False},
        }
    return {
        "echo": settings.DB_ECHO,
        "pool_pre_ping": True,
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
    }


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs())

async_session_maker = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False,
)

async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    from app.db.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    await engine.dispose()
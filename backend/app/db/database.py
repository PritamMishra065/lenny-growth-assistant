"""
Database connection management using SQLAlchemy async engine.
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.config import settings
import structlog

logger = structlog.get_logger()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_ENV == "development",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# Session factory
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields a database session."""
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables on startup."""
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title VARCHAR(255) DEFAULT 'New Chat',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                model_provider VARCHAR(50) DEFAULT 'ollama',
                model_name VARCHAR(100) DEFAULT 'llama3.1:8b',
                metadata JSONB DEFAULT '{}'
            );
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                sources JSONB DEFAULT '[]',
                artifact JSONB DEFAULT NULL,
                skill_used VARCHAR(50),
                model_provider VARCHAR(50),
                model_name VARCHAR(100),
                tokens_used INTEGER,
                latency_ms INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON sessions(updated_at);
        """))

    logger.info("database_initialized")


async def check_db_health() -> bool:
    """Check if the database connection is healthy."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return False


async def close_db():
    """Close the database engine on shutdown."""
    await engine.dispose()
    logger.info("database_connection_closed")

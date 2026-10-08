import asyncio
import os
import shutil
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.database import Base, get_db
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def temp_storage(tmp_path: Path):
    """Provide isolated temporary directories for file storage during testing."""
    orig_storage = settings.STORAGE_DIR
    orig_certs = settings.CERTIFICATES_DIR
    orig_archives = settings.ARCHIVES_DIR

    test_storage = tmp_path / "test_storage"
    test_certs = test_storage / "certificates"
    test_archives = test_storage / "archives"

    test_storage.mkdir(parents=True, exist_ok=True)
    test_certs.mkdir(parents=True, exist_ok=True)
    test_archives.mkdir(parents=True, exist_ok=True)

    settings.STORAGE_DIR = test_storage
    settings.CERTIFICATES_DIR = test_certs
    settings.ARCHIVES_DIR = test_archives

    yield test_storage

    # Restore original settings
    settings.STORAGE_DIR = orig_storage
    settings.CERTIFICATES_DIR = orig_certs
    settings.ARCHIVES_DIR = orig_archives


@pytest_asyncio.fixture(scope="function")
async def test_db_engine(tmp_path: Path) -> AsyncGenerator[AsyncEngine, None]:
    """Create a temporary sqlite test database engine."""
    db_file = tmp_path / "test_db.sqlite3"
    test_db_url = f"sqlite+aiosqlite:///{db_file}"

    engine = create_async_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db_session(test_db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated database session for a test."""
    session_maker = async_sessionmaker(
        bind=test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(
    test_db_engine: AsyncEngine,
    temp_storage: Path,
) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP test client with overridden database dependency."""
    session_maker = async_sessionmaker(
        bind=test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    # Also temporarily override AsyncSessionLocal in app.services.processor to use test DB
    import app.services.processor as processor_module
    orig_session_maker = processor_module.AsyncSessionLocal
    processor_module.AsyncSessionLocal = session_maker

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    processor_module.AsyncSessionLocal = orig_session_maker
    app.dependency_overrides.clear()

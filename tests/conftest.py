"""
Pytest configuration and fixtures for the entire test suite.
Provides common fixtures for API, database, workers, and integration tests.
"""

import asyncio
import os
import sys
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from apps.api.main import app
from apps.api.core.database import Base, get_db
from apps.api.core.config import settings
from apps.api.core.redis import redis_client


# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/research_checker_test"
)
TEST_DATABASE_URL_SYNC = TEST_DATABASE_URL.replace("+asyncpg", "")


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
def test_db_session_sync():
    """Create synchronous test database session for workers."""
    engine = create_engine(TEST_DATABASE_URL_SYNC, echo=False)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.rollback()
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def override_get_db(test_db_session):
    """Override the get_db dependency for API tests."""
    async def _override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_client(override_get_db) -> Generator[TestClient, None, None]:
    """Create test client for synchronous API tests."""
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def async_test_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client for async API tests."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def test_redis():
    """Create test Redis client."""
    test_redis_client = redis_client
    await test_redis_client.connect()

    # Clear test data
    await test_redis_client.redis.flushdb()

    yield test_redis_client

    # Cleanup
    await test_redis_client.redis.flushdb()
    await test_redis_client.disconnect()


@pytest.fixture(scope="function")
def sample_pipeline_data():
    """Sample pipeline data for tests."""
    return {
        "name": "Test Pipeline",
        "metadata": {"test": True, "source": "pytest"}
    }


@pytest.fixture(scope="function")
def sample_claim_data():
    """Sample claim data for tests."""
    return {
        "text": "This is a test claim about artificial intelligence.",
        "claim_type": "factual",
        "confidence": 0.95,
        "evidence_type": "empirical",
        "source_span_start": 0,
        "source_span_end": 50,
        "is_foundational": False
    }


@pytest.fixture(scope="function")
def sample_dependency_data():
    """Sample dependency data for tests."""
    return {
        "relationship_type": "evidential",
        "confidence": 0.88,
        "strength": "strong",
        "explanation": "Claim B provides direct evidence for Claim A",
        "semantic_markers": ["therefore", "because"]
    }


@pytest.fixture(scope="function")
def sample_document_file():
    """Create a sample test document file."""
    import tempfile

    content = b"""Test Document for Research Analysis

    This is a test document containing several claims:

    1. Artificial intelligence is transforming modern society.
    2. Machine learning models require large amounts of training data.
    3. Neural networks are inspired by biological neurons.

    These claims can be analyzed for dependencies and contradictions.
    """

    with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture(scope="function")
def sample_pdf_file():
    """Create a sample PDF file for testing."""
    import tempfile
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
            c = canvas.Canvas(f.name, pagesize=letter)
            c.drawString(100, 750, "Test PDF Document")
            c.drawString(100, 730, "This PDF contains test claims.")
            c.drawString(100, 710, "AI is revolutionizing technology.")
            c.save()
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)
    except ImportError:
        pytest.skip("reportlab not installed")


@pytest.fixture(scope="function")
def mock_gemini_response():
    """Mock Gemini API response for testing."""
    return {
        "claims": [
            {
                "text": "Artificial intelligence is transforming modern society",
                "type": "factual",
                "confidence": 0.95,
                "evidence_type": "empirical"
            },
            {
                "text": "Machine learning requires large datasets",
                "type": "factual",
                "confidence": 0.92,
                "evidence_type": "empirical"
            }
        ]
    }


@pytest.fixture(scope="function")
def mock_gemini_dependency_response():
    """Mock Gemini dependency analysis response."""
    return {
        "dependencies": [
            {
                "source_claim_id": "claim-1",
                "target_claim_id": "claim-2",
                "relationship_type": "evidential",
                "confidence": 0.88,
                "strength": "strong",
                "explanation": "Claim 2 provides evidence for Claim 1"
            }
        ]
    }


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables for each test."""
    original_env = os.environ.copy()

    # Set test environment
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(scope="function")
def test_pipeline_id():
    """Generate a test pipeline ID."""
    return str(uuid4())


@pytest.fixture(scope="function")
def test_claim_id():
    """Generate a test claim ID."""
    return str(uuid4())


@pytest.fixture(scope="function")
def test_document_id():
    """Generate a test document ID."""
    return str(uuid4())


# Markers for different test types
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "worker: Worker tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "database: Database tests")
    config.addinivalue_line("markers", "frontend: Frontend tests")
    config.addinivalue_line("markers", "smoke: Smoke tests")

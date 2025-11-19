"""
Test script for API startup and basic functionality
Run this to verify the FastAPI application starts correctly
"""
import asyncio
import sys
from core.config import settings
from core.database import init_db, close_db, get_db
from core.redis import redis_client

async def test_configuration():
    """Test configuration loading"""
    print("\n" + "=" * 60)
    print("Testing Configuration")
    print("=" * 60)

    print(f"\nApp Name: {settings.APP_NAME}")
    print(f"Version: {settings.VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Port: {settings.PORT}")

    print(f"\nDatabase URL: {settings.DATABASE_URL[:30]}..." if len(settings.DATABASE_URL) > 30 else settings.DATABASE_URL)
    print(f"Redis URL: {settings.REDIS_URL}")
    print(f"Gemini Model: {settings.GEMINI_MODEL}")
    print(f"Gemini API Key: {'***' + settings.GEMINI_API_KEY[-4:] if len(settings.GEMINI_API_KEY) > 10 else 'Not set'}")

    print(f"\nUpload Dir: {settings.UPLOAD_DIR}")
    print(f"Export Dir: {settings.EXPORT_DIR}")
    print(f"Max Upload Size: {settings.MAX_UPLOAD_SIZE / (1024*1024):.0f}MB")

    optional_configs = []
    if settings.CLERK_SECRET_KEY:
        optional_configs.append("Clerk Auth")
    if settings.SENTRY_DSN:
        optional_configs.append("Sentry")

    if optional_configs:
        print(f"\nOptional configs enabled: {', '.join(optional_configs)}")
    else:
        print(f"\nOptional configs: None (minimal setup)")

    print("\n✅ Configuration loaded successfully")
    return True

async def test_database():
    """Test database connectivity"""
    print("\n" + "=" * 60)
    print("Testing Database Connection")
    print("=" * 60)

    try:
        print("\nConnecting to database...")
        await init_db()
        print("✅ Database connection established")

        # Test session
        print("\nTesting database session...")
        async with get_db() as session:
            result = await session.execute("SELECT 1")
            print("✅ Database session works")

        return True

    except Exception as e:
        print(f"\n❌ Database error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL is running")
        print("2. Check DATABASE_URL in .env")
        print("3. Verify database exists")
        print("4. Check credentials")
        return False

async def test_redis():
    """Test Redis connectivity"""
    print("\n" + "=" * 60)
    print("Testing Redis Connection")
    print("=" * 60)

    try:
        print("\nConnecting to Redis...")
        await redis_client.connect()
        print("✅ Redis connection established")

        # Test set/get
        print("\nTesting Redis operations...")
        test_key = "test:api:startup"
        test_value = "Hello from API test!"

        await redis_client.set(test_key, test_value, ttl=60)
        retrieved = await redis_client.get(test_key)

        if retrieved == test_value:
            print("✅ Redis set/get works")
        else:
            print(f"⚠️  Retrieved value doesn't match: {retrieved}")

        # Test JSON
        print("\nTesting JSON storage...")
        test_data = {"status": "testing", "count": 42}
        await redis_client.set_json("test:json", test_data, ttl=60)
        retrieved_json = await redis_client.get_json("test:json")

        if retrieved_json == test_data:
            print("✅ Redis JSON operations work")
        else:
            print(f"⚠️  Retrieved JSON doesn't match: {retrieved_json}")

        # Cleanup
        await redis_client.delete(test_key)
        await redis_client.delete("test:json")

        return True

    except Exception as e:
        print(f"\n❌ Redis error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Redis is running")
        print("2. Check REDIS_URL in .env")
        print("3. Verify Redis is accessible")
        return False

async def test_api_imports():
    """Test that all API modules can be imported"""
    print("\n" + "=" * 60)
    print("Testing Module Imports")
    print("=" * 60)

    try:
        print("\nImporting main app...")
        from main import app
        print(f"✅ FastAPI app loaded: {app.title}")

        print("\nImporting services...")
        from services.gemini.client import gemini_client
        from services.gemini.prompts import (
            ClaimExtractionPrompt,
            DependencyAnalysisPrompt,
            ContradictionDetectionPrompt,
            SynthesisPrompt
        )
        print("✅ Gemini client and prompts loaded")

        return True

    except Exception as e:
        print(f"\n❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print(" " * 20 + "API STARTUP TESTS")
    print("=" * 80)

    results = {}

    # Test configuration
    results['config'] = await test_configuration()

    # Test imports
    results['imports'] = await test_api_imports()

    # Test database
    results['database'] = await test_database()

    # Test Redis
    results['redis'] = await test_redis()

    # Cleanup
    await close_db()
    await redis_client.close()

    # Summary
    print("\n" + "=" * 80)
    print(" " * 30 + "TEST SUMMARY")
    print("=" * 80)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.upper():20s} {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 All tests passed! API is ready to start.")
        print("\nTo start the API, run:")
        print("  cd apps/api")
        print("  python main.py")
        print("\nOr with uvicorn:")
        print("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")

    print("=" * 80 + "\n")

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    asyncio.run(main())

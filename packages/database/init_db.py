"""
Database initialization script
Creates all tables and runs initial migrations
"""
import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import models to ensure they're registered
from models import Base

async def init_database():
    """Initialize database schema"""

    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("❌ DATABASE_URL environment variable not set!")
        print("\nPlease set DATABASE_URL in .env file:")
        print("  DATABASE_URL=postgresql://user:password@host:port/database")
        sys.exit(1)

    # Convert to async URL if needed
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')

    print("=" * 60)
    print("Database Initialization")
    print("=" * 60)
    print(f"\nDatabase URL: {database_url[:40]}...")

    try:
        # Create engine
        print("\n[1/3] Creating database engine...")
        engine = create_async_engine(
            database_url,
            echo=True,  # Show SQL statements
            pool_pre_ping=True
        )

        # Test connection
        print("\n[2/3] Testing database connection...")
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL")
            print(f"   Version: {version}")

        # Create all tables
        print("\n[3/3] Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("\n✅ Database initialized successfully!")
        print("\nCreated tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")

        # Show next steps
        print("\n" + "=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print("\n1. The database schema is now created")
        print("2. You can start the API with: python main.py")
        print("3. Or use Alembic for migrations: alembic upgrade head")
        print("\n" + "=" * 60)

        await engine.dispose()
        return True

    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()

        print("\nTroubleshooting:")
        print("1. Verify DATABASE_URL is correct")
        print("2. Ensure PostgreSQL is running")
        print("3. Check database credentials")
        print("4. Verify database exists")
        print("\nFor Railway:")
        print("  - Database is auto-created when you add PostgreSQL service")
        print("  - DATABASE_URL is automatically set")

        return False

async def check_tables():
    """Check what tables exist in the database"""

    database_url = os.getenv('DATABASE_URL')
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')

    engine = create_async_engine(database_url, echo=False)

    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))

            tables = [row[0] for row in result]

            if tables:
                print("\nExisting tables:")
                for table in tables:
                    print(f"  - {table}")
            else:
                print("\nNo tables found in database")

        await engine.dispose()

    except Exception as e:
        print(f"Error checking tables: {e}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Database initialization')
    parser.add_argument('--check', action='store_true', help='Check existing tables')
    args = parser.parse_args()

    if args.check:
        asyncio.run(check_tables())
    else:
        success = asyncio.run(init_database())
        sys.exit(0 if success else 1)

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker


SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./bucket.db" # telling python to use sqlite (would change if using postgres, etc)

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}) #connecting database with python

AsyncSessionLocal = async_sessionmaker(autocommit = False, autoflush=False, bind=engine, class_=AsyncSession) # temp transaction with the database

class Base(DeclarativeBase):
    pass

# manages the lifecycle of your database connections during a web request. FastAPI uses it as a dependency injected directly into your path operations.
async def get_db():
    async with AsyncSessionLocal() as db: # automatically opens a brand-new database session connection when a user hits an endpoint.
        yield db
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./bucket.db" # telling python to use sqlite (would change if using postgres, etc)

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}) #connecting database with python

SessionLocal = sessionmaker(autocommit = False, autoflush=False, bind=engine) # temp transaction with the database

class Base(DeclarativeBase):
    pass

# manages the lifecycle of your database connections during a web request. FastAPI uses it as a dependency injected directly into your path operations.
def get_db():
    with SessionLocal() as db: # automatically opens a brand-new database session connection when a user hits an endpoint.
        yield db
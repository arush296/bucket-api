# pyrefly: ignore [missing-import]
from fastapi import Depends, FastAPI, Request, HTTPException, status
# pyrefly: ignore [missing-import]
from fastapi.exceptions import RequestValidationError
# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
# pyrefly: ignore [missing-import]
from fastapi.templating import Jinja2Templates
# pyrefly: ignore [missing-import]
from starlette.exceptions import HTTPException as StarletteHTTPException
from database import Base, engine, get_db
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import select
from typing import Annotated
from datetime import datetime
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
# selectinload is a loading strategy provided by SQLAlchemy that allows you to efficiently load related objects in a single query using a JOIN. When you use selectinload, SQLAlchemy will generate a SQL query that retrieves the main objects (like posts) along with their related objects (like authors) in one go, instead of making separate queries for each related object. This can significantly improve performance by reducing the number of database round-trips, especially when dealing with one-to-many or many-to-many relationships. In our case, using selectinload(models.Post.author) allows us to fetch each post along with its associated author information in a single query, which is more efficient than fetching posts and then making additional queries to get each author's details.
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import selectinload 
# pyrefly: ignore [missing-import]
from contextlib import asynccontextmanager

import models
from routers import buckets, resources, users

# Create database tables
# Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title="Bucket API", lifespan=lifespan)

app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(buckets.router, prefix="/api/buckets", tags=["Buckets"]) # tags is to reorganise in swagger docs
app.include_router(resources.router, prefix="/api/resources", tags=["Resources"])



@app.get("/")
def read_root():
    return {"message": "Welcome to the Bucket API!"}
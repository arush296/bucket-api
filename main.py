from fastapi import Depends, FastAPI, Request, HTTPException, status
# from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from database import Base, engine, get_db
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Annotated
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload # selectinload is a loading strategy provided by SQLAlchemy that allows you to efficiently load related objects in a single query using a JOIN. When you use selectinload, SQLAlchemy will generate a SQL query that retrieves the main objects (like posts) along with their related objects (like authors) in one go, instead of making separate queries for each related object. This can significantly improve performance by reducing the number of database round-trips, especially when dealing with one-to-many or many-to-many relationships. In our case, using selectinload(models.Post.author) allows us to fetch each post along with its associated author information in a single query, which is more efficient than fetching posts and then making additional queries to get each author's details.
from contextlib import asynccontextmanager

import models
from schema import BucketCreate, BucketResponse, BucketUpdate, ResourceCreate, ResourceResponse, ResourceUpdate

# Create database tables
# Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title="Bucket API", lifespan=lifespan)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Bucket API!"}


# ==========================================
# BUCKET CRUD
# ==========================================

@app.get("/api/buckets", response_model=list[BucketResponse])
async def read_buckets(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Bucket)) # select in load not required as BucketResponse doesnt access the resources relationship
    return result.scalars().all()

@app.post("/api/buckets", response_model=BucketResponse, status_code=status.HTTP_201_CREATED)
async def create_bucket(bucket: BucketCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    db_result = await db.execute(select(models.Bucket.name).where(models.Bucket.name == bucket.name))
    result = db_result.scalars().first() # .scalars().first() hasnt been added directly to db_result because it will try to get the scalar of a db operation that is still being awaited which might lead to an error. So this way you only access the scalar after the db operation is completed. 
    if result:
        raise HTTPException(status_code=400, detail="Bucket name already exists")
    db_bucket = models.Bucket(name=bucket.name, description=bucket.description)
    db.add(db_bucket)
    await db.commit()
    await db.refresh(db_bucket)
    return db_bucket

@app.get("/api/buckets/{id}", response_model=BucketResponse)
async def read_bucket(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    db_result = await db.execute(select(models.Bucket).where(models.Bucket.id == id))
    result = db_result.scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="Bucket not found")
    return result


@app.patch("/api/buckets/{id}", response_model=BucketResponse)
async def update_bucket(id: int, bucket_update: BucketUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    db_result = await db.execute(select(models.Bucket).where(models.Bucket.id == id))
    result = db_result.scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="Bucket not found")
    update_data = bucket_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(result, key, value)
    result.updated_at = datetime.now()

    await db.commit()
    await db.refresh(result)
    return result


@app.delete("/api/buckets/{id}")
async def delete_bucket(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    db_result = await db.execute(select(models.Bucket).where(models.Bucket.id == id))
    db_bucket = db_result.scalars().first()
    if not db_bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")
    await db.delete(db_bucket)
    await db.commit()
    return {"message": "Bucket deleted successfully"}


# ==========================================
# RESOURCE CRUD
# ==========================================

@app.get("/api/resources", response_model=list[ResourceResponse])
async def read_resources(db:Annotated[AsyncSession, Depends(get_db)]):
    db_result = await db.execute(select(models.Resource))
    result = db_result.scalars().all()
    return result


@app.post("/api/resources", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(resource: ResourceCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    db_result = await db.execute(select(models.Bucket).where(models.Bucket.id == resource.bucket_id))
    result = db_result.scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="Bucket not found")
    db_resource = models.Resource(
        title=resource.title,
        url=resource.url,
        description=resource.description,
        source=resource.source,
        bucket_id=resource.bucket_id
    )
    db.add(db_resource) # no await required, it is a synch, non blocking method
    await db.commit()
    await db.refresh(db_resource)
    return db_resource


@app.get("/api/resources/{id}", response_model=ResourceResponse)
async def read_resource(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    db_result = await db.execute(select(models.Resource).where(models.Resource.id == id))
    result = db_result.scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="Resource not found")
    return result


@app.patch("/api/resources/{id}", response_model=ResourceResponse)
async def update_resource(id: int, resource_update: ResourceUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    db_result = await db.execute(select(models.Resource).where(models.Resource.id == id))
    result = db_result.scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="Resource not found")
        
    update_data = resource_update.model_dump(exclude_unset=True)
    
    # If bucket_id is being updated, verify the new bucket exists
    if "bucket_id" in update_data and update_data["bucket_id"] is not None:
        db_bucket_result = await db.execute(select(models.Bucket).where(models.Bucket.id == update_data["bucket_id"]))
        db_bucket = db_bucket_result.scalars().first()
        if not db_bucket:
            raise HTTPException(status_code=404, detail="Bucket not found")
            
    for key, value in update_data.items():
        setattr(result, key, value)
    
    result.updated_at = datetime.now()

    await db.commit()
    await db.refresh(result)
    return result


@app.delete("/api/resources/{id}")
async def delete_resource(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    db_result = await db.execute(select(models.Resource).where(models.Resource.id == id))
    result = db_result.scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="Resource not found")
    await db.delete(result)
    await db.commit()
    return {"message": "Resource deleted successfully"}

# all resources in a particular bucket
@app.get("/api/buckets/{id}/resources", response_model=list[ResourceResponse])
async def read_bucket_resources(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    db_result = await db.execute(select(models.Bucket).where(models.Bucket.id == id))
    result = db_result.scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="Bucket not found")
    db_resources_result = await db.execute(select(models.Resource).where(models.Resource.bucket_id == id))
    result = db_resources_result.scalars().all()
    return result
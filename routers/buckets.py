from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from datetime import datetime
from database import get_db
import models
from schema import BucketCreate, BucketResponse, BucketUpdate, ResourceResponse

router = APIRouter()

# ==========================================
# BUCKET CRUD
# ==========================================

# /api/buckets
@router.get("", response_model=list[BucketResponse])
async def read_buckets(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Bucket)) # select in load not required as BucketResponse doesnt access the resources relationship
    return result.scalars().all()

# /api/buckets
@router.post("", response_model=BucketResponse, status_code=status.HTTP_201_CREATED)
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

# /api/buckets/{id}
@router.get("/{id}", response_model=BucketResponse)
async def read_bucket(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    db_result = await db.execute(select(models.Bucket).where(models.Bucket.id == id))
    result = db_result.scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="Bucket not found")
    return result


# /api/buckets/{id}
@router.patch("/{id}", response_model=BucketResponse)
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


# /api/buckets/{id}
@router.delete("/{id}")
async def delete_bucket(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    db_result = await db.execute(select(models.Bucket).where(models.Bucket.id == id))
    db_bucket = db_result.scalars().first()
    if not db_bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")
    await db.delete(db_bucket)
    await db.commit()
    return {"message": "Bucket deleted successfully"}

# all resources in a particular bucket
# /api/buckets/{id}/resources
@router.get("/{id}/resources", response_model=list[ResourceResponse])
async def read_bucket_resources(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    db_result = await db.execute(select(models.Bucket).where(models.Bucket.id == id))
    result = db_result.scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="Bucket not found")
    db_resources_result = await db.execute(select(models.Resource).where(models.Resource.bucket_id == id))
    result = db_resources_result.scalars().all()
    return result
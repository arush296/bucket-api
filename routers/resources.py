# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status
# pyrefly: ignore [missing-import]
from sqlalchemy import select
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from datetime import datetime
from database import get_db
import models
from schema import ResourceCreate, ResourceResponse, ResourceUpdate

router = APIRouter()

# ==========================================
# RESOURCE CRUD
# ==========================================

# /api/resources
@router.get("", response_model=list[ResourceResponse])
async def read_resources(db:Annotated[AsyncSession, Depends(get_db)]):
    db_result = await db.execute(select(models.Resource))
    result = db_result.scalars().all()
    return result


# /api/resources
@router.post("", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
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


# /api/resources/{id}
@router.get("/{id}", response_model=ResourceResponse)
async def read_resource(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    db_result = await db.execute(select(models.Resource).where(models.Resource.id == id))
    result = db_result.scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="Resource not found")
    return result


# /api/resources/{id}
@router.patch("/{id}", response_model=ResourceResponse)
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


# /api/resources/{id}
@router.delete("/{id}")
async def delete_resource(id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    db_result = await db.execute(select(models.Resource).where(models.Resource.id == id))
    result = db_result.scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="Resource not found")
    await db.delete(result)
    await db.commit()
    return {"message": "Resource deleted successfully"}

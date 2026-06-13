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
import datetime

import models
from schema import BucketCreate, BucketResponse, BucketUpdate, ResourceCreate, ResourceResponse, ResourceUpdate

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bucket API")


@app.get("/")
def read_root():
    return {"message": "Welcome to the Bucket API!"}


# ==========================================
# BUCKET CRUD
# ==========================================

@app.get("/api/buckets", response_model=list[BucketResponse])
def read_buckets(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Bucket))
    return result.scalars().all()

@app.post("/api/buckets", response_model=BucketResponse, status_code=status.HTTP_201_CREATED)
def create_bucket(bucket: BucketCreate, db: Annotated[Session, Depends(get_db)]):
    if (bucket.name in (db.execute(select(models.Bucket.name)).scalars().all())):
        raise HTTPException(status_code=400, detail="Bucket name already exists")
    db_bucket = models.Bucket(name=bucket.name, description=bucket.description)
    db.add(db_bucket)
    db.commit()
    db.refresh(db_bucket)
    return db_bucket

@app.get("/api/buckets/{id}", response_model=BucketResponse)
def read_bucket(id: int, db: Annotated[Session, Depends(get_db)]):
    if (id not in (db.execute(select(models.Bucket.id)).scalars().all())):
        raise HTTPException(status_code=404, detail="Bucket not found")
    db_bucket = db.execute(select(models.Bucket).where(models.Bucket.id == id)).scalars().first()
    return db_bucket


@app.patch("/api/buckets/{id}", response_model=BucketResponse)
def update_bucket(id: int, bucket_update: BucketUpdate, db: Annotated[Session, Depends(get_db)]):
    if (id not in (db.execute(select(models.Bucket.id)).scalars().all())):
        raise HTTPException(status_code=404, detail="Bucket not found")

    db_bucket = db.execute(select(models.Bucket).where(models.Bucket.id == id)).scalars().first()
    
    # Update only the fields that were set in the request
    update_data = bucket_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_bucket, key, value)
    
    db_bucket.updated_at = datetime.now()

    db.commit()
    db.refresh(db_bucket)
    return db_bucket


@app.delete("/api/buckets/{id}")
def delete_bucket(id: int, db: Annotated[Session, Depends(get_db)]):
    db_bucket = db.execute(select(models.Bucket).where(models.Bucket.id == id)).scalars().first()
    if not db_bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")
    db.delete(db_bucket)
    db.commit()
    return {"message": "Bucket deleted successfully"}


# ==========================================
# RESOURCE CRUD
# ==========================================

@app.get("/api/resources", response_model=list[ResourceResponse])
def read_resources(db:Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Resource))
    return result.scalars().all()


@app.post("/api/resources", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
def create_resource(resource: ResourceCreate, db: Annotated[Session, Depends(get_db)]):
    buck_id = db.execute(select(models.Bucket.id)).scalars().all()
    if (resource.bucket_id not in buck_id):
        raise HTTPException(status_code=404, detail="Bucket not found")
    db_resource = models.Resource(
        title=resource.title,
        url=resource.url,
        description=resource.description,
        source=resource.source,
        bucket_id=resource.bucket_id
    )
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    return db_resource



@app.get("/api/resources/{id}", response_model=ResourceResponse)
def read_resource(id: int, db: Annotated[Session, Depends(get_db)]):
    db_res_id = db.execute(select(models.Resource.id)).scalars().all()
    if (id not in db_res_id):
        raise HTTPException(status_code=404, detail="Resource not found")
    db_resource = db.execute(select(models.Resource).where(models.Resource.id == id)).scalars().first()
    return db_resource


@app.patch("/api/resources/{id}", response_model=ResourceResponse)
def update_resource(id: int, resource_update: ResourceUpdate, db: Annotated[Session, Depends(get_db)]):
    if (id not in (db.execute(select(models.Resource.id)).scalars().all())):
        raise HTTPException(status_code=404, detail="Resource not found")
    db_resource = db.execute(select(models.Resource).where(models.Resource.id == id)).scalars().first()
        
    update_data = resource_update.model_dump(exclude_unset=True)
    
    # If bucket_id is being updated, verify the new bucket exists
    if "bucket_id" in update_data and update_data["bucket_id"] is not None:
        db_bucket = db.get(models.Bucket, update_data["bucket_id"])
        if db_bucket is None:
            raise HTTPException(status_code=404, detail="Bucket not found")
            
    for key, value in update_data.items():
        setattr(db_resource, key, value)
    
    db_resource.updated_at = datetime.now()

    db.commit()
    db.refresh(db_resource)
    return db_resource


@app.delete("/api/resources/{id}")
def delete_resource(id: int, db: Annotated[Session, Depends(get_db)]):
    db_resource = db.execute(select(models.Resource).where(models.Resource.id == id)).scalars().first()
    if not db_resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    db.delete(db_resource)
    db.commit()
    return {"message": "Resource deleted successfully"}

# all resources in a particular bucket
@app.get("/api/buckets/{id}/resources", response_model=list[ResourceResponse])
def read_bucket_resources(id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Bucket).where(models.Bucket.id == id)).scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="Bucket not found")
    result = db.execute(select(models.Resource).where(models.Resource.bucket_id == id)).scalars().all()
    return result
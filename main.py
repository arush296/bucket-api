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

@app.post("/api/buckets", response_model=BucketResponse, status_code=status.HTTP_201_CREATED)
def create_bucket(bucket: BucketCreate, db: Session = Depends(get_db)):
    db_bucket = models.Bucket(name=bucket.name, description=bucket.description)
    db.add(db_bucket)
    db.commit()
    db.refresh(db_bucket)
    return db_bucket


@app.get("/api/buckets", response_model=list[BucketResponse])
def read_buckets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    result = db.execute(select(models.Bucket).offset(skip).limit(limit))
    return result.scalars().all()


@app.get("/api/buckets/{id}", response_model=BucketResponse)
def read_bucket(id: int, db: Session = Depends(get_db)):
    db_bucket = db.get(models.Bucket, id)
    if db_bucket is None:
        raise HTTPException(status_code=404, detail="Bucket not found")
    return db_bucket


@app.put("/api/buckets/{id}", response_model=BucketResponse)
def update_bucket(id: int, bucket_update: BucketUpdate, db: Session = Depends(get_db)):
    db_bucket = db.get(models.Bucket, id)
    if db_bucket is None:
        raise HTTPException(status_code=404, detail="Bucket not found")
    
    # Update only the fields that were set in the request
    update_data = bucket_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_bucket, key, value)
        
    db.commit()
    db.refresh(db_bucket)
    return db_bucket


@app.delete("/api/buckets/{id}")
def delete_bucket(id: int, db: Session = Depends(get_db)):
    db_bucket = db.get(models.Bucket, id)
    if db_bucket is None:
        raise HTTPException(status_code=404, detail="Bucket not found")
    
    db.delete(db_bucket)
    db.commit()
    return {"message": "Bucket deleted successfully"}


# ==========================================
# RESOURCE CRUD
# ==========================================

@app.post("/api/resources", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
def create_resource(resource: ResourceCreate, db: Session = Depends(get_db)):
    # Verify the bucket exists first
    db_bucket = db.get(models.Bucket, resource.bucket_id)
    if db_bucket is None:
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


@app.get("/api/resources", response_model=list[ResourceResponse])
def read_resources(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    result = db.execute(select(models.Resource).offset(skip).limit(limit))
    return result.scalars().all()


@app.get("/api/resources/{id}", response_model=ResourceResponse)
def read_resource(id: int, db: Session = Depends(get_db)):
    db_resource = db.get(models.Resource, id)
    if db_resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    return db_resource


@app.put("/api/resources/{id}", response_model=ResourceResponse)
def update_resource(id: int, resource_update: ResourceUpdate, db: Session = Depends(get_db)):
    db_resource = db.get(models.Resource, id)
    if db_resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
        
    update_data = resource_update.model_dump(exclude_unset=True)
    
    # If bucket_id is being updated, verify the new bucket exists
    if "bucket_id" in update_data and update_data["bucket_id"] is not None:
        db_bucket = db.get(models.Bucket, update_data["bucket_id"])
        if db_bucket is None:
            raise HTTPException(status_code=404, detail="Bucket not found")
            
    for key, value in update_data.items():
        setattr(db_resource, key, value)
        
    db.commit()
    db.refresh(db_resource)
    return db_resource


@app.delete("/api/resources/{id}")
def delete_resource(id: int, db: Session = Depends(get_db)):
    db_resource = db.get(models.Resource, id)
    if db_resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
        
    db.delete(db_resource)
    db.commit()
    return {"message": "Resource deleted successfully"}
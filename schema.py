from database import Base
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr

# Buckets i.e. categories
class BucketBase(BaseModel):
    name: str = Field(example="Bucket Name", min_length=1, max_length=255)
    description: str = Field(example="Bucket Description", max_length=1000)

class BucketCreate(BucketBase):
    pass

class BucketResponse(BucketBase):
    id: int
    user_id: int
    created_at: datetime = Field(default=datetime.now(), example=datetime.now())
    updated_at: datetime = Field(default=datetime.now(), example=datetime.now())
    
    model_config = ConfigDict(
        from_attributes=True
    )

class BucketUpdate(BucketBase):
    name: str | None = Field(default=None, example="Bucket Name", min_length=1, max_length=255)
    description: str | None = Field(default=None, example="Bucket Description", max_length=1000)


# Resources to be put in bucket
class ResourceBase(BaseModel):
    title: str = Field(example="Resource Name", min_length=1, max_length=255)
    url: str = Field(example="https://example.com")
    description: str = Field(example="Resource Description", max_length=1000)
    source: str = Field(default="", example="Resource Source")
    bucket_id: int

class ResourceCreate(ResourceBase):
    pass

class ResourceResponse(ResourceBase):
    id: int
    created_at: datetime = Field(default=datetime.now(), example=datetime.now())
    updated_at: datetime = Field(default=datetime.now(), example=datetime.now())
    
    model_config = ConfigDict(
        from_attributes=True
    )

class ResourceUpdate(ResourceBase):
    title: str | None = Field(default=None, example="Resource Name", min_length=1, max_length=255)
    url: str | None = Field(default=None, example="https://example.com")
    description: str | None = Field(default=None, example="Resource Description", max_length=1000)
    source: str | None = Field(default=None, example="Resource Source")
    bucket_id: int | None = None


class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(min_length=4, max_length=255)

class UserResponse(UserBase):
    id: int
    created_at: datetime = Field(default=datetime.now(), example=datetime.now())
    updated_at: datetime = Field(default=datetime.now(), example=datetime.now())
    
    model_config = ConfigDict(
        from_attributes=True
    )

class Token(BaseModel):
    access_token: str
    token_type: str
# pyrefly: ignore [missing-import]
from datetime import timedelta
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
from schema import UserCreate, UserResponse, Token, UserUpdate
# pyrefly: ignore [missing-import]
from fastapi.security import OAuth2PasswordRequestForm
from config import settings
from auth import (hash_password, create_access_token, verify_password, verify_access_token, oauth2_scheme, CurrentUser)

router = APIRouter()

# create user
@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    db_result = await db.execute(select(models.User).where(models.User.email == user.email.lower()))
    result = db_result.scalars().first()
    if result:
        raise HTTPException(status_code=400, detail="User already exists")
    db_user = models.User(name=user.name, email=user.email.lower(), password_hash=hash_password(user.password))
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# user login
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Annotated[AsyncSession, Depends(get_db)]):
    db_result = await db.execute(select(models.User).where(models.User.email == form_data.username.lower()))
    result = db_result.scalars().first()
    if not result:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not verify_password(form_data.password, result.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token_expires =  timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(result.id)},
        expires_delta = access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=UserResponse)
# Client sends the JWT in the Authorization: Bearer <token> header.
# oauth2_scheme is a fastapi dependency which automatically extracts the token from the header
async def read_me(current_user: CurrentUser):
    return current_user
    # payload = verify_access_token(token)
    # # here payload will be the dictionary/payload that was passed when creating the token
    # if not payload:
    #     raise HTTPException(status_code=401, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    # user_id = payload["sub"]
    # db_result = await db.execute(select(models.User).where(models.User.id == int(user_id)))
    # result = db_result.scalars().first()
    # if not result:
    #     raise HTTPException(status_code=401, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    # return result

# update user
@router.patch("/{id}", response_model=UserResponse)
async def update_user(
    id: int,
    user_update: UserUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    db_result = await db.execute(select(models.User).where(models.User.id == id))
    result = db_result.scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    if result.id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to update this user")
        
    update_data = user_update.model_dump(exclude_unset=True)
    
    if "email" in update_data and update_data["email"] is not None:
        email_lower = update_data["email"].lower()
        conflict_result = await db.execute(select(models.User).where(models.User.email == email_lower, models.User.id != id))
        conflict = conflict_result.scalars().first()
        if conflict:
            raise HTTPException(status_code=400, detail="Email already registered by another user")
        result.email = email_lower
        
    if "name" in update_data and update_data["name"] is not None:
        result.name = update_data["name"]
        
    if "password" in update_data and update_data["password"] is not None:
        result.password_hash = hash_password(update_data["password"])
        
    result.updated_at = datetime.now()
    await db.commit()
    await db.refresh(result)
    return result

# delete user
@router.delete("/{id}")
async def delete_user(id: int, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    db_result = await db.execute(select(models.User).where(models.User.id == id))
    result = db_result.scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    if result.id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this user")
    await db.delete(result)
    await db.commit()
    return {"message": "User deleted successfully"}

# # get user
# @router.get("", response_model=UserResponse)
# async def read_users(db: Annotated[AsyncSession, Depends(get_db)]):
#     db_result = await db.execute(select(models.User))
#     result = db_result.scalars().first()
#     if not result:
#         raise HTTPException(status_code=404, detail="User not found")
#     return result
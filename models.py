from datetime import UTC, datetime
# pyrefly: ignore [missing-import]
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), onupdate=datetime.now())

    buckets: Mapped[list["Bucket"]] = relationship(back_populates="user")


class Bucket(Base):
    __tablename__ = "buckets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), onupdate=datetime.now())

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="buckets")
    resources: Mapped[list["Resource"]] = relationship(back_populates="bucket")

class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    url: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(255), nullable=True)
    bucket_id: Mapped[int] = mapped_column(ForeignKey("buckets.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), onupdate=datetime.now())

    bucket: Mapped[Bucket] = relationship(back_populates="resources")
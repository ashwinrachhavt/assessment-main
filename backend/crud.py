from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import schemas
from models import Base, Chat, FormSubmission

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: type[ModelType]):
        """CRUD helpers for SQLAlchemy models."""
        self.model = model

    async def get(
        self,
        db: AsyncSession,
        id: uuid.UUID | str | int,
        options: list | None = None,
    ) -> ModelType | None:
        statement = (
            select(self.model).filter(self.model.id == id).options(*(options or []))
        )
        result = await db.scalars(statement)
        return result.first()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        filters: list | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        statement = (
            select(self.model).filter(*(filters or [])).offset(skip).limit(limit)
        )
        result = await db.scalars(statement)
        return result.all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(
            **obj_in_data, created_at=datetime.now(UTC).replace(tzinfo=None)
        )  # type: ignore

        db.add(db_obj)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        obj_data = jsonable_encoder(
            db_obj, exclude={"embedding", "vector", "routing_options"}
        )
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = jsonable_encoder(obj_in, exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: str) -> ModelType:
        obj = await db.get(self.model, id)
        await db.delete(obj)
        await db.commit()
        return obj


class CRUDChat(CRUDBase[Chat, schemas.ChatCreate, schemas.ChatUpdate]):
    pass


chat = CRUDChat(Chat)


class CRUDFormSubmission(
    CRUDBase[FormSubmission, schemas.FormSubmissionCreate, schemas.FormSubmissionUpdate]
):
    pass


form = CRUDFormSubmission(FormSubmission)

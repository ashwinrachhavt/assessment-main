from __future__ import annotations

from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Chat(BaseModel):
    id: str
    created_at: datetime
    messages: list

    model_config = ConfigDict(from_attributes=True)


class ChatCreate(BaseModel):
    messages: list = Field(default_factory=list)


class ChatUpdate(BaseModel):
    messages: list


class FormSubmission(BaseModel):
    id: str
    created_at: datetime
    # Some legacy rows may have nulls; keep response tolerant
    name: str | None = None
    phone_number: str | None = None
    email: str | None = None
    status: int | None = None

    model_config = ConfigDict(from_attributes=True)


class FormSubmissionCreate(BaseModel):
    name: str
    phone_number: str
    email: str
    chat_id: str
    status: int | None = None


class FormSubmissionUpdate(BaseModel):
    name: str | None = None
    phone_number: str | None = None
    email: str | None = None
    status: int | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """Validate status is None, 1, 2, or 3"""
        if v is not None and v not in [1, 2, 3]:
            raise ValueError(
                "Status must be None, 1 (TO DO), 2 (IN PROGRESS), or 3 (COMPLETED)"
            )
        return v


# Task 2


# adding an enum based FormStatus class to validate the status field
class FormStatus(IntEnum):
    TODO = 1
    IN_PROGRESS = 2
    COMPLETED = 3


class AuditChange(BaseModel):
    id: str
    created_at: datetime | None = None
    field: str
    old_value: object | None = None
    new_value: object | None = None

    model_config = ConfigDict(from_attributes=True)


# Task 3 Audit Log Revisions


class AuditRevisionWithChanges(BaseModel):
    id: str
    created_at: datetime | None = None
    entity_type: str
    entity_id: str
    event_type: str
    source: str | None = None
    actor_type: str | None = None
    actor_id: str | None = None
    reason: str | None = None
    request_id: str | None = None
    changes: list[AuditChange] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

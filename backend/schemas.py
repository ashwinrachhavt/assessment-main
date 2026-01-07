from typing import Optional
import uuid
from datetime import datetime
from enum import IntEnum
from pydantic import BaseModel, field_validator


class Chat(BaseModel):
    id: str
    created_at: datetime
    messages: list

    class Config:
        orm_mode=True

class ChatCreate(BaseModel):
    messages: list = []

class ChatUpdate(BaseModel):
    messages: list


class FormSubmission(BaseModel):
    id: str
    created_at: datetime
    # Some legacy rows may have nulls; keep response tolerant
    name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    status: Optional[int] = None

    class Config:
        orm_mode=True

class FormSubmissionCreate(BaseModel):
    name: str
    phone_number: str
    email: str
    chat_id: str
    status: Optional[int] = None

class FormSubmissionUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    status: Optional[int] = None
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate status is None, 1, 2, or 3"""
        if v is not None and v not in [1, 2, 3]:
            raise ValueError('Status must be None, 1 (TO DO), 2 (IN PROGRESS), or 3 (COMPLETED)')
        return v



# Task 2

# adding an enum based FormStatus class to validate the status field
class FormStatus(IntEnum):
    TODO = 1
    IN_PROGRESS = 2
    COMPLETED = 3


class AuditChange(BaseModel):
    id: str
    created_at: datetime
    field: str
    old_value: Optional[object] = None
    new_value: Optional[object] = None

    class Config:
        orm_mode = True

# Task 3 Audit Log Revisions

class AuditRevisionWithChanges(BaseModel):
    id: str
    created_at: datetime
    entity_type: str
    entity_id: str
    event_type: str
    source: Optional[str] = None
    actor_type: Optional[str] = None
    actor_id: Optional[str] = None
    reason: Optional[str] = None
    request_id: Optional[str] = None
    changes: list[AuditChange] = []

    class Config:
        orm_mode = True

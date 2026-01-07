import secrets

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Chat(Base):
    __tablename__ = "chat"

    id = Column(
        String(length=32), primary_key=True, index=True, default=secrets.token_urlsafe
    )
    created_at = Column(DateTime, index=True)
    messages = Column(JSON)
    form_submissions = relationship(
        "FormSubmission", cascade="all, delete", back_populates="chat"
    )


class FormSubmission(Base):
    __tablename__ = "form_submission"

    id = Column(
        String(length=32), primary_key=True, index=True, default=secrets.token_urlsafe
    )
    created_at = Column(DateTime, index=True)
    chat_id = Column(
        String(length=32), ForeignKey("chat.id"), index=True, nullable=False
    )
    chat = relationship("Chat", back_populates="form_submissions")
    name = Column(String, index=True)
    phone_number = Column(String, index=True)
    email = Column(String, index=True)
    status = Column(Integer, index=True)


class AuditRevision(Base):
    __tablename__ = "audit_revision"

    id = Column(
        String(length=32), primary_key=True, index=True, default=secrets.token_urlsafe
    )
    created_at = Column(DateTime, index=True)

    entity_type = Column(String, index=True, nullable=False)
    entity_id = Column(String, index=True, nullable=False)
    event_type = Column(String, index=True, nullable=False)  # create|update|delete

    actor_type = Column(String, nullable=True)
    actor_id = Column(String, nullable=True)
    source = Column(String, nullable=True)  # api|ui|chat_tool
    reason = Column(String, nullable=True)
    request_id = Column(String, nullable=True)

    changes = relationship(
        "AuditChange", cascade="all, delete-orphan", back_populates="revision"
    )


class AuditChange(Base):
    __tablename__ = "audit_change"

    id = Column(
        String(length=32), primary_key=True, index=True, default=secrets.token_urlsafe
    )
    created_at = Column(DateTime, index=True)

    revision_id = Column(
        String(length=32), ForeignKey("audit_revision.id"), index=True, nullable=False
    )
    revision = relationship("AuditRevision", back_populates="changes")

    field = Column(String, index=True, nullable=False)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)

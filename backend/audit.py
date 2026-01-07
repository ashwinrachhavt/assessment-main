# Task 3 Audit Log Revisionsßå

from __future__ import annotations

from typing import Any, Iterable, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models import AuditChange, AuditRevision


async def log_revision(
    db: AsyncSession,
    *,
    entity_type: str,
    entity_id: str,
    event_type: str,
    changes: Iterable[dict[str, Any]],
    source: Optional[str] = None,
    actor_type: Optional[str] = None,
    actor_id: Optional[str] = None,
    reason: Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    """
    Best-effort audit logging.
    This intentionally commits in its own transaction to keep main logic simple.
    """
    revision = AuditRevision(
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        source=source,
        actor_type=actor_type,
        actor_id=actor_id,
        reason=reason,
        request_id=request_id,
    )
    db.add(revision)
    await db.flush()  # assigns revision.id

    for ch in changes:
        db.add(
            AuditChange(
                revision_id=revision.id,
                field=ch["field"],
                old_value=ch.get("old_value"),
                new_value=ch.get("new_value"),
            )
        )

    await db.commit()


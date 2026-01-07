from __future__ import annotations

import pytest

import crud
import database
import schemas


@pytest.mark.asyncio
async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Hello World"}


@pytest.mark.asyncio
async def test_form_lifecycle(client):
    # create a chat via API
    resp = await client.post("/chat", json={"messages": []})
    assert resp.status_code == 200
    chat_id = resp.json()["id"]

    assert database.SessionLocal is not None
    async with database.SessionLocal() as db:  # type: ignore[misc]
        form = await crud.form.create(
            db=db,
            obj_in=schemas.FormSubmissionCreate(
                name="Ada Lovelace",
                email="ada@example.com",
                phone_number="555-0100",
                chat_id=chat_id,
                status=None,
            ),
        )

    # update status
    resp = await client.put(f"/forms/{form.id}", json={"status": 2})
    assert resp.status_code == 200
    assert resp.json()["status"] == 2

    # query by chat/status
    resp = await client.get(f"/chat/{chat_id}/forms", params={"status": 2})
    assert resp.status_code == 200
    forms = resp.json()
    assert len(forms) == 1
    assert forms[0]["id"] == form.id

    # delete
    resp = await client.delete(f"/forms/{form.id}")
    assert resp.status_code == 200

    # gone
    resp = await client.get(f"/chat/{chat_id}/forms")
    assert resp.status_code == 200
    assert resp.json() == []

from typing import Any, AsyncGenerator, Optional
import uuid
import json

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession
import crud
from database import SessionLocal
import schemas
from models import FormSubmission
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_TEMPLATE = """"""

# Get a DB Session
async def get_db() -> AsyncGenerator:
    async with SessionLocal() as session:
        yield session


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/chat", response_model=list[schemas.Chat])
async def get_chats(db: AsyncSession = Depends(get_db)):
    chats = await crud.chat.get_multi(db, limit=10)
    return chats


@app.post("/chat", response_model=schemas.Chat)
async def create_chat(data: schemas.ChatCreate, db: AsyncSession = Depends(get_db)):
    chat = await crud.chat.create(db=db, obj_in=data)
    return chat


@app.put("/chat/{chat_id}", response_model=schemas.Chat)
async def update_chat(
    chat_id: str, data: schemas.ChatUpdate, db: AsyncSession = Depends(get_db)
):
    """
    Update chat with new messages and handle tool calls.
    Supports: submit_interest_form, update_interest_form, delete_interest_form
    """
    chat = await crud.chat.get(db, id=chat_id)

    # TASK 2: Define all three tools
    tools = [
        {
            "type": "function",
            "function": {
                "name": "submit_interest_form",
                "description": "Submit an interest form for the user with the given properties",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "the user's name",
                        },
                        "email": {
                            "type": "string",
                            "description": "the user's email address",
                        },
                        "phone_number": {
                            "type": "string",
                            "description": "the user's phone number",
                        },
                    },
                    "required": ["name", "email", "phone_number"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "update_interest_form",
                "description": "Update an existing interest form submission. You can update the name, email, phone number, or status (1=TO DO, 2=IN PROGRESS, 3=COMPLETED).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "form_id": {
                            "type": "string",
                            "description": "the ID of the form to update",
                        },
                        "name": {
                            "type": "string",
                            "description": "the user's updated name",
                        },
                        "email": {
                            "type": "string",
                            "description": "the user's updated email address",
                        },
                        "phone_number": {
                            "type": "string",
                            "description": "the user's updated phone number",
                        },
                        "status": {
                            "type": "integer",
                            "description": "status: 1=TO DO, 2=IN PROGRESS, 3=COMPLETED",
                        },
                    },
                    "required": ["form_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "delete_interest_form",
                "description": "Delete an interest form submission",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "form_id": {
                            "type": "string",
                            "description": "the ID of the form to delete",
                        },
                    },
                    "required": ["form_id"],
                },
            },
        },
    ]

    # First OpenAI call
    resp = openai_client.chat.completions.create(
        messages=[{"role": "system", "content": SYSTEM_TEMPLATE}] + data.messages,
        model="gpt-4o-mini",
        tools=tools,
    )
    resp_message = resp.choices[0].message.model_dump()
    data.messages.append(resp_message)

    # TASK 1 & 2: Handle tool calls
    if resp_message.get('tool_calls'):
        for t in resp_message["tool_calls"]:
            tool_name = t["function"]["name"]
            
            # Parse the JSON arguments
            try:
                form_data = json.loads(t["function"]["arguments"])
            except json.JSONDecodeError:
                # If JSON parsing fails, append error and continue
                data.messages.append(
                    {
                        "tool_call_id": t["id"],
                        "role": "tool",
                        "name": tool_name,
                        "content": "Error: Invalid JSON arguments",
                    }
                )
                continue
            
            tool_response = "Success"
            
            try:
                if tool_name == "submit_interest_form":
                    # TASK 1: Create form submission
                    if not form_data.get("name") or not form_data.get("email") or not form_data.get("phone_number"):
                        raise ValueError("name, email, and phone_number are required")

                    form_submission_data = schemas.FormSubmissionCreate(
                        name=form_data.get("name"),
                        email=form_data.get("email"),
                        phone_number=form_data.get("phone_number"),
                        chat_id=chat_id,
                        status=None
                    )
                    created_form = await crud.form.create(db=db, obj_in=form_submission_data)
                    tool_response = f"Success! Form submitted with ID: {created_form.id}"
                    
                elif tool_name == "update_interest_form":
                    # TASK 2: Update form submission
                    form_id = form_data.get("form_id")
                    form_obj = await crud.form.get(db, id=form_id)
                    
                    if not form_obj:
                        tool_response = f"Error: Form with ID {form_id} not found"
                    else:
                        # Build update data with only provided, non-null fields
                        update_payload: dict[str, Any] = {}
                        for key in ("name", "email", "phone_number", "status"):
                            if key in form_data and form_data[key] is not None:
                                update_payload[key] = form_data[key]

                        update_data = schemas.FormSubmissionUpdate(**update_payload)
                        await crud.form.update(db=db, db_obj=form_obj, obj_in=update_data)
                        tool_response = f"Success! Form {form_id} updated"
                        
                elif tool_name == "delete_interest_form":
                    # TASK 2: Delete form submission
                    form_id = form_data.get("form_id")
                    form_obj = await crud.form.get(db, id=form_id)
                    
                    if not form_obj:
                        tool_response = f"Error: Form with ID {form_id} not found"
                    else:
                        await crud.form.remove(db=db, id=form_id)
                        tool_response = f"Success! Form {form_id} deleted"
                        
            except Exception as e:
                tool_response = f"Error: {str(e)}"
            
            # Append tool response message
            data.messages.append(
                {
                    "tool_call_id": t["id"],
                    "role": "tool",
                    "name": tool_name,
                    "content": tool_response,
                }
            )

        # Second OpenAI call with tool results
        resp = openai_client.chat.completions.create(
            messages=[{"role": "system", "content": SYSTEM_TEMPLATE}] + data.messages,
            model="gpt-4o-mini",
            tools=tools,
        )
        resp_message = resp.choices[0].message.model_dump()
        data.messages.append(resp_message)

    # Update chat with all messages
    chat = await crud.chat.update(db, db_obj=chat, obj_in=data)
    return chat


@app.get("/chat/{chat_id}", response_model=schemas.Chat)
async def get_chat(chat_id: str, db: AsyncSession = Depends(get_db)):
    chat = await crud.chat.get(db, id=chat_id)
    return chat


# TASK 1 & 2: Get all form submissions for a chat with optional status filter
@app.get("/chat/{chat_id}/forms", response_model=list[schemas.FormSubmission])
async def get_chat_forms(
    chat_id: str, 
    status: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all form submissions for a specific chat.
    Optional query parameter: status (1=TO DO, 2=IN PROGRESS, 3=COMPLETED)
    """
    filters = [FormSubmission.chat_id == chat_id]
    
    # TASK 2: Add status filter if provided
    if status is not None:
        if status not in [1, 2, 3]:
            raise HTTPException(status_code=400, detail="Status must be 1, 2, or 3")
        filters.append(FormSubmission.status == status)
    
    forms = await crud.form.get_multi(db, filters=filters)
    return forms


# TASK 2: REST API Endpoints for Form Management

@app.put("/forms/{form_id}", response_model=schemas.FormSubmission)
async def update_form(
    form_id: str, 
    data: schemas.FormSubmissionUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """
    Update a form submission.
    Can update: name, email, phone_number, status
    Status must be None, 1 (TO DO), 2 (IN PROGRESS), or 3 (COMPLETED)
    """
    form = await crud.form.get(db, id=form_id)
    
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    # Disallow explicitly setting these fields to null via REST API
    update_payload = data.model_dump(exclude_unset=True)
    for key in ("name", "email", "phone_number"):
        if key in update_payload and update_payload[key] is None:
            raise HTTPException(status_code=400, detail=f"{key} cannot be null")
    
    updated_form = await crud.form.update(db=db, db_obj=form, obj_in=data)
    return updated_form


@app.delete("/forms/{form_id}")
async def delete_form(form_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a form submission"""
    form = await crud.form.get(db, id=form_id)
    
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    await crud.form.remove(db=db, id=form_id)
    return {"message": "Form deleted successfully", "form_id": form_id}

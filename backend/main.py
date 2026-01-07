from typing import Any, AsyncGenerator
import uuid
import json

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession
import crud
from database import SessionLocal
import schemas
import os
from dotenv import load_dotenv
from models import FormSubmission
load_dotenv() # Loading environment variables from .env file in the root directory, always a good practice :D. 

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

# response_model represents the format of the response that this endpoint will produce. Responses are always in JSON
@app.get("/chat", response_model=list[schemas.Chat])
async def get_chats(db: AsyncSession = Depends(get_db)):
    chats = await crud.chat.get_multi(db, limit=10)
    return chats

# the data parameter represents the body of the request. The request body should always be in JSON format
@app.post("/chat", response_model=schemas.Chat)
async def create_chat(data: schemas.ChatCreate, db: AsyncSession = Depends(get_db)):
    chat = await crud.chat.create(db=db, obj_in=data)
    return chat

# the chat_id parameter maps to the chat id in the URL
@app.put("/chat/{chat_id}", response_model=schemas.Chat)
async def update_chat(
    chat_id: str, data: schemas.ChatUpdate, db: AsyncSession = Depends(get_db)
):
    chat = await crud.chat.get(db, id=chat_id)

    resp = openai_client.chat.completions.create(
        messages=[{"role": "system", "content": SYSTEM_TEMPLATE}] + data.messages,
        model="gpt-4o-mini",
        tools=[
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
                        "required": ["name", "email", "phone_number"],  # Added required fields
                    },
                },
            }
        ],
    )
    resp_message = resp.choices[0].message.model_dump()

    data.messages.append(resp_message)

    # TASK 1: Handle tool calls and save to database
    if resp_message.get('tool_calls'):
        for t in resp_message["tool_calls"]:
            # Parse the tool call arguments
            if t["function"]["name"] == "submit_interest_form":                
                form_data = json.loads(t["function"]["arguments"]) # Parse the JSON arguments from the tool call
                
                # Create FormSubmission in database using CRUD
                form_submission_data = schemas.FormSubmissionCreate(
                    name=form_data.get("name"),
                    email=form_data.get("email"),
                    phone_number=form_data.get("phone_number"),
                    chat_id=chat_id,
                    status=None  # Default status is None
                )
                
                # Save to database
                await crud.form.create(db=db, obj_in=form_submission_data)
            
            # Append tool response message
            data.messages.append(
                {
                    "tool_call_id": t["id"],
                    "role": "tool",
                    "name": t["function"]["name"],
                    "content": "Success",
                }
            )

        # Make second completion call with tool results
        resp = openai_client.chat.completions.create(
            messages=[{"role": "system", "content": SYSTEM_TEMPLATE}] + data.messages,
            model="gpt-4o-mini",
            tools=[
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
                }
            ],
        )
        resp_message = resp.choices[0].message.model_dump()
        data.messages.append(resp_message)

    # Update chat with new messages
    chat = await crud.chat.update(db, db_obj=chat, obj_in=data)

    return chat



@app.get("/chat/{chat_id}", response_model=schemas.Chat)
async def get_chat(chat_id: str, db: AsyncSession = Depends(get_db)):
    chat = await crud.chat.get(db, id=chat_id)

    return chat


# Task 1

@app.get("/chat/{chat_id}/forms", response_model=list[schemas.FormSubmission])
async def get_chat_forms(chat_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get all form submissions for a specific chat.
    """    
    # Use the CRUD get_multi with filters
    forms = await crud.form.get_multi(
        db, 
        filters=[FormSubmission.chat_id == chat_id]
    )
    
    return forms

import sys
import typing

import orjson
import uvicorn
import asyncio
import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from src.functions.image_generation import run_image_generation_service
from src.functions.story_generation import run_story_generation_service
from src.models import PromptPayload, UserPayload, NewStoryPayload, Story, StoryStatus
from src.external_libs.prompt_builder import build_prompt
from src.external_libs.text_completion import generate_text

import firebase_admin
from firebase_admin import firestore, credentials

sys.path.append("src")

HTTP_PORT = 8000


class ORJSONResponse(JSONResponse):
    media_type = "application/json"

    def render(self, content: typing.Any) -> bytes:
        return orjson.dumps(content, option=orjson.OPT_SERIALIZE_NUMPY)


app = FastAPI(default_response_class=ORJSONResponse)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=["*"]
)

db = None


@app.on_event("startup")
async def setup():
    # Initialize Firebase App
    cred = credentials.Certificate("goodnight-ai-firebase-service-account-key.json")
    firebase_admin.initialize_app(cred)
    # Get a reference to the Firestore database
    db = firestore.client()
    asyncio.create_task(run_story_generation_service(db))
    asyncio.create_task(run_image_generation_service(db))


@app.get("/")
def read_root():
    return {"Status": "Active"}


@app.post("/prompt/")
async def generate_text_endpoint(payload: PromptPayload, request: Request):
    prompt = payload.prompt
    temperature = payload.temperature
    max_tokens = payload.max_tokens
    final_prompt = build_prompt(payload.genre)
    return generate_text(final_prompt, temperature, max_tokens)


@app.post("/new_user/")
async def new_user(payload: UserPayload, request: Request):
    # Check if the user already exists in the Firestore collection
    user_ref = db.collection(u'users').document(payload.id_token)
    user = user_ref.get()
    utc_timestamp = datetime.datetime.utcnow().timestamp()
    if not user.exists:
        # If the user does not exist, store the information in the Firestore collection
        user_ref.set({
            u'name': payload.name,
            u'email': payload.email,
            u'profile_picture': payload.profile_picture,
            u'access_token': payload.access_token,
            u'device_token': payload.device_token,
            u'id_token': payload.id_token,
            u'last_story_generated_timestamp': utc_timestamp
        })
        user_id = user_ref.id
        user_ref.update({
            u'user_id': user_id
        })
        return {"message": "User information stored successfully", "user_id": user_id}, 201
    else:
        return "User already exists", 200


@app.post("/new_story/")
async def new_story(payload: NewStoryPayload, request: Request):
    story_ref = db.collection(u'users').document(payload.user_id).collection(u'stories').document()
    story_id = story_ref.id
    utc_timestamp = datetime.datetime.utcnow().timestamp()
    story = Story(
        prompt=build_prompt(payload.genre, payload.main_character_name),
        status=StoryStatus.PendingTextGeneration,
        timestamp=utc_timestamp
    )
    user_ref = db.collection(u'users').document(payload.user_id)
    user = user_ref.get().to_dict()
    if user is None:
        raise HTTPException(status_code=400, detail="User not found")
    if "stories" not in user:
        user["stories"] = []
    user["stories"].append(story.dict())
    user_ref.set(user)
    return {"message": "Story request created successfully", "story_id": story_id}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=HTTP_PORT, reload=True)

import asyncio
import datetime
import sys
import typing

import firebase_admin
import orjson
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from firebase_admin import auth, credentials, firestore
from starlette.middleware.cors import CORSMiddleware

from src.external_libs.prompt_builder import build_prompt
from src.external_libs.text_completion import generate_text
from src.functions.image_generation import run_image_generation_service
from src.functions.story_generation import run_story_generation_service
from src.models import (NewStoryPayload, PromptPayload, Story, StoryStatus,
                        UserDbObject, UserPayload,
                        UserSubscriptionObject)

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
security = HTTPBearer()


def get_auth_verified_user_id(authorization):
    # Verify JWT token
    if not authorization:
        raise HTTPException(
            status_code=400, detail="Authorization header missing")
    id_token = authorization.split("Bearer ")[1]
    try:
        decoded_token = firebase_admin.auth.verify_id_token(id_token)
        return decoded_token["uid"]
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid JWT token")


@app.on_event("startup")
async def setup():
    global db
    # Initialize Firebase App
    cred = credentials.Certificate(
        "goodnight-ai-firebase-service-account-key.json")
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


@app.post("/user/")
async def new_user(payload: UserPayload, authorization=Depends(security)):
    verified_user_id = get_auth_verified_user_id(authorization.credentials)
    # Check if the user already exists in the Firestore collection
    user_ref = db.collection(u'users').document(verified_user_id)
    user = user_ref.get()

    if not user.exists:
        # If the user does not exist, store the information in the Firestore collection
        user_object = UserDbObject(
            name=payload.name,
            email=payload.email,
            profile_picture=payload.profile_picture,
            user_id=verified_user_id,
            last_story_generated_timestamp=0,
            subscription=UserSubscriptionObject(
                start_date_timestamp=0,
                end_date_timestamp=0,
                finished_free_story=False,
            ),
            stories=[]
        )
        user_ref.set(user_object.dict())
        return {"message": "User information stored successfully", "user_id": verified_user_id}, 201
    else:
        return "User already exists", 200


@app.get("/user/")
async def get_user(authorization=Depends(security)):
    verified_user_id = get_auth_verified_user_id(authorization.credentials)
    # Check if the user already exists in the Firestore collection
    user_ref = db.collection(u'users').document(verified_user_id)
    user = user_ref.get()

    if not user.exists:
        # If the user does not exist, store the information in the Firestore collection
        raise HTTPException(
            status_code=401, detail="User does not exist")
    else:
        return user.to_dict()


@app.post("/story/")
async def new_story(payload: NewStoryPayload, authorization=Depends(security)):
    verified_user_id = get_auth_verified_user_id(authorization.credentials)
    # Check if user exists
    user_ref = db.collection(u'users').document(verified_user_id)
    user = user_ref.get().to_dict()
    utc_timestamp = datetime.datetime.utcnow().timestamp()
    if user is None:
        raise HTTPException(status_code=400, detail="User not found")

    # Check if user subscription valid
    subscription = user["subscription"]
    if subscription["end_date_timestamp"] < utc_timestamp and subscription["finished_free_story"]:
        raise HTTPException(status_code=403, detail="Free tier ran out")

    # Check if last story generated was less than a day ago
    time_since_last_story = utc_timestamp - \
                            user["last_story_generated_timestamp"]
    if time_since_last_story < 24 * 60 * 60:
        raise HTTPException(
            status_code=429, detail="Too many story requests in a day")

    # Generate prompt and store in db
    story_ref = db.collection(u'users').document(
        verified_user_id).collection(u'stories').document()
    story_id = story_ref.id
    story = Story(
        prompt=build_prompt(payload.genre, payload.main_character_name),
        status=StoryStatus.PendingTextGeneration,
        timestamp=utc_timestamp
    )
    if "stories" not in user:
        user["stories"] = []
    user["stories"].append(story.dict())

    # Update subscription if applicable
    if subscription["end_date_timestamp"] < utc_timestamp and not subscription["finished_free_story"]:
        user["subscription"]["finished_free_story"] = True
    user["last_story_generated_timestamp"] = datetime.datetime.utcnow().timestamp()
    user_ref.set(user)
    return {"message": "Story request created successfully", "story_id": story_id}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=HTTP_PORT, reload=True)

import asyncio
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

from functions.image_queue_process import run_image_queue_process_service
from functions.new_story_queue_process import run_story_request_service
from src.functions.image_generation import run_image_generation_service
from src.functions.story_generation import run_story_generation_service
from src.models import (StoryStatus,
                        UserDbObject, UserPayload,
                        UserSubscriptionObject, ReadStoryPayload)

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
    asyncio.create_task(run_story_request_service(db))
    asyncio.create_task(run_story_generation_service(db))
    asyncio.create_task(run_image_generation_service(db))
    asyncio.create_task(run_image_queue_process_service(db))


@app.get("/")
def read_root():
    return {"Status": "Active"}

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
                isActive = False
            ),
            config=payload.user_config,
            stories=[]
        )
        user_ref.set(user_object.dict())
        return {"message": "User information stored successfully", "user_id": verified_user_id}, 201
    else:
        return "User already exists", 200


@app.post("/user/config/")
async def edit_user_config(payload: UserPayload, authorization=Depends(security)):
    verified_user_id = get_auth_verified_user_id(authorization.credentials)
    # Check if the user already exists in the Firestore collection
    user_ref = db.collection(u'users').document(verified_user_id)
    user = user_ref.get()

    if not user.exists:
        return "User does not exist", 400
    else:
        # Update only the config
        user_ref.update({"config": payload.user_config})
        return {"message": "User information stored successfully", "user_id": verified_user_id}, 201

@app.post("/user/subscription")
async def update_user_subscription(payload: UserSubscriptionObject, authorization=Depends(security)):
    verified_user_id = get_auth_verified_user_id(authorization.credentials)
    # Check if the user already exists in the Firestore collection
    user_ref = db.collection(u'users').document(verified_user_id)
    user = user_ref.get()

    if not user.exists:
        return "User does not exist", 400
    else:
        # Update only the subscription
        user_ref.update({"subscription": payload})
        return {"message": "User information stored successfully", "user_id": verified_user_id}, 201

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


@app.post("/read-story/")
async def update_story_as_read(payload: ReadStoryPayload, authorization=Depends(security)):
    verified_user_id = get_auth_verified_user_id(authorization.credentials)
    # Check if user exists
    user_ref = db.collection(u'users').document(verified_user_id)
    user = user_ref.get().to_dict()
    if user is None:
        raise HTTPException(status_code=400, detail="User not found")

    # Check if story exists
    stories = user.get("stories")
    if stories:
        for index, story in enumerate(stories):
            if story["story_id"] == payload.story_id:
                stories[index]["read_status"] = "read"
                user_ref.update({
                    "stories": stories
                })
                return {"message": "Story updated successfully", "story_id": payload.story_id}
    return {"message": "Story not found", "story_id": payload.story_id}


@app.get("/story/")
async def get_latest_story(authorization=Depends(security)):
    verified_user_id = get_auth_verified_user_id(authorization.credentials)
    # Check if user exists
    user_ref = db.collection(u'users').document(verified_user_id)
    user = user_ref.get().to_dict()
    if user is None:
        raise HTTPException(status_code=400, detail="User not found")
    # Get latest story
    stories = user.get("stories")
    latest_story = None
    if stories:
        for index, story in enumerate(stories):
            if story["status"] == StoryStatus.StoryReady:
                latest_story = story
    return latest_story, 200


@app.get("/stories/")
async def get_stories(authorization=Depends(security)):
    verified_user_id = get_auth_verified_user_id(authorization.credentials)
    # Check if user exists
    user_ref = db.collection(u'users').document(verified_user_id)
    user = user_ref.get().to_dict()
    if user is None:
        raise HTTPException(status_code=400, detail="User not found")
    stories = user.get("stories")
    return stories, 200


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=HTTP_PORT, reload=True)

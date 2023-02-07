from pydantic import BaseModel
from enum import Enum


class PromptPayload(BaseModel):
    prompt: str
    genre: str = "children"
    temperature: float = 0.9
    max_tokens: int = 5


class UserPayload(BaseModel):
    name: str
    email: str
    profile_picture: str
    id_token: str
    access_token: str
    device_token: str


class UserSubscriptionObject(BaseModel):
    start_date_timestamp: int = 0
    end_date_timestamp: int = 0
    finished_free_story: bool


class UserDbObject(BaseModel):
    name: str
    email: str
    profile_picture: str
    access_token: str
    device_token: str
    id_token: str
    user_id: str
    last_story_generated_timestamp: int
    subscription: UserSubscriptionObject


class StoryStatus(str, Enum):
    PendingTextGeneration = 'PendingTextGeneration'
    PendingImageGeneration = 'PendingImageGeneration'
    PendingImageFetch = 'PendingImageFetch'
    StoryReady = 'StoryReady'


class Story(BaseModel):
    prompt: str = ''
    generated_story: str = ''
    generated_summary: str = ''
    image_url: str = ''
    timestamp: int = 0
    status: StoryStatus


class NewStoryPayload(BaseModel):
    user_id: str
    genre: str
    main_character_name: str

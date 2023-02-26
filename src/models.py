from enum import Enum

from pydantic import BaseModel
from pydantic.types import List


class PromptPayload(BaseModel):
    prompt: str
    genre: str = "children"
    temperature: float = 0.9
    max_tokens: int = 5


class UserAgeGroup(str, Enum):
    Children = 'children'
    Teens = 'teens'
    Adults = 'adults'


class UserConfig(BaseModel):
    main_character_name: str = ''
    age_group: UserAgeGroup = UserAgeGroup.Adults
    genre: str = 'adventure'


class UserPayload(BaseModel):
    name: str
    email: str
    profile_picture: str
    user_config: UserConfig


class UserSubscriptionObject(BaseModel):
    start_date_timestamp: int = 0
    end_date_timestamp: int = 0
    finished_free_story: bool


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
    fetch_image_timestamp: int = 0
    fetch_image_id: str = ''
    status: StoryStatus


class NewStoryPayload(BaseModel):
    genre: str
    main_character_name: str


class UserDbObject(BaseModel):
    name: str
    email: str
    profile_picture: str
    user_id: str
    last_story_generated_timestamp: int
    subscription: UserSubscriptionObject
    stories: List[Story]
    config: UserConfig

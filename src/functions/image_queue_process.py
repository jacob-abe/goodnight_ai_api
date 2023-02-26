import asyncio
import datetime

from src.config import STABLE_DIFFUSION_API_KEY
from src.models import StoryStatus
import requests
import time

IMAGE_QUEUE_FREQUENCY = 30  # Every 30 secs


def fetch_queued_image(id: str):
    response = requests.post(f"https://stablediffusionapi.com/api/v4/dreambooth/fetch/{id}",
                             json={"key": STABLE_DIFFUSION_API_KEY})
    if response.status_code == 200:
        response_body = response.json()
        if response_body['output'] is not None:
            return response_body['output'][0]
        else:
            raise Exception(f"Response does not have output")
    else:
        raise Exception(f"Request failed with status code: {response.status_code}")


async def run_image_queue_process_service(firestore_db):
    while True:
        users_ref = firestore_db.collection("users")
        users = users_ref.stream()

        for user in users:
            stories = user.get("stories")
            if stories:
                for index, story in enumerate(stories):
                    if story.get("status") == "PendingImageFetch" and story.get("fetch_image_timestamp") < time.time():
                        image_url = fetch_queued_image(story.get("fetch_image_id"))
                        user_ref = users_ref.document(user.id)
                        story = story.copy()
                        story["image_url"] = image_url
                        story["status"] = StoryStatus.StoryReady
                        story["timestamp"] = datetime.datetime.utcnow().timestamp()
                        stories[index] = story
                        user_ref.update({
                            "stories": stories
                        })

        await asyncio.sleep(IMAGE_QUEUE_FREQUENCY)

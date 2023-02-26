import asyncio
import time

from src.config import STABLE_DIFFUSION_API_KEY
from src.models import StoryStatus
import requests

IMAGE_GENERATION_FREQUENCY = 60  # Every minute


def generate_image(prompt):
    data = {
        "key": STABLE_DIFFUSION_API_KEY,
        "model_id": "midjourney",
        "prompt": prompt,
        "negative_prompt": "painting, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, deformed, ugly, blurry, bad anatomy, bad proportions, extra limbs, cloned face, skinny, glitchy, double torso, extra arms, extra hands, mangled fingers, missing lips, ugly face, distorted face, extra legs",
        "width": "512",
        "height": "512",
        "samples": "1",
        "num_inference_steps": "30",
        "safety_checker": "no",
        "enhance_prompt": "yes",
        "seed": None,
        "guidance_scale": 7.5,
        "webhook": None,
        "track_id": None
    }
    response = requests.post("https://stablediffusionapi.com/api/v3/dreambooth", json=data)
    if response.status_code == 200:
        response_body = response.json()
        if response_body['output'] is not None:
            return response_body['output'][0]
        else:
            if response_body["status"] is 'processing' and response_body["eta"] is not None:
                return {
                    "eta":float(response_body["eta"]) + time.time(),
                    "fetch_id":response_body["id"]
                }
            else:
                raise Exception("Unexpected result from api")
    else:
        raise Exception(f"Request failed with status code: {response.status_code}")

async def run_image_generation_service(firestore_db):
    while True:
        users_ref = firestore_db.collection("users")
        users = users_ref.stream()

        for user in users:
            stories = user.get("stories")
            if stories:
                for index, story in enumerate(stories):
                    if story.get("status") == "PendingImageGeneration":
                        image_response = generate_image(story.get("prompt"))
                        if image_response.get("eta") is not None:
                            story["fetch_image_timestamp"] = image_response.get("eta")
                            story["fetch_image_id"] = image_response.get("fetch_id")
                            story["status"] = StoryStatus.PendingImageFetch
                            stories[index] = story
                            user_ref = users_ref.document(user.id)
                            user_ref.update({
                                "stories": stories
                            })
                        # If the image is ready, update the story
                        else:
                            image_url = image_response
                            user_ref = users_ref.document(user.id)
                            story = story.copy()
                            story["image_url"] = image_url
                            story["status"] = StoryStatus.StoryReady
                            stories[index] = story
                            user_ref.update({
                                "stories": stories
                            })

        await asyncio.sleep(IMAGE_GENERATION_FREQUENCY)

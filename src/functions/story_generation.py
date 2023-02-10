import asyncio

from google.cloud.firestore_v1.types import firestore

from src.models import StoryStatus
from src.external_libs.prompt_builder import build_summary_prompt
from src.external_libs.text_completion import generate_text

STORY_GENERATION_FREQUENCY = 60  # Every minute


def generate_story(prompt):
    generated_text = generate_text(prompt, temperature=float(0.9), max_tokens=int(400))
    generated_summary = generate_text(build_summary_prompt(generated_text), temperature=float(0.9), max_tokens=25)
    return [generated_text, generated_summary]


async def run_story_generation_service(firestore_db):
    while True:
        users_ref = firestore_db.collection("users")
        users = users_ref.stream()

        for user in users:
            stories = user.get("stories")
            if stories:
                for index, story in enumerate(stories):
                    if story.get("status") == "PendingTextGeneration":
                        [generated_text, generated_summary] = generate_story(story.get("prompt"))
                        user_ref = users_ref.document(user.id)
                        story = story.copy()
                        story["generated_story"] = generated_text
                        story["generated_summary"] = generated_summary
                        story["status"] = StoryStatus.PendingImageGeneration
                        stories[index] = story
                        user_ref.update({
                            "stories": stories
                        })

        await asyncio.sleep(STORY_GENERATION_FREQUENCY)

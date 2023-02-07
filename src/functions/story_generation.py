import asyncio

from src.config import OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS
from src.models import StoryStatus
from src.external_libs.prompt_builder import build_summary_prompt
from src.external_libs.text_completion import generate_text

STORY_GENERATION_FREQUENCY = 60  # Every minute


def generate_story(prompt):
    generated_text = generate_text(prompt, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS)
    generated_summary = generate_text(build_summary_prompt(generated_text), OPENAI_TEMPERATURE, 25)
    return [generated_text, generated_summary]


async def run_story_generation_service(firestore_db):
    while True:
        users_ref = firestore_db.collection("users")
        users = users_ref.stream()

        for user in users:
            stories = user.get("stories")
            if stories:
                for story in stories:
                    if story.get("status") == "PendingTextGeneration":
                        story_ref = users_ref.document(user.id).collection("stories").document(story.id)
                        [generated_text, generated_summary] = generate_story(story.get("prompt"))
                        story_ref.update({
                            "generated_story": generated_text,
                            "generated_summary": generated_summary,
                            "status": StoryStatus.PendingImageGeneration
                        })

        await asyncio.sleep(STORY_GENERATION_FREQUENCY)

import asyncio
import datetime

from external_libs.prompt_builder import build_prompt
from models import StoryStatus, Story

STORY_GENERATION_FREQUENCY = 300  # Every 5 minutes


async def run_story_request_service(firestore_db):
    while True:
        users_ref = firestore_db.collection("users")
        users = users_ref.stream()

        for user in users:
            stories = user.get("stories")
            # Find the last story and if the story is unread and user has not requested a new story today
            if stories:
                last_story = stories[-1]
                if last_story["status"] == StoryStatus.StoryReady and last_story["read_status"] == "read":
                    user = user.to_dict()
                    # Check if the user has requested a new story today
                    if datetime.datetime.utcnow().timestamp() - user["last_story_generated_timestamp"] > 24 * 60 * 60:
                        # Check if user subscription valid
                        subscription = user["subscription"]
                        if subscription["end_date_timestamp"] < datetime.datetime.utcnow().timestamp() and subscription[
                            "finished_free_story"]:
                            raise Exception("Free tier ran out")
                        # Request a new story
                        story_id = len(stories)
                        config = user["config"]
                        story = Story(
                            prompt=build_prompt(config["genre"], config["main_character_name"]),
                            status=StoryStatus.PendingTextGeneration,
                            timestamp=datetime.datetime.utcnow().timestamp(),
                            read_status='unread',
                            story_id=story_id
                        )
                        if "stories" not in user:
                            user["stories"] = []
                        user["stories"].append(story.dict())

                        # Update subscription if applicable
                        if subscription["end_date_timestamp"] < datetime.datetime.utcnow().timestamp() and not \
                        subscription["finished_free_story"]:
                            user["subscription"]["finished_free_story"] = True
                        user["last_story_generated_timestamp"] = datetime.datetime.utcnow().timestamp()
                        user_ref = firestore_db.collection(u'users').document(user["user_id"])
                        user_ref.set(user)

        await asyncio.sleep(STORY_GENERATION_FREQUENCY)

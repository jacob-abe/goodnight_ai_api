def build_prompt(genre: str, main_character: str = None):
    final_prompt = ''
    if not main_character:
        final_prompt = "Write a " + genre + " short story" + " with a starting and ending."
    else:
        final_prompt = "Write a " + genre + " short story" + \
                       " featuring " + main_character + " with a starting and ending."
    return final_prompt


def build_summary_prompt(story):
    return "Give a short summary to generate an prompt for an illustration for this story: " + story

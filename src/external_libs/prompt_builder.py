def build_prompt(genre: str, main_character: str = None, age_type: str = 'adult'):
    final_prompt = ''
    if not main_character:
        final_prompt = "Write a " + genre + " short story" + " with a starting and ending."+\
                       f"The story should be engaging and interesting for an {age_type} audience."
    else:
        final_prompt = "Write a " + genre + " short story" + \
                       " featuring " + main_character + " with a starting and ending."+\
                       f"The story should be engaging and interesting for an {age_type} audience."
    return final_prompt


def build_summary_prompt(story):
    return "Give a short summary to generate an prompt for an illustration for the following story: " + story

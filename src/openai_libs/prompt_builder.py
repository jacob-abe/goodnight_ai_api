def build_prompt(input: str, genre: str):
    final_prompt = "Write a " + genre + " short story" + \
        " about " + input + " with a starting and ending."
    return final_prompt

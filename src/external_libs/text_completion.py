import openai

from src.config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY


def generate_text(prompt, temperature=0.9, max_tokens=5):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    return response.choices[0].text

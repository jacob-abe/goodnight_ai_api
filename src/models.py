from pydantic import BaseModel


class PromptPayload(BaseModel):
    prompt: str
    genre: str = "children"
    temperature: float = 0.9
    max_tokens: int = 5

import sys
import typing

import orjson
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from src.models import PromptPayload
from src.openai_libs.prompt_builder import build_prompt
from src.openai_libs.text_completion import generate_text

sys.path.append("src")


HTTP_PORT = 8000


class ORJSONResponse(JSONResponse):
    media_type = "application/json"

    def render(self, content: typing.Any) -> bytes:
        return orjson.dumps(content, option=orjson.OPT_SERIALIZE_NUMPY)


app = FastAPI(default_response_class=ORJSONResponse)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=["*"]
)


@app.get("/")
def read_root():
    return {"Status": "Active"}


@app.post("/prompt/")
async def generate_text_endpoint(payload: PromptPayload, request: Request):
    prompt = payload.prompt
    temperature = payload.temperature
    max_tokens = payload.max_tokens
    final_prompt = build_prompt(prompt, payload.genre)
    return generate_text(final_prompt, temperature, max_tokens)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=HTTP_PORT, reload=True)

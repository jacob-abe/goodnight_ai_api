import os

from dotenv import load_dotenv

load_dotenv()

HTTP_PORT = os.getenv('HTTP_PORT', 5001)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'RANDOM-VALS')
STABLE_DIFFUSION_API_KEY = os.getenv('STABLE_DIFFUSION_API_KEY', 'RANDOM-VALS')
SKIP_STARTUP = os.getenv('SKIP_STARTUP', 'False')

# OpenAI SETTINGS
OPENAI_TEMPERATURE = 0.9,
OPENAI_MAX_TOKENS = 400

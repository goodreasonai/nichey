from dotenv import load_dotenv
import os

load_dotenv('.env')  # Load environment variables from .env

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
BING_API_KEY = os.environ.get('BING_API_KEY')
OPEN_ROUTER_API_KEY = os.environ.get('OPEN_ROUTER_API_KEY')

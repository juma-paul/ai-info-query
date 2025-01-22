import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not google_credentials_path:
    raise EnvironmentError("GOOGLE_APPLICATIONS_CREDENTIALS environment variable not set or missing in .env file.")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_credentials_path

client = OpenAI(api_key=OPENAI_API_KEY)

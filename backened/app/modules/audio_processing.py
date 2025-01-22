import os, io
from dotenv import load_dotenv
from google.cloud import speech
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

TEMP_AUDIO_PATH = "temp_audio.wav"
speech_client = speech.SpeechClient()

def handle_audio_input(audio_data):
    try:
        with open(TEMP_AUDIO_PATH, "wb") as temp_audio_file:
            temp_audio_file.write(audio_data)

        with io.open(TEMP_AUDIO_PATH, "rb") as audio_file:
            content = audio_file.read()

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
            enable_automatic_punctuation=True,
        )
        audio = speech.RecognitionAudio(content=content)

        response = speech_client.recognize(config=config, audio=audio)

        if not response.results:
            return None

        transcription = response.results[0].alternatives[0].transcript

        if os.path.exists(TEMP_AUDIO_PATH):
            os.remove(TEMP_AUDIO_PATH)

        return transcription.strip().lower()
    except Exception as e:
        if os.path.exists(TEMP_AUDIO_PATH):
            os.remove(TEMP_AUDIO_PATH)
        print(f"Error in handle_audio_input: {e}")
        return None
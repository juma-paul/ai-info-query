import os, io
from pathlib import Path
from openai import OpenAI
from datetime import datetime
from pydub import AudioSegment
from dotenv import load_dotenv
from google.cloud import speech
from pydub.playback import play
import speech_recognition as sr
from langdetect import detect
from modules.chatbot import (
    sanitize_and_moderate, translate_text, retrieval_chain, 
    conversation_memory, chat_history_storage
)

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
REPLY_AUDIO_PATH = "reply.mp3"
speech_client = speech.SpeechClient()

WAKE_WORD = "assistant"
STOP_WORD = "stop"
is_active = False

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


def generate_and_play_speech(text, verbose=True):
    try:
        print(f"Generating speech for text: {text}")
        speech_file_path = Path(REPLY_AUDIO_PATH)

        tts_response = client.audio.speech.create(
            model="tts-1",
            voice="shimmer",
            input=text
        )
        tts_response.stream_to_file(speech_file_path)
        audio_url = f"/static/{speech_file_path.name}"

        reply_audio = AudioSegment.from_file(speech_file_path)
        play(reply_audio)

        if verbose:
            print(f"[{datetime.now()}] Playback completed.")

        if os.path.exists(speech_file_path):
            os.remove(speech_file_path)
            if verbose:
                print(f"[{datetime.now()}] Temporary audio file '{REPLY_AUDIO_PATH}' removed.")

        return audio_url
    except Exception as e:
        if os.path.exists(REPLY_AUDIO_PATH):
            os.remove(REPLY_AUDIO_PATH)
        print(f"Error in generate_and_play_speech: {e}")
        raise e
    

def listen_for_audio():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.pause_threshold = 0.8
    recognizer.dynamic_energy_threshold = False

    with sr.Microphone(sample_rate=16000) as source:
        print("Listening for audio...")
        audio = recognizer.listen(source)
    return audio


def process_query(query, input_lang='auto-detect', output_lang='English'):
    try:
        detected_lang = detect(query) if input_lang == "auto-detect" else input_lang

        is_valid, error_message = sanitize_and_moderate(query, "input")
        if not is_valid:
            return {"status": "error", "message": error_message}

        if detected_lang != "English":
            query = translate_text(query, target_lang="English")

        response = retrieval_chain.invoke({
            "input": query,
            "chat_history": conversation_memory.load_memory_variables({}).get("chat_history", [])
        })
        answer = response["answer"]

        is_valid, error_message = sanitize_and_moderate(answer, "output")
        if not is_valid:
            return {"status": "error", "message": "Response contains inappropriate content."}

        if output_lang != "English":
            answer = translate_text(answer, target_lang=output_lang)

        chat_history_storage.append({"role": "user", "content": query})
        chat_history_storage.append({"role": "assistant", "content": answer})
        conversation_memory.save_context({"input": query}, {"output": answer})

        return {"status": "success", "userMessage": query, "assistantResponse": answer}
    except Exception as e:
        return {"status": "error", "message": str(e)}
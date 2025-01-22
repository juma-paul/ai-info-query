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
from flask import Blueprint, request, jsonify
from modules.chatbot import (
    sanitize_and_moderate, translate_text, retrieval_chain, 
    conversation_memory, chat_history_storage
)

audio_bp = Blueprint('speech', __name__)

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
    

@audio_bp.route('/speech_chat', methods=['POST'])
def speech_chat():
    global is_active
    try:
        input_lang = request.json.get('inputLanguage', 'auto-detect')
        output_lang = request.json.get('outputLanguage', 'English')

        while True:
            # Waiting Mode: Listen for wake word
            while not is_active:
                audio = listen_for_audio()
                transcription = handle_audio_input(audio.get_wav_data())
                if transcription and WAKE_WORD in transcription.lower():
                    is_active = True
                    generate_and_play_speech("Hello! How can I help you today?")
                    break

            # Conversation Mode
            while is_active:
                audio = listen_for_audio()
                transcription = handle_audio_input(audio.get_wav_data())

                if not transcription:
                    generate_and_play_speech("I didn't catch that. Could you please repeat?")
                    continue

                if STOP_WORD in transcription.lower():
                    is_active = False
                    generate_and_play_speech("Goodbye! I'll be here if you need me.")
                    break

                # Process query
                response = process_query(transcription, input_lang, output_lang)

                if response["status"] == "error":
                    error_message = response.get("message", "An error occurred")
                    generate_and_play_speech(f"I'm sorry, but {error_message} Let's try again.")
                    continue

                audio_url = generate_and_play_speech(response["assistantResponse"])

                return jsonify({
                    "status": "success",
                    "userMessage": response["userMessage"],
                    "assistantResponse": response["assistantResponse"],
                    "audioUrl": audio_url
                })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
from flask import Flask
from flask_cors import CORS 
from modules.document_processing import document_bp
from modules.chatbot import chatbot_bp
from modules.audio_processing import audio_bp

def create_app():
    app = Flask(__name__)

    CORS(app)
    
    # Register Blueprints
    app.register_blueprint(document_bp, url_prefix='/document')
    app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
    app.register_blueprint(audio_bp, url_prefix='/speech')

    return app
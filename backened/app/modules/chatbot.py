import re
from openai import OpenAI
from langdetect import detect
from config import OPENAI_API_KEY
from langchain_openai import ChatOpenAI
from .document_processing import vector_db
from flask import Blueprint, request, jsonify
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_history_aware_retriever, create_retrieval_chain


chatbot_bp = Blueprint('chatbot', __name__)

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize conversation memory
try:
    conversation_memory = ConversationBufferWindowMemory(
        memory_key='chat_history',
        k=5,
        return_messages=True
    )
except Exception as e:
    raise ValueError(f"Failed to initialize conversation memory: {str(e)}")

# Initialize the retriever
try:
    retriever = vector_db.as_retriever()
except Exception as e:
    raise ValueError(f"Failed to initialize retriever: {str(e)}")
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



import os, re
from flask import Blueprint
from config import OPENAI_API_KEY
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter


document_bp = Blueprint('document', __name__)

# Initialize embedding function
embedding_function = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

# Initialize vector store
persist_directory = 'docs/chroma_db/'
os.makedirs(persist_directory, exist_ok=True)
vector_db = Chroma(persist_directory=persist_directory, embedding_function=embedding_function)

# Initialize text splitter for consistent chunking
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)


# Utility function for cleaning web content
def clean_text(text):
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove common web elements and navigation text
    text = re.sub(r'\b(?:Menu|Navigation|Search|Copyright|©)\b|\[\w+\]', '', text, flags=re.IGNORECASE)
    
    return text
import os, re, tempfile, uuid
from flask import Blueprint, request
from config import OPENAI_API_KEY
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader


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


@document_bp.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    if 'pdf' not in request.files:
        return {'error': 'No PDF file provided!'}, 400
    
    pdf_file = request.files['pdf']
    if not pdf_file.filename.endswith('.pdf'):
        return {'error': 'Invalid file format. Please upload a PDF.'}, 400
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_path = temp_file.name  
        pdf_file.save(temp_path)

    try:
        pdf_loader = PyPDFLoader(temp_path)
        pdf_docs = pdf_loader.load()
        chunks = text_splitter.split_documents(pdf_docs)

        if not chunks:
            return {'error': 'No content was extracted from the PDF.'}, 400

        # Prepare documents and metadata
        documents = [chunk.page_content for chunk in chunks]
        metadata = [{"id": str(uuid.uuid4()), **chunk.metadata} for chunk in chunks]

        vector_db.add_texts(documents, metadatas=metadata)
        
        return {'message': 'PDF processed and added successfully.'}, 200
    except Exception as e:
        return {'error': f'Error processing PDF: {str(e)}'}, 500
    finally:
        os.remove(temp_path)
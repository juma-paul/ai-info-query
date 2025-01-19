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

languages = {
    "en": "English", "es": "Spanish", "fr": "French", "ru": "Russian", "zh": "Chinese", "ar": "Arabic", "sw": "Swahili"
}

# Initialize conversation memory
try:
    conversation_memory = ConversationBufferWindowMemory(
        memory_key='chat_history',
        k=5,
        return_messages=True
    )
except Exception as e:
    raise ValueError(f"Failed to initialize conversation memory: {str(e)}")

chat_history_storage = []

# Initialize the retriever
try:
    retriever = vector_db.as_retriever()
except Exception as e:
    raise ValueError(f"Failed to initialize retriever: {str(e)}")


# Define the standalone question contextualization prompt
contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, just "
    "reformulate it if needed and otherwise return it as is."
)

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# Create a history-aware retriever
llm = ChatOpenAI(
    model_name='gpt-3.5-turbo',
    temperature=0.1,
    api_key=OPENAI_API_KEY
)

history_aware_retriever = create_history_aware_retriever(
    llm=llm,
    retriever=retriever,
    prompt=contextualize_q_prompt,
)

# Define the question-answering system prompt
qa_system_prompt = (
    "You are an assistant for question-answering tasks. Use "
    "the following pieces of retrieved context to answer the "
    "question. If you don't know the answer, just say that you "
    "don't know. Use three sentences maximum and keep the answer "
    "concise."
    "\n\n"
    "{context}"
)
qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        ("human", "{input}"),
    ]
)

# Define the document combination chain for QA
question_answer_chain = create_stuff_documents_chain(llm=llm, prompt=qa_prompt)

# Create the retrieval chain
retrieval_chain = create_retrieval_chain(
    history_aware_retriever,
    question_answer_chain,
)

# Utility Functions
def moderate_content(content, content_type="input"):
    try:
        response = client.moderations.create(input=content, model="omni-moderation-2024-09-26")
        if 'results' in response and len(response.results) > 0:
            flagged = response.results[0].get('flagged', False)
            categories = response.results[0].get('categories', {})
            if flagged:
                flagged_categories = ', '.join(category for category, flagged in categories.items() if flagged)
                if content_type == "input":
                    message = f"I cannot assist with that request as it violates ethical guidelines related to: {flagged_categories}. Please feel free to ask a constructive or appropriate question."
                else:
                    message = f"The response generated might not be appropriate to share as it violates guidelines related to: {flagged_categories}. If you have another question, feel free to ask."
                return False, message
    except Exception:
        return False, "An error occurred while processing your request. Please try again later."
    return True, None

def detect_prompt_injection(content):
    injection_keywords = [
        "ignore all rules", "ignore previous instructions", "bypass", "pretend", "as if",
        "you are now", "disregard", "change the system", "disregard all", "do not follow", "reset"
    ]
    for keyword in injection_keywords:
        if keyword.lower() in content.lower():
            return False, "Your request includes potentially harmful manipulations and cannot be processed."
    return True, None


# Input sanitization remains the same
def sanitize_input(input_text):
    # Sanitize template injections by replacing curly braces
    input_text = input_text.replace('{', '{{').replace('}', '}}')
    
    # Sanitize SQL injection risks (very basic example)
    input_text = re.sub(r"(?i)(DROP|SELECT|INSERT|UPDATE|DELETE|--|\bUNION\b|\bFROM\b)", "", input_text)
    
    return input_text


def sanitize_and_moderate(content, content_type="input"):
    # Step 0: Sanitize input
    content = sanitize_input(content)

    # Step 1: Check for prompt injection
    is_valid, error_message = detect_prompt_injection(content)
    if not is_valid:
        return False, error_message

    # Step 2: Perform content moderation
    return moderate_content(content, content_type)


def translate_text(text, target_lang='English'):
    """Translates text to the specified target language."""
    if target_lang != 'English':
        try:
            translation = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"Translate the following text into {target_lang}."},
                    {"role": "user", "content": text}
                ],
                max_tokens=1000
            )
            return translation.choices[0].message.content.strip()
        except Exception:
            return "An error occurred while translating the text. Please try again later."
    return text


@chatbot_bp.route('/get-history', methods=['GET'])
def get_history():
    try:
        return jsonify({'history': chat_history_storage}), 200
    except Exception:
        return jsonify({'error': 'Failed to retrieve chat history'}), 500
    

@chatbot_bp.route('/clear-history', methods=['POST'])
def clear_history():
    try:
        chat_history_storage.clear()
        return jsonify({'message': 'Chat history cleared successfully'}), 200
    except Exception:
        return jsonify({'error': 'Failed to clear chat history'}), 500
    

@chatbot_bp.route('/start-new-conversation', methods=['POST'])
def start_new_conversation():
    try:
        conversation_memory.clear()
        return jsonify({'message': 'New conversation started successfully'}), 200
    except Exception:
        return jsonify({'error': 'Failed to start new conversation'}), 500
    

@chatbot_bp.route('/available-languages', methods=['GET'])
def get_available_languages():
    """Retrieves the list of available languages for translation."""
    try:
        languages_list = [{"code": code, "name": name} for code, name in languages.items()]
        return jsonify({"languages": languages_list}), 200
    except Exception:
        return jsonify({'error': 'Failed to retrieve available languages'}), 500  
    

@chatbot_bp.route('/ask', methods=['POST'])
def ask_question():
    """Processes user questions, applies sanitization, moderation, and returns a response."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        question = data.get('question', '')
        input_lang = data.get('inputLanguage', 'auto-detect')
        output_lang = data.get('outputLanguage', 'English')

        if not question:
            return jsonify({'error': 'No question provided'}), 400

        # Sanitize and moderate the question
        is_valid, error_message = sanitize_and_moderate(question, "input")
        if not is_valid:
            return jsonify({'error': error_message, 'flagged': True}), 400

        # Language detection and translation
        original_language = 'English'
        if input_lang == 'auto-detect':
            detected_lang = detect(question)
            if detected_lang != 'en' and detected_lang in languages:
                original_language = languages[detected_lang]
                question = translate_text(question, 'English')
        elif input_lang != 'English':
            original_language = input_lang
            question = translate_text(question, 'English')

        # Running the QA Chain
        response = retrieval_chain.invoke({
            "input": question,
            "chat_history": conversation_memory.load_memory_variables({}).get("chat_history", [])
        })

        answer = response['answer']

        # Moderate the generated answer
        is_valid, error_message = sanitize_and_moderate(answer, "output")
        if not is_valid:
            return jsonify({'error': error_message, 'flagged': True}), 400

        # Translate the answer if needed
        if output_lang != 'English':
            answer = translate_text(answer, output_lang)

        # Update chat history and memory
        chat_history_storage.append({"role": "user", "content": question})
        chat_history_storage.append({"role": "assistant", "content": answer})
        conversation_memory.save_context(
            {"input": question},
            {"output": answer}
        )

        return jsonify({
            'answer': answer,
            'original_language': original_language
        }), 200

    except Exception as e:
        return jsonify({'error': 'An error occurred while handling the question', 'details': str(e)}), 500
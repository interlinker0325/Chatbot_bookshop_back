from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv
import json
from pinecone import Pinecone
from flask_cors import CORS
from flask import Flask, request, jsonify
from datetime import datetime

load_dotenv()
app = Flask(__name__)
CORS(app)

# Initialize clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
pc_index = pc.Index(host = os.getenv("PINECONE_INDEX_NAME"))  

chat_histories = {}

class Message(BaseModel):
    role: str
    content: str
    timestamp: datetime = datetime.now()

class ChatHistory(BaseModel):
    messages: List[Message] = []
    last_recommended_books: List[Dict] = []  # Store the last set of recommended books
    last_query: Optional[str] = None

class Query(BaseModel):
    book_related: bool

def analyze_query(query:str, chat_history: List[Message]) -> bool:
    messages = [
        {
            "role": "system",
            "content": (
                "Please analyze the user's message and determine if it is related to books or bookshops. Return 'true' if it is related, and 'false' if it is not."
            ),  
        }
    ]
    for msg in chat_history[-3:]:
        messages.append({"role": msg.role, "content": msg.content})
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    answer = response.choices[0].message.content.strip().lower()
    return answer == "true"

def is_book_followup(query: str, last_books: List[Dict]) -> Optional[Dict]:
    if not last_books:
        return None
    messages = [
        {
            "role": "system",
            "content": """Analyze if the user's question is about one of the previously recommended books.
            If yes, return the book's details in JSON format. If no, return 'null'.
            
            Example response for a match:
            {
                "title": "Book Title",
                "author": ["Author Name"],
                "price": 19.99,
                "summary": "Book summary",
                "url": "https://example.com/book"
            }
            
            Example response for no match:
            null"""
        },
        {
            "role": "user",
            "content": f"Previous books: {last_books}\n\nUser question: {query}"
        }
    ]
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    
    try:
        content = response.choices[0].message.content.strip()
        if content.lower() == 'null':
            return None
        return json.loads(content)
    except:
        return None

def is_criteria_followup(query: str, last_query: str) -> bool:
    messages = [
        {
            "role": "system",
            "content": """Analyze if the user's message is a follow-up request with specific criteria (like language, publisher, etc.).
            Return 'true' if it is a follow-up with criteria, 'false' if it is not.
            
            Examples of follow-up criteria:
            - "anything in Italian?"
            - "from Mondadori publishing house?"
            - "books in Spanish?"
            - "anything from Penguin?"
            
            Examples of non-follow-up:
            - "tell me more about this book"
            - "what's the price?"
            """
        },
        {
            "role": "user",
            "content": f"Previous query: {last_query}\n\nCurrent query: {query}"
        }
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    answer = response.choices[0].message.content.strip().lower()
    return answer == "true"

def get_book_details(book: Dict, query: str) -> str:
    """Get detailed information about a specific book based on the user's query."""
    messages = [
        {
            "role": "system",
            "content": f"""You are a knowledgeable bookseller. Provide detailed information about this book:
            Title: {book['title']}
            Author: {', '.join(book['author'])}
            Summary: {book['summary']}
            
            The user asked: {query}
            
            Provide a detailed, informative response that directly addresses the user's question about this specific book.
            Include relevant details about the book's themes, writing style, reception, and why it might interest the reader.
            Keep the response concise but informative."""
        }
    ]
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    
    return response.choices[0].message.content.strip()

def get_embedding(query: str) -> list:
    response = client.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def generate_response(query: str, results: dict) -> str:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Generate a helpful response based on the search results."},
            {"role": "user", "content": f"Query: {query}\nResults: {results}"}
        ]
    )
    return response.choices[0].message.content

@app.route('/chatbot', methods=['POST'])
def chatbot():
    try:
        data = request.get_json()
        query = data.get('query')
        session_id = data.get('session_id', 'default')

        if not query:
            return jsonify({"error": "No query provided"}), 400

        if session_id not in chat_histories:
            chat_histories[session_id] = ChatHistory()

        chat_history = chat_histories[session_id]

        # Add user message to history
        chat_history.messages.append(Message(role="user", content=query))

        # Check for book follow-up questions
        if chat_history.last_recommended_books:
            matched_book = is_book_followup(query, chat_history.last_recommended_books)
            if matched_book:
                detailed_response = get_book_details(matched_book, query)
                chat_history.messages.append(Message(role="assistant", content=detailed_response))
                return jsonify({
                    "response": detailed_response,
                    "books": None,
                    "session_id": session_id
                })

        # Check for criteria follow-up
        if chat_history.last_query and is_criteria_followup(query, chat_history.last_query):
            # Get embedding and query Pinecone with criteria
            embedding = get_embedding(f"{chat_history.last_query} {query}")
            search_results = pc_index.query(
                namespace="new_book_shop",
                vector=embedding,
                top_k=3,
                include_metadata=True
            )
            
            books = []
            for book in search_results["matches"]:
                books.append({
                    "title": book["metadata"]["title"],
                    "author": book["metadata"]["author"],
                    "summary": book["metadata"]["summary"],
                    "price": book["metadata"]["price"],
                    "url": book["metadata"]["url"]
                })
            
            response_text = "Here are some books matching your criteria:"
            chat_history.messages.append(Message(role="assistant", content=response_text))
            chat_history.last_recommended_books = books
            
            return jsonify({
                "response": response_text,
                "books": books,
                "session_id": session_id
            })

        # Analyze if query is book-related
        is_book_related = analyze_query(query, chat_history.messages)
        print("Is book related:", is_book_related)

        if not is_book_related:
            response_text = "I'm a book recommendation assistant. I can help you find books, but I can't assist with other topics."
            chat_history.messages.append(Message(role="assistant", content=response_text))
            return jsonify({
                "response": response_text,
                "books": None,
                "session_id": session_id
            })

        # Get embedding and query Pinecone
        embedding = get_embedding(query)
        search_results = pc_index.query(
            namespace="new_book_shop",
            vector=embedding,
            top_k=3,
            include_metadata=True
        )
        
        books = []
        for book in search_results["matches"]:
            books.append({
                "title": book["metadata"]["title"],
                "author": book["metadata"]["author"],
                "summary": book["metadata"]["summary"],
                "price": book["metadata"]["price"],
                "url": book["metadata"]["url"]
            })
        
        if books:
            response_text = "Here are some books you might like:"
            chat_history.last_recommended_books = books
            chat_history.last_query = query
        else:
            response_text = "I couldn't find any matching books. Could you try rephrasing your request?"
        
        chat_history.messages.append(Message(role="assistant", content=response_text))
        
        return jsonify({
            "response": response_text,
            "books": books,
            "session_id": session_id
        })

    except Exception as e:
        print(f"Error in chatbot endpoint: {str(e)}")
        return jsonify({
            "error": "An error occurred while processing your request",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
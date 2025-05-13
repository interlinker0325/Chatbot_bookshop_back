import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from typing import List
from flask import Flask, request, jsonify
from flask_cors import CORS


# Load environment variables from .env file
load_dotenv()
app = Flask(__name__)
CORS(app)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Book(BaseModel):
    title: str
    author: str
    publisher: str
    why_fit_for_me: str
    purchase_link: List[str]

class Output(BaseModel):
    books: List[Book]

def analyze_query(query: str) -> bool:
    """Check if the query is related to books or bookshops."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Please analyze the user's message and determine if it is related to books "
                    "or bookshops. Return 'true' if it is related, and 'false' if it is not."
                ),
            },
            {"role": "user", "content": query},
        ],
    )
    answer = response.choices[0].message.content.strip().lower()
    return answer == "true"

def generate_response(query: str) -> Output:
    """Generate a helpful response including purchase link."""
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system", 
                "content": "Your role is to recommend 3 books based on the user's query. For each book, provide the title, author, publisher, why it fits the user's needs, and purchase links (like Amazon and LaFeltrinelli)."
            },
            {"role": "user", "content": query},
        ],
        response_format=Output,
    )
    return response.choices[0].message.parsed

@app.route('/chatbot', methods=['POST'])
def chatbot():
    try:
        # user_query = input("Enter your query: ")
        data = request.get_json()
        query = data.get('query')
        print(query)

        if not query:
            return jsonify({"error": "No query provided"}), 400

        is_book_related = analyze_query(query)
        print(f"Is book related? {is_book_related}")

        if not is_book_related:
            # return jsonify({ "response": "I'm just a bookseller, I can help you find the next book to read but nothing else."})
            return jsonify({
                "response": "I'm just a bookseller, I can help you find the next book to read but nothing else",
                "books": None
            })
        else:
            response_text = "Here are some books you might like:\n\n"
            answer = generate_response(query)
            for i, book in enumerate(answer.books, 1):
                response_text += f"\nBook {i}:"
                response_text +=f"📖 {book.title}"
                response_text +=f"👤 {book.author}"
                response_text +=f"Publisher: {book.publisher}"
                response_text +=f"Why it fits for you: {book.why_fit_for_me}"
                response_text +=("Purchase Links:")
                for link in book.purchase_link:
                    response_text +=f"- {link}"
                return jsonify({
                    "response": response_text,
                    "books" : book
                })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

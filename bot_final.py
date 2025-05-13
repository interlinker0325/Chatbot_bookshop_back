from enum import Enum
from typing import Optional
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv
import json
from pinecone import Pinecone
from flask_cors import CORS
from flask import Flask, request, jsonify

load_dotenv()
app = Flask(__name__)
CORS(app)

# Initialize clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
pc_index = pc.Index(host = os.getenv("PINECONE_INDEX_NAME"))  

class Query(BaseModel):
    book_related: bool

def analyze_query(query) -> bool:
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Please analyze the user's message and determine if it is related to books or bookshops. Return 'true' if it is related, and 'false' if it is not"},
            {"role": "user", "content": query}
        ],
        response_format=Query,
    )
    return response.choices[0].message.parsed.book_related

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
        
        if not query:
            return jsonify({"error": "No query provided"}), 400

        # Step 1: Analyze query
        is_book_related = analyze_query(query)
        print("step1", is_book_related)

        if not is_book_related:
            final_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Give a concise response."},
                    {"role": "user", "content": query}
                ]
            )
            return jsonify({
                "response": final_response.choices[0].message.content,
                "books": None
            })

        # Step 2: Get embedding and query Pinecone
        embedding = get_embedding(query)
        search_results = pc_index.query(
            namespace="new_book_shop",
            vector=embedding,
            top_k=3,
            # filter=filters,
            include_metadata=True
        )
        print("search_results", search_results, type(search_results))
        
        # # Step 3: Generate final response
        # final_response = generate_response(query, search_results)
        # print("final_response", final_response)

        serched_books = search_results["matches"]
        print("serched_books", serched_books)
        books = []
        for book in serched_books:
            books.append({
                "title": book["metadata"]["title"],
                "author": book["metadata"]["author"],
                "summary": book["metadata"]["summary"],
                "price": book["metadata"]["price"],
                "url": book["metadata"]["url"]
            })
        
        if books:
            response_text = "Here are some books you might like:\n\n"
            for book in books:
                response_text += f"📖 {book['title']}\n"
                response_text += f"👤 By: {', '.join(book['author'])}\n"
                response_text += f"💰 Price: €{book['price']}\n"
                response_text += f"🔗 <a href='{book['url']}' target='_blank'>View Book</a>\n\n"
        else:
            response_text = "I couldn't find any matching books."
        
        return jsonify({
            "response": response_text,
            "books": books  # Still include the structured data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
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

class ResearchPaperExtraction(BaseModel):
    title: str
    author: str
    pages_upper_limit: int
    pages_lower_limit: int
    price_upper_limit: float
    price_lower_limit: float
    publication_date: list[int]
    publisher: str
    publish_year: list[int]
    review: int
    summary: str
    url: str

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

def extract_book_params(query: str) -> ResearchPaperExtraction:
    completion = client.beta.chat.completions.parse(
        model = "gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Your role is to extract the title, author, pages, price, url, publication date, publisher, publish year, review, and summary of the book that user want to find. If the information is not available, leave it blank."},
            {"role": "user", "content": query}
        ],
        response_format=ResearchPaperExtraction,
    )
    return completion.choices[0].message.parsed

def create_filters(params: ResearchPaperExtraction) -> dict:
    filters = {}
    
    if params.title:
        filters["title"] = {"$eq": params.title}
    if params.author:
        filters["author"] = {"$eq": params.author}
    
    # Handle pages filter
    if params.pages_lower_limit > 0 or params.pages_upper_limit > 0:
        pages_filter = {}
        if params.pages_lower_limit > 0:
            pages_filter["$gte"] = params.pages_lower_limit
        if params.pages_upper_limit > 0:
            pages_filter["$lte"] = params.pages_upper_limit
        filters["pages"] = pages_filter
    
    # Handle price filter
    if params.price_lower_limit > 0 or params.price_upper_limit > 0:
        price_filter = {}
        if params.price_lower_limit > 0:
            price_filter["$gte"] = params.price_lower_limit
        if params.price_upper_limit > 0:
            price_filter["$lte"] = params.price_upper_limit
        filters["price"] = price_filter
    
    if params.publication_date:
        filters["publication_date"] = {"$in": params.publication_date}
    if params.publisher:
        filters["publisher"] = {"$eq": params.publisher}
    if params.publish_year:
        filters["publish_year"] = {"$in": params.publish_year}
    if params.review > 0:
        filters["review"] = {"$eq": params.review}
    if params.summary:
        filters["summary"] = {"$eq": params.summary}
    if params.url:
        filters["url"] = {"$eq": params.url}
    
    return filters

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
            return jsonify({"response": final_response.choices[0].message.content})

        # Step 2: Extract book parameters
        book_params = extract_book_params(query)
        book_params_dict = {
            "title": book_params.title,
            "author": book_params.author,
            "summary": book_params.summary,
            "pages_upper_limit" : book_params.pages_upper_limit,
            "pages_lower_limit" : book_params.pages_lower_limit,
            "price_upper_limit":book_params.price_upper_limit,
            "price_lower_limit" : book_params.price_lower_limit,
            "publication_date" : book_params.publication_date,
            "publisher":book_params.publisher,
            "publish_year" : book_params.publish_year,
            "review" : book_params.review,
            "url" : book_params.url
        }
        paper_json_str = json.dumps(book_params_dict, indent=2)
        
        # Step 3: Create filters
        filters = create_filters(book_params)
        
        # # Step 4: Get embedding and query Pinecone
        embedding = get_embedding(query)
        search_results = pc_index.query(
            namespace="new_book_shop",
            vector=embedding,
            top_k=3,
            filter=filters,
            include_metadata=True
        )
        
        # # Step 5: Generate final response
        final_response = generate_response(query, search_results)
        
        return jsonify({
            "response": final_response,
            "results": search_results.to_dict()  # Convert Pinecone response to dict
        })
        # return search_results

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
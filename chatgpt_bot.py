import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from typing import List


# Load environment variables from .env file
load_dotenv()

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

if __name__ == "__main__":
    user_query = input("Enter your query: ")

    if not user_query:
        print("No query provided.")
        exit(1)

    is_book_related = analyze_query(user_query)
    print(f"Is book related? {is_book_related}")

    if not is_book_related:
        print("I'm just a bookseller, I can help you find the next book to read but nothing else.")
    else:
        answer = generate_response(user_query)
        print("\nBook Recommendations:")
        for i, book in enumerate(answer.books, 1):
            print(f"\nBook {i}:")
            print(f"Title: {book.title}")
            print(f"Author: {book.author}")
            print(f"Publisher: {book.publisher}")
            print(f"Why it fits for you: {book.why_fit_for_me}")
            print("Purchase Links:")
            for link in book.purchase_link:
                print(f"- {link}")
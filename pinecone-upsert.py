import json
from openai import OpenAI
import numpy as np
from pinecone import Pinecone
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

pc_index = pc.Index(host=os.getenv("PINECONE_INDEX_NAME"))

with open('new_cleaned_data.json', encoding='utf-8') as file:
    result_links = json.load(file)

def get_embeddings(query):
    response = client.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    )
    embedding = response.data[0].embedding
    
    return embedding
def upsert_to_pinecone(record):
    unique_id = str(uuid.uuid4())
    pc_index.upsert(
        vectors=[
            {
                "id": unique_id,
                "values": record['value'],
                "metadata": record["metadata"]
            }
        ],
        namespace="new_book_shop"
    )

if __name__ == "__main__":
    print("Starting upsert process...", len(result_links))
    for index, book in enumerate(result_links):
        print(index)
        try:
            url = book.get("url", " ")
            title = book.get("title", " ")

            review = book.get("review", " ")
            review_str = review.split(":")[1].split("\n")[0].strip() if ":" in review else "0"
            review_num = int(review_str) if review_str.isdigit() else 0

            price = book.get("price", " ")
            price_str = price.split(" ")[0].strip().replace(",", ".") if price else "0.0"
            price_num = float(price_str)
            formatted_price = f"{price_num:.2f}"
            price_data = float(formatted_price)

            summary = book["summary"]
            author = book.get("Autore:", " ")
            author_list = [name.strip() for name in author.split(",")] if author else []

            publisher = book.get("Editore:", " ")
            publish_year = book.get("Anno edizione:", " ")
            pulish_num = int(publish_year) if publish_year else None

            publication_date = book.get("In commercio dal:", "")
            month_mapping = {
                "gennaio": "01",
                "febbraio": "02",
                "marzo": "03",
                "aprile": "04",
                "maggio": "05",
                "giugno": "06",
                "luglio": "07",
                "agosto": "08",
                "settembre": "09",
                "ottobre": "10",
                "novembre": "11",
                "dicembre": "12"
            }
            try:
                day, month, year = publication_date.split()
                month_number = month_mapping[month]
                formatted_date = f"{year}-{month_number}-{day.zfill(2)}"
                updated_date = int(formatted_date.replace("-", ""))
            except: 
                formatted_date = " "

            pages = book.get("Pagine:", " ")
            number_str = pages.split()[0] if pages else "0"
            pages_num = int(number_str) if number_str.isdigit() else 0

            EAN = book.get("EAN:", " ")

            metadata =  {
                "url": url,
                "title": title,
                "author": author_list,
                "review": review_num,
                "price": price_data,
                "publisher": publisher,
                "publish_year": pulish_num,
                "publication_date": updated_date,
                "pages": pages_num,
                "EAN": EAN,
                "summary": summary
            }
            

            embedding = get_embeddings(summary)

            record = {}
            record["value"] = embedding
            record["metadata"] = metadata

            upsert_to_pinecone(record)
        except Exception as e: 
            print(f'Summary is not exist: {len(result_links)}')
            continue


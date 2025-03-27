import json
from openai import OpenAI
import numpy as np
from pinecone import Pinecone
import os
from dotenv import load_dotenv
import uuid

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

pc_index = pc.Index(host=os.getenv("PINECONE_INDEX_NAME"))

with open('total_result.json', encoding='utf-8') as file:
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
    )

if __name__ == "__main__":
    print("Starting upsert process...", len(result_links))
    for index, book in enumerate(result_links):
        print(index)
        try:
            title = book[0]["title"]
            review = book[0]["review"]
            price = book[0]["price"]
            summary = book[0]["summary"]
            author = book[1]["Autore:"]
            publisher = book[2]["Editore:"] 
            year = book[3]["Anno edizione:"]
            publication_date = book[-3]["In commercio dal:"]
            pages = book[-2]["Pagine:"]
            EAN = book[-1]["EAN:"]

            metadata =  {
                "title": title,
                "author": author,
                "review": review,
                "price": price,
                "publisher": publisher,
                "year": year,
                "publication_date": publication_date,
                "pages": pages,
                "EAN": EAN,
                "summary": summary
            }
            

            embedding = get_embeddings(summary)

            record = {}
            record["value"] = embedding
            record["metadata"] = metadata

            upsert_to_pinecone(record)
        except:
            pass


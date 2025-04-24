import json
from openai import OpenAI
import numpy as np
from pinecone import Pinecone
import os
from dotenv import load_dotenv
import uuid
import re
from datetime import datetime

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
pc_index = pc.Index(host=os.getenv("PINECONE_INDEX_NAME"))

query = "plz give me the booklist"

def query_embedding(query):
    response = client.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    )
    embedding = response.data[0].embedding
    return embedding
embedded_query = query_embedding(query)
print("embedding_query is finished")

# try:
id_search = pc_index.query(
    namespace="book_shop", 
    vector = embedded_query,
    top_k=6000,
    include_metadata=True,
)
print("id_result is finished", id_search['matches'])
id_result = id_search['matches']

# id_list = []
# for item in id_result:
#     id_list.append(item['id'])
# print(id_list, "id_result")


# metadata_list = []
# for items in id_result:
#     metadata_list.append(items['metadata']['price']) 
# print(metadata_list, "metadata_list")

for index, item in enumerate(id_result):
    print(f"Index: {index}, Total Items: {len(id_result)}")
    current_publish_year = item['metadata']['publish_year']
    current_id = item['id']

    pc_index.update(
        id = current_id,
        set_metadata = {
            "sales_year": current_publish_year,
        },
        namespace="updated_book_shop"
    ) 
# except:
#     pass 

# id_search = pc_index.query(
#     namespace="book_shop", 
#     vector = embedded_query,
#     top_k=2,
#     include_metadata=True,
# )
# print("id_result is finished", id_search['matches'])

    

    





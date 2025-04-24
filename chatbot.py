from enum import Enum
from typing import Optional
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv
import json
from pinecone import Pinecone

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
pc_index = pc.Index(host=os.getenv("PINECONE_INDEX_NAME"))

# query = "give me the book list of the books that the author is 'Avirama Golan' and publication year is between 2006 to 2013. The price should be higher than 30EUR. And pages should be 40~100"
query = "give me the book list with the fighting content and the number of pages are about 250" 
# query = "what is the react?"

class Query(BaseModel):
    book_related : bool
def analyze_query(query):
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Please analyze the user's message and determine if it is related to books or bookshops. Return 'true' if it is related, and 'false' if it is not"},
            {"role": "user", "content": query}
        ],
        response_format=Query,
    )
    return response.choices[0].message.parsed.book_related
query_result = analyze_query(query)
print(query_result, "query_result")

if query_result:
    class ReserchPaperExtraction(BaseModel):
        title : str
        author : str
        pages_upper_limit : int
        pages_lower_limit: int
        price_upper_limit : float
        price_lower_limit : float
        publication_date : list[int]
        publisher : str
        publish_year : list[int]
        review: int
        summary:str
        url: str
    completion = client.beta.chat.completions.parse(
        model = "gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Your role is to extract the title, author, pages, price, url, publication date, publisher, publish year, review, and summary of the book that user want to find. If the information is not available, leave it blank."},
            {"role": "user", "content": query}
        ],
        response_format=ReserchPaperExtraction,
    )
    research_format = completion.choices[0].message.parsed
    print(research_format, type(research_format))
    # output = {}
    # if research_format.title:
    #     output["title"] = research_format.title

    # if research_format.author:
    #     output["author"] = research_format.author

    # if research_format.pages > 0:
    #     output["pages"] = research_format.pages

    # if research_format.price > 0:
    #     output["price"] = research_format.price

    # if research_format.sales_year:
    #     output["publish_year"] = research_format.publication_date

    # if research_format.publisher:
    #     output["publisher"] = research_format.publisher

    # if research_format.publication_date:
    #     year_range = research_format.publication_date.split('-')
    #     if len(year_range) == 2:
    #         output["publication_date"] = {
    #             "$gt": year_range[0].strip(),
    #             "$lt": year_range[1].strip()
    #         }
    #     else : 
    #         output["publication_date"] = {
    #             "$eq": year_range[0].strip()
    #         }
    # if research_format.review > 0:
    #     output["review"] = research_format.review
    # print("output", output, type(output))

    

    filter_data = {}
    if research_format.title:
        filter_data["title"] = {"$eq": research_format.title}
    if research_format.author:
        filter_data["author"] = {"$eq": research_format.author}
    if research_format.pages_upper_limit > 0:
        filter_data["pages"] = {"$lte": research_format.pages_upper_limit}
    if research_format.pages_lower_limit > 0:
        filter_data["pages"] = {"$gte": research_format.pages_lower_limit}
    if research_format.pages_lower_limit == research_format.pages_upper_limit != 0:
        filter_data["pages"] = {"$eq": research_format.pages_lower_limit}
    if research_format.pages_lower_limit == research_format.pages_upper_limit == 0:
        pass
    if research_format.price_upper_limit > 0:
        filter_data["price"] = {"$lte": research_format.price_upper_limit}
    if research_format.price_lower_limit > 0:
        filter_data["price"] = {"$gte": research_format.price_lower_limit}
    if research_format.price_lower_limit == research_format.price_upper_limit != 0:
        filter_data["price"] = {"$eq": research_format.price_lower_limit}
    if research_format.price_lower_limit == research_format.price_upper_limit == 0:
        pass
    if research_format.publication_date:
        filter_data["publication_date"] = {"$in": research_format.publication_date}
    if(research_format.publisher):
        filter_data["publisher"] = {"$eq": research_format.publisher}
    if research_format.publish_year:
        filter_data["publish_year"] = {"$in": research_format.publish_year}
    if(research_format.review > 0):
        filter_data["review"] = {"$eq": research_format.review}
    if(research_format.summary):
        filter_data["summary"] = {"$eq": research_format.summary}
    if research_format.url:
        filter_data["url"] = {"$eq": research_format.url}
    print("filter_data", filter_data)


    def query_embedding(query):
        response = client.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        )
        embedding = response.data[0].embedding
        return embedding
    embedded_query = query_embedding(query)
    print("embedding_query is finished")

    serch_result = pc_index.query(
        namespace="new_book_shop",
        vector=embedded_query, 
        top_k=3,
        filter=filter_data,
        include_metadata=True,
        include_values=False
    )
    print("search_result====>", serch_result )

    def total_result(serch_result, query):
        total = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "developer", "content": "Plz create your own response based on the user's query and search result."},
                {"role": "user", "content": f"Query:{query}, Search_Result:{serch_result}"}
            ],
        )
        return total.choices[0].message.content

    total = total_result(query, serch_result)
    print("total_result is finished", total)
else :
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "plz create your own response."},
            # but I don't want long response and also I want systematical response.
            {"role": "user", "content": query}
        ],
    )
    print(completion.choices[0].message.content)









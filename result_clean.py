import json

fixed_schema_keys = ["title", "review", "price", "summary", "Autore:", "Editore:", "Anno edizione:", "In commercio dal:", "Pagine:", "EAN:"]

with open('total_result.json', encoding='utf-8') as file:
    result_links = json.load(file)

    cleaned_data = []
    for book in result_links:
        cleaned_book = {}
        for item in book:
            for key in item.keys():
                if key in fixed_schema_keys:
                    cleaned_book[key] = item[key]
        cleaned_data.append(cleaned_book)
    cleaned_json = json.dumps(cleaned_data, ensure_ascii=False, indent=4)
    
    with open('cleaned_data.json', 'w', encoding='utf-8') as file:
        file.write(cleaned_json)
    
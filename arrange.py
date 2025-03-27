import json

all_result = []
for num in range(1,4):
    with open(f'result{num}.json', encoding='utf-8') as file:
        result_links = json.load(file)

    for book in result_links:
        for item in book:
            if "Autore:" in item:
                item["Autore:"] = item["Autore:"].replace('\n', '').replace('&', '').strip()

with open('total_result.json', 'w', encoding='utf-8') as file:
    json.dump(result_links, file, indent=4, ensure_ascii=False)
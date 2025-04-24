import json
from urllib.parse import unquote
from collections import Counter

# return the index including the target url
target_url = (
    "https://www.lafeltrinelli.it//pronti-per-prova-invalsi-inglese-libro-vari"
    "/e/9788846840066?inventoryId=142866523&queryId=ca5ef336d615583f85b24db87c04a630"
).lower().strip()

try:
    with open('test1.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    found = False
    for index, item in enumerate(data):
        item_url = unquote(item.get("url", "").lower().strip())
        if item_url == target_url:
            print(f"Found at index: {index}")
            found = True
            break
    
    if not found:
        print("URL not found in any item")

except FileNotFoundError:
    print("Error: File 'test1.json' not found")
except json.JSONDecodeError:
    print("Error: Invalid JSON format in file")
except Exception as e:
    print(f"Unexpected error: {type(e).__name__} - {str(e)}")


# return the length
with open('sol.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
print(len(data))

# return the length
with open('test1.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
print(len(data))

# returnt the length including the affilate link
with open('finally_result3.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
count = 0
for index, item in enumerate(data):
    affiliate_link = item.get("affiliate_link")
    if affiliate_link:
        count += 1
print(count)

# merge into one file
files_name = ['sol.json', 'test1.json', 'finally_result3.json']
merged_data = []
for file_name in files_name:
    with open(file_name, 'r', encoding='utf-8') as file:
        data = json.load(file)
        merged_data.extend(data)
with open('merged_data.json', 'w', encoding='utf-8') as file:
    json.dump(merged_data, file, ensure_ascii=False, indent=4)

# returnt the length including the affilate link
with open('merged_data.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
print(len(data))
count = 0
for index, item in enumerate(data):
    affiliate_link = item.get("affiliate_link")
    if affiliate_link:
        count += 1
print(count)


# remove the data not involve the affilate_link
with open('merged_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
filtered_data = [item for item in data if "affiliate_link" in item]

with open('filtered.json', 'w', encoding='utf-8') as f:
    json.dump(filtered_data, f, ensure_ascii=False, indent=2)



# check the duplicate
with open('filtered.json', 'r', encoding='utf-8') as file:
    merged_data = json.load(file)
affiliate_links = [item["affiliate_link"] for item in merged_data]
affiliate_link_counts = Counter(affiliate_links)
duplicates = [link for link, count in affiliate_link_counts.items() if count > 1]
if duplicates:
    print("Duplicate affiliate links:")
    for duplicate in duplicates:
        print(duplicate)
else:
    print("No duplicate affiliate links found.")
print(len(duplicate))
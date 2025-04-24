import requests
from bs4 import BeautifulSoup
import json

with open('res.json') as res_file:
    res_links = json.load(res_file)

new_link = "https://www.lafeltrinelli.it/"

book_num = 1

res = []
for res_link in res_links:
    book_link = new_link + res_link
    print(book_link)
    result = []
    result.append({
        "url": book_link,
    })

    try:
        page = requests.get(book_link)

        if page.status_code == 200:
            soup = BeautifulSoup(page.content, "html.parser")

            title = soup.find("h1", class_="cc-title").get_text()
            review = soup.find("div", class_="cc-content-reviews").find("span").get_text()
            price = soup.find("div", class_="cc-buy-box-info").find("div",class_="cc-content-price").find("span", class_="cc-price").get_text()
            print(price)
            summary = soup.find("div", class_="cc-em-content-body").find("div").get_text()
            cleaned_summary = summary.strip()
            # cleaned_summary = " ".join(cleaned_summary.split())

            result.append({
                "title": title,
                "review": review,
                "price": price,
                "summary": cleaned_summary,
            })
            
            contents = soup.find("div", class_="cc-em-row")
            
            new_contents = contents.find_all("div", class_="cc-em-col")

            index_data_pairs = []

            for second_contents in new_contents:
                second_content = second_contents.find_all("div", class_="cc-item")
                for datas in second_content:
                    index = datas.find("div", class_="cc-content-label").find("span").get_text()
                    data = datas.find("div", class_="cc-content-value").find("span").get_text()
                    print(index, data)
                    index_data_pairs.append({index: data})

            result.extend(index_data_pairs)
            print("result",result)

            with open(f"result{book_num}.json", encoding='utf-8') as file:
                total_data = json.load(file)

            if len(total_data) > 10000 and book_num != 4:
                book_num += 1

                with open(f"result{book_num}.json", "r") as file:
                    total_data = json.load(file)
                    
            total_data.append(result)

            with open(f"result{book_num}.json", "w", encoding='utf-8') as file:
                json.dump(total_data, file, indent=4, ensure_ascii=False)

        else:
            print("Failed to retrieve the webpage.")
    except:
        pass


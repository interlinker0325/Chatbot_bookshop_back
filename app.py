from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time, json

cService = webdriver.ChromeService()

driver = webdriver.Chrome(service=cService)

# driver.get('https://www.lafeltrinelli.it/indici/libri-autori')

# div_element = driver.find_element(By.CLASS_NAME, 'cc-index__head__list')
# link_elements = div_element.find_elements(By.TAG_NAME, 'a')
# for link in link_elements:
#     href_value = link.get_attribute('href')
#     print(href_value)
#     driver.get(href_value)

with open("author_links.json", "r") as file:
    data = json.load(file)

book_links = []
for link in data:
    driver.get(link)

    time.sleep(2)
    div_element = driver.find_element(By.CLASS_NAME, 'cc-listing-items')
    body_elements = div_element.find_elements(By.TAG_NAME, 'div')
    for body in body_elements:
        link_elements = body.find_elements(By.TAG_NAME, 'a')
        for link in link_elements:
            href_value = link.get_attribute('href')
            print(href_value)
            book_links.append(href_value)


print(book_links)

with open("book_links.json", "w") as file:
    json.dump(book_links, file)

time.sleep(10)

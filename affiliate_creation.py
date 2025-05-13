import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

cService = webdriver.ChromeService()
driver = webdriver.Chrome(service=cService)

driver.get('https://ui.awin.com/link-builder/us/awin/publisher/1709207')
time.sleep(3)   

input_email = driver.find_element(By.ID, "email")
input_email.send_keys("giorgia141198@gmail.com")
button_email = driver.find_element(By.ID, "login")
button_email.click()
time.sleep(8)

input_pass = driver.find_element(By.ID, "password")
input_pass.send_keys("dygwug-geGsyv-4tefxa")
button_pass = driver.find_element(By.NAME, "action")
button_pass.click()
time.sleep(8)

# li_element = driver.find_element(By.CLASS_NAME, "menu-link menu-icon-toolbox")
# a_element = li_element.find_element(By.TAG_NAME, "a").get_attribute("href")
# driver.get(a_element)
# time.sleep(8)

driver.get("https://ui.awin.com/link-builder/us/awin/publisher/1709207")
time.sleep(10)

selete_niche = driver.find_element(By.ID, "advertiserInput")
selete_niche.send_keys(" ") 
time.sleep(2)
niche_list = driver.find_element(By.ID, "cdk-overlay-0").find_element(By.ID,"mat-autocomplete-0")
first_item = niche_list.find_element(By.XPATH, ".//*")
first_item.click()
time.sleep(2)
with open("new_cleaned_data.json", "r", encoding='utf-8') as file:
    book_urls = json.load(file)

for index, book_url in enumerate(book_urls[5569:], start=5569):
    print("index===========>", index)
    print("total========>", len(book_urls))
    link = book_url["url"]
    print("link", link)
    url_input = driver.find_element(By.NAME, "destinationUrl")
    url_input.clear()
    url_input.send_keys(link)
    print("1")
    generate_button =  driver.find_element(By.XPATH, "//button[@data-action='create-link']")
    generate_button.click()
    print("2")
    time.sleep(2)
    # getlink_button = driver.find_element(By.XPATH, "//button[@data-action='shorten-link']")
    # getlink_button.click()
    # print("3")
    # time.sleep(3)
    textarea = driver.find_element(By.NAME, "url").get_attribute("value")
    print("textarea",textarea)
    # if len(textarea) >= 50:
    #     print("Shortened link is valid, breaking the loop.")
    #     break
    time.sleep(1)
    book_url["affiliate_link"] = textarea
    print("book_url",book_url)
    with open("finally_result2.json", "w", encoding='utf-8') as file:
        json.dump(book_urls, file, ensure_ascii=False, indent=4)
    # time.sleep(2)
driver.quit()
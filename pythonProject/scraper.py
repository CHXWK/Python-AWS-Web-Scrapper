from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os
import time
import pandas as pd
import smtplib


load_dotenv()


def get_driver(url):
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--start-fullscreen')
    chrome_options.add_argument('--single-process')
    serv = Service(os.getcwd() + '/chromedriver')
    driver = webdriver.Chrome()
    driver.get(url)
    return driver


def get_table_header(driver):
    """Return Table columns in list form"""
    header = driver.find_elements(By.TAG_NAME, 'th')
    header_list = [item.text for index, item in enumerate(header) if index < 10]
    return header_list


def get_table_rows(driver):
    """Get number of rows available on the page"""
    tablerows = len(driver.find_elements(By.XPATH, '//*[@id="scr-res-table"]/div[1]/table/tbody/tr'))
    return tablerows


def parse_table_rows(rownum, driver, header_list):
    """get the data for on row at a time and return column value in the form of dictonary"""
    row_dictionary = {}
    #time.sleep(1/3)
    for index, item in enumerate(header_list):
        time.sleep(1/20)
        column_xpath = '//*[@id="scr-res-table"]/div[1]/table/tbody/tr[{}]/td[{}]'.format(rownum, index+1)
        row_dictionary[item] = driver.find_element(By.XPATH, column_xpath).text
    return row_dictionary


def parse_multiple_pages(driver, total_crypto):
    """Loop through each row, perform Next button click at the end of page return total_crypto numbers of rows"""

    table_data = []
    page_num = 1
    is_scraping = True
    header_list = get_table_header(driver)

    while is_scraping:
        table_rows = get_table_rows(driver)
        print('Found {} rows on Page : {}'.format(table_rows, page_num))
        print('Parsing Page : {}'.format(page_num))
        table_data += [parse_table_rows(i, driver, header_list) for i in range(1, table_rows + 1)]
        total_count = len(table_data)
        print('Total rows scraped : {}'.format(total_count))
        if total_count >= total_crypto:
            print('Done Parsing..')
            is_scraping = False
        else:
            print('Clicking Next Button')
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="scr-res-table"]/div[2]/button[3]')))
            element.click()
            page_num += 1
    return table_data


def scrape_yahoo_crypto(url, total_crypto, path):
    """Get the list of yahoo finance crypto-currencies and write them to CSV file """
    print('Creating driver')
    driver = get_driver(url)
    table_data = parse_multiple_pages(driver, total_crypto)
    driver.close()
    driver.quit()
    print('Save the data to a CSV')
    table_df = pd.DataFrame(table_data)
    table_df.to_csv(path)
    # Doing this to analyze the final output
    print('Completed')
    return table_df


def send_to_email():
    """will send the CSV to an email"""
    SENDER_EMAIL = os.environ.get("EMAIL_ADDR")
    RECEIVER_EMAIL = os.environ.get("EMAIL_ADDR")
    SENDER_PASSWORD = os.environ.get("PASSWORD")

    msg = MIMEMultipart()
    msg['Subject'] = 'Daily Crypto Update'
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    body = MIMEText('100 top crypto attached...', 'plain')
    msg.attach(body)

    with open('crypto-currencies.csv', 'rb') as f:
        msg.attach(MIMEApplication(f.read(), f.name))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)


if __name__ == "__main__":
     YAHOO_FINANCE_URL = 'https://finance.yahoo.com/cryptocurrencies'
     TOTAL_CRYPTO = 100
     crypto_df = scrape_yahoo_crypto(YAHOO_FINANCE_URL, TOTAL_CRYPTO, 'crypto-currencies.csv')
     send_to_email()




from bs4 import BeautifulSoup
from selenium import webdriver
import os
import pandas as pd


url = "https://finance.yahoo.com/quote/TSLA/insider-transactions?p=TSLA"

# set a chrome driver that will take all information from page
driver = webdriver.Chrome(os.getcwd() + "\chromedriver.exe")
driver.get(url)

df = pd.DataFrame(columns=['Insider', 'Type', 'Value', 'Date', 'Shares', 'Price'])

# form a "soup" file, from where can be extracted all the data
soup = BeautifulSoup(driver.page_source, "html.parser")

table = soup.findAll("table", attrs={'class': 'W(100%) BdB Bdc($seperatorColor)'})
for record in table[0].findAll("tr", attrs={"class": "BdT Bdc($seperatorColor) Bgc($hoverBgColor):h Whs(nw) H(45px)"}):
    insider = record.findAll("a", attrs={"class": "Tt(u)"})[0].text
    cells = record.findAll("td", attrs={"class": "Ta(end) Pstart(10px)"})
    if cells[2].text == "":
        value = 0
    else:
        value = int(cells[2].text.replace(",", ""))
    new_row = {
        'Insider': insider, 
        'Type': cells[1].text,
        'Value': value,
        'Date': cells[3].text,
        'Shares': int(cells[4].text.replace(",", "")),
        'Price': float(
            value /
            float(cells[4].text.replace(",", ""))
        )
    }
    df = df.append(new_row, ignore_index=True)


df.to_csv("interesting_transactions.csv")
import requests
from bs4 import BeautifulSoup
import random
import pandas as pd


class Room:
    def __init__(self, room_name=None, describe=None, format=None, amenities=None, key_fact=None):
        self.room_name = room_name
        self.describe = [buf.replace('\r\n', '') for buf in describe]
        self.format = [buf.replace('\n', '') for buf in format]
        self.amenities = amenities
        self.key_fact = key_fact
        self.img_path = ''

    def __call__(self) -> dict:
        return {
            'room name': self.room_name,
            'image url': self.img_path,
            'describe1': self.describe[0],
            'describe2': self.describe[1],
            'amenities': ','.join(self.amenities),
            'key fact': ','.join(self.key_fact),
            'format': ','.join(self.format)
        }


def toURLArg(name_: str) -> str:
    """
        將房間名稱轉換成網址路徑
    :param name_: 房間名稱
    :return: 網址路徑
    """
    final = '-'.join(list(filter(lambda word: word != '', name_.lower().split(' '))))
    return final


FEATURES = 'html.parser'
url = 'https://www.sixsenses.com/en/resorts/southern-dunes-the-red-sea/accomodation-results?newSearch=1&src=&Hotel=RSISD&Arrive=12/02/2023&Depart=12/03/2023&Rooms=1&Adult=2&Child=0'
page_url = 'https://www.sixsenses.com/en/resorts/southern-dunes-the-red-sea/accommodation'
home_url = 'https://www.sixsenses.com'
rep = requests.get(url)
praser = BeautifulSoup(rep.text, features=FEATURES)
items = praser.findAll('div', {'class': 'item'})  # 所有的房間資訊都顯示在class='item'的div
room_list = []

for item in items:
    room_name = item.get('data-room-name')  # 透過 data-room-name屬性可以取得房間名稱
    room_path = toURLArg(room_name)  # 房間頁面的路徑可透過 變數page_url/將房間名稱小寫用減號替代空格 取得

    single_rep = requests.get(f'{page_url}/{room_path}')  # 訪問個房間頁面
    single_html = BeautifulSoup(single_rep.text, features='html.parser')

    boxes = single_html.find('div', {'id': 'boxes'})  # 頁面中的重要資料都包含在class='boxes'的div裡

    img_path = boxes.find('picture').find('source').get('srcset')  # 房間示意圖的url

    description_detail = boxes.find('div', {'class': 'description-detail'})

    quote = description_detail.find('h3', {'class': 'quote'}).getText()  # 房間的大標題
    p = description_detail.find('p').getText()  # 房間的副標題
    describe = [quote, p]

    # 負責取得最大人數、房間大小、房間設計圖
    all_li = description_detail.findAll('div', recursive=False)[1].findAll('li')
    format = []
    for idx, li in enumerate(all_li):
        if idx == len(all_li) - 1:
            href = li.a.get('href')
            format.append(f'{home_url}/{href}')

        format.append(li.text.replace(':Generic.Info\n', ''))

    accordion = description_detail.find('div', {'class': 'accordion-div'}).findAll(['h4', 'li'])
    amenities, key_facts = [], []
    amenities_done = False

    for tag in accordion:
        tag_txt = tag.text
        if tag_txt == 'Key Facts':
            amenities_done = True
            continue
        if tag.name == 'h4':
            continue

        if amenities_done:
            key_facts.append(tag_txt)
            continue
        amenities.append(tag_txt)
    room = Room(room_name, amenities=amenities, key_fact=key_facts, format=format, describe=describe)
    room.img_path = f'{home_url}/{img_path}'
    room_list.append(room())


df = pd.DataFrame(room_list)
df.to_csv('./results.csv', index=False)


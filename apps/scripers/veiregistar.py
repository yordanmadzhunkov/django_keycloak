from bs4 import BeautifulSoup
import requests
import re
from datetime import date
from decimal import Decimal
from time import sleep


def parse_date(date_str):
    match = re.search(r'(\d+) (\w+) (\d+)', date_str)
    months = ['Януари', 'Февруари', 'Март', 'Април', 'Май', 'Юни',
              'Юли', 'Август', 'Септември', 'Октомври', 'Ноември', 'Декември']
    if match:
        day = int(match.group(1))
        year = int(match.group(3))
        for month in range(12):
            if match.group(2).upper() == months[month].upper():
                return date(year, month + 1, day)
    raise ValueError('not parsed date_str = ' + date_str)


def parse_decimal(decimal_str):
    match = re.search(r'(\d+\.\d+)', decimal_str)
    if match:
        return Decimal(match.group(1))
    match = re.search(r'(\d+)', decimal_str)
    if match:
        return Decimal(match.group(1))
    raise ValueError("not parsed decimal = " + decimal_str)


def parse_eik(eik_str):
    match = re.search(r'ЕИК (\d+)', eik_str)
    if match:
        return str(match.group(1))
    raise ValueError("not parsed eik = " + eik_str)


def parse_card(soup_factory):
    factory_info = soup_factory.find(class_='col-xl-8')
    # print(soup_factory.find(class_ = 'col-xl-8').prettify())

    strong = factory_info.find_all('strong')
    # print(strong)
    name = factory_info.find('h3').text
    energy_type = strong[0].text
    location = strong[0].text
    opened = strong[1].text
    capacity = strong[2].text
    owner = strong[3].find_all('small')[0].text
    eik = strong[3].find_all('small')[1].text

    try:
        eik = parse_eik(eik)
    except ValueError:
        eik = owner

    factory = {'name': name,
               'energy': name.split(' ')[0],
               'location': location,
               'opened': parse_date(opened),
               'capacity': parse_decimal(capacity),
               'owner': owner,
               'eik': eik,
               }
    return factory


class VEIEegistarScriper:
    base_url = 'https://www.veiregistar.bg'

    # URL generation
    def full_url(self, href):
        return href if href.startswith(self.base_url) else self.base_url + href

    def factories_list_url(self, page_number):
        return self.full_url('/objects&page=%d' % page_number)

    # Fetching
    def fetch_soup(self, href):
        website = requests.get(self.full_url(href))
        soup = BeautifulSoup(website.content, 'html.parser')
        return soup

    # Parsing functions

    def parse_factories_list_page(self, soup):
        cards = soup.find_all(class_='card')
        factories = []
        for card in cards:
            href = card.attrs['href']
            factories.append(href)
        return factories

    # Scriping functions
    def scripe_factories_list(self, page_number):
        soup = self.fetch_soup(self.factories_list_url(page_number))
        factories = self.parse_factories_list_page(soup)
        return factories

    def scripe_factory(self, href):
        soup = self.fetch_soup(self.full_url(href))
        return parse_card(soup)

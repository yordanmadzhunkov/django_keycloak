from bs4 import BeautifulSoup
import requests
import re
from datetime import timedelta, date, datetime
from decimal import Decimal


def same_name_ignore_whitespace(a, b):
    return a.replace(' ', '') == b.replace(' ', '')


def parse_nothing(data):
    return {}


def parse_native_name(soup):
    return {'name': soup.text}


def parse_latin_name(soup):
    return {'latin_name': soup.text}


def is_person(name, href):
    if name.find('"') >= 0:
        return False
    if re.search(r'/person/(\d+)$', href):
        return False
    if re.search(r'/person/[a-zA-Z0-9+/]+$', href):
        return True
    return False


def strip_person_href(href):
    m = re.search(r'(/person/[a-zA-Z0-9]+)/', href)
    if m:
        return m.group(1)
    return href


def parse_people(soup, role):
    people = []
    for a_tag in soup.find_all('a'):
        name = a_tag.text
        href = strip_person_href(a_tag.attrs['href'])
        people.append({
            'name': name,
            'href': href,
            'role': role,
            'person': is_person(name, href)
        })
    return {'people': people}


def parse_traders(soup):
    return parse_people(soup, 'trader')


def parse_share(line):
    # <b>  2,500.00 лв - 50.00% дял </b>
    # print(line)
    m = re.search(r'([\d\.]+) (лв) - ([\d\.]+)\% дял', line.replace(',', ''))
    if m:
        return {'share': {
            'capital': Decimal(m.group(1)),
            'currency': m.group(2),
            'percent': Decimal(m.group(3)),
        }}
    return None


def parse_ceo_and_owners(soup):
    # print(soup)
    people = []
    r = str(soup).replace('\n', '').split('<br/>')
    for line in r:
        # print('')
        # print(line)
        ex = re.search(r'(ЗАЛИЧЕН)', line)
        m = re.search(r'(Управител|Съдружник): (<a.*)', line)
        if m:
            a_tag = BeautifulSoup(m.group(2), 'html.parser').find('a')
            if m.group(1) == 'Управител':
                role = 'ceo'
            else:
                role = 'ex-owner' if ex else 'owner'
            name = a_tag.text.strip()
            href = strip_person_href(a_tag.attrs['href'])
            person = {
                'name': name,
                'href': href,
                'role': role,
                'person': is_person(name, href),
            }
            if role == 'owner' or role == 'ex-owner':
                person.update(parse_share(line))
            people.append(person)
    return {'people': people}


def parse_directors(soup):
    return parse_people(soup, 'Director in board')


def parse_capital_owner(soup):
    return parse_people(soup, 'Capital owner')


def parse_active(soup):
    return {'active': soup.text.strip() == 'Активен'}


def parse_revenue(soup):
    # print(soup.text)
    amountRE = r'([\d,]+)'
    currencyRE = r'(лв)'
    yearRE = r'(\d+)'
    moneyRE = amountRE + ' ' + currencyRE
    m = re.search(moneyRE + '\. оборот\s*\(' + moneyRE +
                  '\. печалба\)\s*за ' + yearRE, soup.text, re.MULTILINE)
    if m:
        year = m.group(5)
        currency = m.group(2)
        revenue = m.group(1).replace(',', '')
        profit = m.group(3).replace(',', '')
        return {
            year: {
                'profit': profit,
                'revenue': revenue,
                'currency': currency,
            }
        }
    return {}


def parse_registration_date(soup):
    # print(soup.text)
    try:
        # March 26, 2008 14:54
        d = datetime.strptime(soup.text.strip(), '%B %d, %Y %H:%M')
    except ValueError:
        # 1991 година
        m = re.search(r'(\d+) година', soup.text)
        if m:
            d = datetime(year=int(m.group(1)), month=1, day=1)
    return {'founded': d.date()}


def parse_legal_form(soup):
    m = re.search(r'\((.*)\)', soup.text)
    if m:
        return {'legal_form': m.group(1)}
    else:
        return {}


def extract_raw_name(name):
    match = re.search(r'"(.*)"', name)
    if match:
        return match.group(1)
    return None


def parse_company_page(soup, raw_name):
    results = soup.find_all('tr')
    for res in results:
        a = res.find('a')
        if a is not None:
            href = a.attrs['href']
            name = ""
            legal_form = ""
            latin_name = ""
            i = 0
            for k in a.text.split('\n'):
                if len(k.strip()) > 3:
                        # print(k)
                    if i == 0:
                        name = k.strip()
                        i = 1
                    elif i == 1:
                        legal_form = k.strip()
                        i = 2
                    else:
                        latin_name = k.strip()

            if legal_form.isascii():
                latin_name = legal_form
                legal_form = ''
            eik = None
            match = re.search(r'/eik/(\d+)/', href)
            if match:
                eik = match.group(1)
            if raw_name is None or same_name_ignore_whitespace(raw_name, name):
                return {
                    'href': href,
                    'name': name,
                    'legal_form': legal_form,
                    'latin_name': latin_name,
                    'eik': eik
                }
    return None


class PapagalScriper:
    base_url = 'https://papagal.bg'

    parsing_functions = {
        "Статус": parse_active,
        "ЕИК/ПИК": parse_nothing,
        "Регистрация по ЗДДС": parse_nothing,
        "Дата на регистрация": parse_registration_date,
        "Наименование": parse_native_name,
        "Транслитерация": parse_latin_name,
        "Оборот": parse_revenue,
        "Служители": parse_nothing,
        "Правна форма": parse_legal_form,
        "Седалище адрес": parse_nothing,
        "Контакти": parse_nothing,
        "Предмет на дейност": parse_nothing,
        "Управители/Съдружници": parse_ceo_and_owners,
        "Съвет на директорите": parse_directors,
        "Физически лица търговци": parse_traders,
        "Едноличен собственик на капитала": parse_capital_owner,
        "Капитал размер": parse_nothing,
        "Код на икономическа дейност": parse_nothing,
    }

    def fetch_soup(self, href):
        website = requests.get(self.base_url + href)
        soup = BeautifulSoup(website.content, 'html.parser')
        return soup

    def fetch_eik(self, name):
        soup = self.fetch_soup('/search_results/%s?type=company' % name)
        raw_name = extract_raw_name(name)
        return parse_company_page(soup, raw_name)

    def scripe(self, eik):
        info = self.fetch_eik(eik)
        if info is not None:
            soup = self.fetch_soup(info['href'])
            return self.parse_soup(soup, info)
        return None

    def parse_soup(self, soup, info):
        # print(soup.prettify())
        # print(soup.find('dl').prettify())
        dd = soup.find('dl').find_all('dd')
        dt = soup.find('dl').find_all('dt')
        if len(dd) == len(dt):
            for i in range(len(dd)):
                # print("...................................")
                # print(dt[i].text.strip())
                label = dt[i].text.strip()
                try:
                    f = self.parsing_functions[label]
                    new_info = f(dd[i])
                    if 'people' in new_info.keys() and 'people' in info:
                        info['people'] = info['people'] + \
                            new_info['people']
                    else:
                        info.update(new_info)
                except Exception as inst:
                    print(type(inst))       # the exception instance
                    print(inst.args)        # arguments stored in .args
                    # __str__ allows args to be printed directly,
                    print(inst)
                    # but may be overridden in exception subclasses
        return info

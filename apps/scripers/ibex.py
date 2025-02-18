from bs4 import BeautifulSoup
from requests_html import HTMLSession

from datetime import datetime, timedelta
from pytz import timezone, utc
from decimal import Decimal
from vei_platform_api import VeiPlatformAPI


def conver_bgn_to_eur(price):
    return str((Decimal(price) / Decimal("1.95583")).quantize(Decimal("1.00")))


def energy_price_entry(start_interval, price):
    end_interval = start_interval + timedelta(hours=1)
    return {
        "price": conver_bgn_to_eur(price),
        "start_interval": start_interval,
        "end_interval": end_interval,
    }


def parse_ibex(soup):
    table1 = soup.find("table", {"id": "wpdtSimpleTable-33"})
    table_rows = table1.find_all("tr")
    first = True
    localtimezone = timezone("Europe/Sofia")
    entries = []
    for tr in table_rows:
        tag = "th" if first else "td"
        td = tr.find_all(tag)
        row = [i.text.replace("\n", "").strip() for i in td]
        if first:
            row[0] = "Hour"
            row[1] = "Unit"
            head = row
        else:
            if len(head) == len(row):
                for i in range(len(head) - 2):
                    price = row[i + 2]
                    date = head[i + 2].split(",")[1]
                    month = int(date.split("/")[0])
                    day = int(date.split("/")[1])
                    hour = int(row[0].split("-")[0])
                    year = datetime.now().year
                    d = datetime(
                        year=year, month=month, day=day, hour=hour, minute=0, second=0
                    )
                    d = localtimezone.localize(d)
                    d = d.astimezone(utc)
                    try:
                        p = Decimal(price)
                        entry = energy_price_entry(d, price)
                        entry["unit"] = row[1]
                        entries.append(entry)
                    except:
                        print("Skiping price = " + price + " at " + str(d))
            if len(head) == len(row) + 1:
                for i in range(len(head) - 2):
                    volume = row[i + 1]
                    date = head[i + 2].split(",")[1]
                    month = int(date.split("/")[0])
                    day = int(date.split("/")[1])
                    # hour = int(row[0].split("-")[0])
                    year = datetime.now().year
                    d = datetime(
                        year=year, month=month, day=day, hour=hour, minute=0, second=0
                    )
                    d = localtimezone.localize(d)
                    d = d.astimezone(utc)
                    try:
                        v = Decimal(volume)
                        for i in range(len(entries)):
                            if entries[i]["start_interval"] == d:
                                entries[i].update(
                                    {"volume_in_kwh": Decimal(volume) * Decimal(1000)}
                                )
                    except:
                        print("Skiping volume = " + volume + " at " + str(d))

        first = False
    return sorted(entries, key=lambda k: k["start_interval"])


def prepare_entries_for_post(entries):
    res = {}
    price = []
    unix_seconds = []
    volume = []
    for p in entries:
        res["unit"] = p["unit"]
        unix_seconds.append(int(p["start_interval"].timestamp()))
        price.append(p["price"])
        volume.append(p["volume_in_kwh"])
    res["unit"] = entries[0]["unit"]
    res["price"] = price
    res["unix_seconds"] = unix_seconds
    res["volume_in_kwh"] = volume
    print(res)
    return res


class IBexScriper:
    base_url = "https://ibex.bg/"
    #'https://ibex.bg/%D0%B4%D0%B0%D0%BD%D0%BD%D0%B8-%D0%B7%D0%B0-%D0%BF%D0%B0%D0%B7%D0%B0%D1%80%D0%B0/%D0%BF%D0%B0%D0%B7%D0%B0%D1%80%D0%B5%D0%BD-%D1%81%D0%B5%D0%B3%D0%BC%D0%B5%D0%BD%D1%82-%D0%B4%D0%B5%D0%BD-%D0%BD%D0%B0%D0%BF%D1%80%D0%B5%D0%B4/day-ahead-prices-and-volumes-v2-0/'
    prices_path = "%d0%b4%d0%b0%d0%bd%d0%bd%d0%b8-%d0%b7%d0%b0-%d0%bf%d0%b0%d0%b7%d0%b0%d1%80%d0%b0/%d0%bf%d0%b0%d0%b7%d0%b0%d1%80%d0%b5%d0%bd-%d1%81%d0%b5%d0%b3%d0%bc%d0%b5%d0%bd%d1%82-%d0%b4%d0%b5%d0%bd-%d0%bd%d0%b0%d0%bf%d1%80%d0%b5%d0%b4/day-ahead-prices-and-volumes-v2-0/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
    }
    billing_zones = {
        "BG": "Bulgaria",
    }

    def fetch_prices_day_ahead(self, billing_zone="BG"):
        if billing_zone != "BG":
            return
        session = HTMLSession()
        prices = session.get(self.base_url + self.prices_path, headers=self.headers)
        prices.html.render()  # this call executes the js in the page
        table1 = prices.html.find("#wpdtSimpleTable-33")[0]
        soup = BeautifulSoup(table1.html, "html.parser")
        ibex_data = parse_ibex(soup)
        # for e in ibex_data:
        #    print(e)
        return prepare_entries_for_post(ibex_data)

    def get_currency_and_unit(self, prices):
        currency, energy_unit = prices["unit"].split("/")
        if currency == "BGN":
            currency = "EUR"
        return currency, energy_unit

    def get_plan_name(self, zone_name):
        plan_name = "BG Day ahead"
        return plan_name

    def process(self, target_list):
        for zone in self.billing_zones.keys():
            prices = self.fetch_prices_day_ahead(zone)
            if prices:
                for target in target_list:
                    try:
                        vei_platform = VeiPlatformAPI(
                            target["url"], token=target["token"]
                        )
                        res = vei_platform.prepare_and_post_prices(self, zone, prices)
                        vei_platform.report_result(res)

                        # res = vei_platform.prepare_and_post_production(
                        #    self, factory_name="Гигамрежата 33", production=prices
                        # )
                        vei_platform.report_result(res)

                        # break
                    except Exception as e:
                        message = getattr(e, "message", repr(e))
                        print(
                            "Exception %s when processing Target %s token=%.4s.."
                            % (message, target["url"], target["token"])
                        )
                        raise e
            else:
                print("Fail to fetch zone = " + zone)

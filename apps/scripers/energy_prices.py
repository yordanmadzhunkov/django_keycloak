# pip install requests
import requests
from prettytable import PrettyTable
from decimal import Decimal
from datetime import datetime, timedelta, timezone as dt_timezone
from tzlocal import get_localzone  # $ pip install tzlocal
import json

# from scripers.ibex import IBexScriper
# from .ibex import IBexScriper


from decouple import config
import requests
from prettytable import PrettyTable
from bs4 import BeautifulSoup
from requests_html import HTMLSession, HtmlElement
from datetime import datetime, timedelta
from pytz import timezone, utc
from decimal import Decimal


def timestamp_to_datetime(timestamp):
    return datetime.fromtimestamp(timestamp, tz=dt_timezone.utc)


def energy_price_entry(start_interval, price):
    end_interval = start_interval + timedelta(hours=1)
    return {
        #'plan': 'day-ahead-bulgaria-2',
        "price": str((Decimal(price) / Decimal("1.95583")).quantize(Decimal("0.01"))),
        "start_interval": start_interval,  # .strftime("%Y-%m-%dT%H:%M:%S%z"),
        "end_interval": end_interval,  # .strftime("%Y-%m-%dT%H:%M:%S%z"),
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
            prices_pretty_table = PrettyTable(row)
        else:
            if len(head) == len(row):
                prices_pretty_table.add_row(row)
                for i in range(len(row) - 2):
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
                    entry = energy_price_entry(d, price)
                    entry["unit"] = row[1]
                    entries.append(entry)
        first = False
    return sorted(entries, key=lambda k: k["start_interval"])


def prepare_entries_for_post(entries):
    res = {}
    price = []
    unix_seconds = []
    for p in entries:
        res["unit"] = p["unit"]
        unix_seconds.append(int(p["start_interval"].timestamp()))
        price.append(p["price"])
    res["unit"] = entries[0]["unit"]
    res["price"] = price
    res["unix_seconds"] = unix_seconds
    return res


def render_entries_to_pretty_table(entries):
    prices_pretty_table = PrettyTable(["Date & time", "price", "unit"])
    for p in entries:
        prices_pretty_table.add_row(
            [
                p["start_interval"],
                p["price"],
                p["unit"],
            ]
        )
    return prices_pretty_table


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
        return prepare_entries_for_post(ibex_data)

    def parse_soup(self, soup):
        entries = parse_ibex(soup)
        print(entries)

    def get_currency_and_unit(self, prices):
        return prices["unit"].split("/")

    def print_prices(self, prices, billing_zone):
        unit = prices["unit"]
        price = prices["price"]
        time_slot_in_unix = prices["unix_seconds"]

        prices_table = PrettyTable(
            ["UTC Date", "UTC Time", "Price " + unit, "Local Time", "Local Date"]
        )
        prices_table.title = "Billing zone = " + self.billing_zones[billing_zone]
        for i in range(len(price)):
            d = timestamp_to_datetime(time_slot_in_unix[i])
            p = Decimal(price[i]).quantize(Decimal("0.01"))
            # print(d + ' '  + str(price[i]) + ' ' + unit)
            ld = d.astimezone(get_localzone())
            prices_table.add_row(
                [
                    d.strftime("%Y-%m-%d"),
                    d.strftime("%H:%M:%S %Z"),
                    p,
                    ld.strftime("%H:%M:%S %Z"),
                    ld.strftime("%Y-%m-%d"),
                ]
            )
        print(prices_table)

    def get_plan_name(self, zone_name):
        plan_name = "BG Day ahead"
        return plan_name


# Send a GET request to a website
# res = requests.get(
#    "https://www.example.com/", # The URL of the API you want to access
#    params={"key1": "value1", "key2": "value2"}, # The parameters you want to pass to the API (like "?key=value" at the end of the URL)
#    data={"key1": "value1", "key2": "value2"}, # The data you want to send to the API
#    headers={"header1": "value1", "header2": "value2"}, # The headers you want to send to the API
#    cookies={"cookie1": "value1", "cookie2": "value2"}, # The cookies you want to send to the API
#    auth=("username", "password"), # The authentication credentials you want to send to the API (some websites require this)
#    timeout=5, # The maximum site response time (in seconds)
#    allow_redirects=True, # Whether or not to follow redirects
# )

# Send a POST request to a website
# res = requests.post(...)

# Send a PUT request to a website
# res = requests.put(...)

# Send a DELETE request to a website
# res = requests.delete(...)


# if res.status_code == 200:
#    output = res.json()
#    print(output)


class EnergyChartsAPI:
    base_url = "https://api.energy-charts.info"
    billing_zones = {
        "AT": "Austria",
        "BE": "Belgium",
        "BG": "Bulgaria",
        "CH": "Switzerland",
        "CZ": "Czech Republic",
        "DE-LU": "Germany, Luxembourg",
        "DE-AT-LU": "Germany, Austria, Luxembourg",
        "DK1": "Denmark 1",
        "DK2": "Denmark 2",
        "EE": "Estionia",
        "ES": "Spain",
        "FI": "Finland",
        "FR": "France",
        "GR": "Greece",
        "HR": "Croatia",
        "HU": "Hungary",
        "IT-Calabria": "Italy Calabria",
        "IT-Centre-North": "Italy Centre North",
        "IT-Centre-South": "Italy Centre South",
        "IT-North": "Italy North",
        "IT-SACOAC": "Italy Sardinia Corsica AC",
        "IT-SACODC": "Italy Sardinia Corsica DC",
        "IT-Sardinia": "Italy Sardinia",
        "IT-Sicily": "Italy Sicily",
        "IT-South": "Italy South",
        "LT": "Lithuania",
        "LV": "Latvia",
        "ME": "Montenegro",
        "NL": "Netherlands",
        "NO1": "Norway 1",
        "NO2": "Norway 2",
        "NO2NSL": "Norway North Sea Link",
        "NO3": "Norway 3",
        "NO4": "Norway 4",
        "NO5": "Norway 5",
        "PL": "Poland",
        "PT": "Portugal",
        "RO": "Romania",
        "RS": "Serbia",
        "SE1": "Sweden 1",
        "SE2": "Sweden 2",
        "SE3": "Sweden 3",
        "SE4": "Sweden 4",
        "SI": "Slovenia",
        "SK": "Slovakia",
    }

    def fetch_and_print_openapi_specs(self):
        openapi_spec = requests.get(self.base_url + "/openapi.json")
        if openapi_spec.status_code == 200:
            openapi_spec = openapi_spec.json()

            openapi = openapi_spec["openapi"]
            info = openapi_spec["info"]
            paths = openapi_spec["paths"]
            components = openapi_spec["components"]
            tags = openapi_spec["tags"]

            print("OpenAPI version: " + openapi)
            print(info.keys())
            print(info["title"] + ": v" + info["version"])
            print(info["description"])
            print("-------------------------------------------------")
            table = PrettyTable(["Path", "Summary"])
            table.align["Path"] = "l"
            table.align["Summary"] = "c"
            for p in paths.keys():
                table.add_row([p, paths[p]["get"]["summary"]])
            print(table)

    def fetch_prices_day_ahead(self, billing_zone="BG"):
        prices = requests.get(
            self.base_url + "/price",  # The URL of the API you want to access
            params={
                "bzn": billing_zone,
            },  # The parameters you want to pass to the API (like "?key=value" at the end of the URL)
        )
        if prices.status_code == 200:
            return prices.json()
        return None

    def print_prices(self, prices, billing_zone):
        unit = prices["unit"]
        price = prices["price"]
        time_slot_in_unix = prices["unix_seconds"]

        prices_table = PrettyTable(
            ["UTC Date", "UTC Time", "Price " + unit, "Local Time", "Local Date"]
        )
        prices_table.title = "Billing zone = " + self.billing_zones[billing_zone]
        for i in range(len(price)):
            d = timestamp_to_datetime(time_slot_in_unix[i])
            p = Decimal(price[i]).quantize(Decimal("0.01"))
            # print(d + ' '  + str(price[i]) + ' ' + unit)
            ld = d.astimezone(get_localzone())
            prices_table.add_row(
                [
                    d.strftime("%Y-%m-%d"),
                    d.strftime("%H:%M:%S %Z"),
                    p,
                    ld.strftime("%H:%M:%S %Z"),
                    ld.strftime("%Y-%m-%d"),
                ]
            )
        print(prices_table)

    def get_plan_name(self, zone_name):
        plan_name = "Day ahead %s" % zone_name
        return plan_name

    def get_currency_and_unit(self, prices):
        return prices["unit"].split("/")


class VeiPlatformAPI:
    token = None
    endpoint_base_url = "http://127.0.0.1:8000/"
    hello_url = "api/v1/hello"
    billing_zone_url = "api/v1/billing_zones"
    plans_url = "api/v1/plans"
    prices_url = "api/v1/prices"

    def __init__(self, endpoint_url, token):
        self.token = token
        self.endpoint_base_url = endpoint_url
        self.headers = {
            "Authorization": "Token " + token,
            "Content-Type": "application/json",
        }

    def check_billing_zone(self, billing_zone):
        full_url = self.endpoint_base_url + self.billing_zone_url
        response = requests.get(
            full_url,
            data={},
            headers=self.headers,
        )
        if response.status_code == 200:
            found = None
            for zone in response.json():
                if zone["code"] == billing_zone:
                    found = zone
        else:
            return {
                "error": "response check_billing_zone Status is not OK",
                "status": response.status_code,
                "reason": response.reason,
            }

        if not found:
            return {"error": "Billing zone " + billing_zone + "is NOT supported"}

        return {
            "check_billing_zone": "OK",
            "code": found["code"],
            "name": found["name"],
        }

    def get_plan(self, billing_zone, name=None):
        response = requests.get(
            self.endpoint_base_url + self.plans_url,
            data={},
            headers=self.headers,
        )
        if response.status_code == 200:
            target_plan = None
            for plan in response.json():
                if plan["billing_zone"] == billing_zone:
                    if name is None or name == plan["name"]:
                        target_plan = plan
                        break
                    else:
                        print("skipping %s" % str(plan))

            return {"plan": target_plan}
        else:
            return {"error": "response Status is not OK"}

    def create_plan(
        self, billing_zone, name, currency="EUR", electricity_unit="MWh"
    ) -> dict:
        data = {
            "name": name,
            "billing_zone": billing_zone,
            "description": "Most basic day ahead plan",
            "currency": currency,
            "electricity_unit": electricity_unit,
        }
        response = requests.post(
            self.endpoint_base_url + self.plans_url,
            data=json.dumps(data),
            headers=self.headers,
        )
        if response.status_code == 201:
            plan = response.json()
            print("created " + str(plan))
            return {"plan": plan}
        else:
            return {"error": "response Status is not CREATED"}

    def get_or_create_plan(
        self, billing_zone, plan_name=None, currency="EUR", energy_unit="MWh"
    ):
        res = self.get_plan(billing_zone=billing_zone, name=plan_name)
        print(res)
        if not "error" in res.keys() and "plan" in res.keys():
            if res["plan"] is None:
                new_plan = self.create_plan(
                    billing_zone=billing_zone,
                    name=plan_name,
                    currency=currency,
                    electricity_unit=energy_unit,
                )
                print(new_plan)
                res.update(new_plan)
        return res

    def time_params(self, start_interval, end_interval):
        res = {
            "start_interval": start_interval.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "end_interval": end_interval.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        return res

    def compute_time_windows(self, timestamps, window_size=timedelta(hours=1)):
        start_timestamp = timestamps[0]
        end_timestamp = timestamps[0]
        for i in range(len(timestamps)):
            if start_timestamp > timestamps[i]:
                start_timestamp = timestamps[i]
            if end_timestamp < timestamps[i]:
                end_timestamp = timestamps[i]
        start_interval = timestamp_to_datetime(start_timestamp)
        end_interval = timestamp_to_datetime(end_timestamp)
        end_interval = end_interval + window_size
        return start_interval, end_interval

    def compute_ovelaping_prices(self, plan, timestamps, price):
        start_interval, end_interval = self.compute_time_windows(timestamps)
        params = self.time_params(start_interval, end_interval)
        # print("PARAMS = " + str(params))
        params["plan"] = plan

        response = requests.get(
            self.endpoint_base_url + self.prices_url,
            params=params,
            headers=self.headers,
        )
        new_prices_to_post = []
        matched_prices = []
        wrong_price = []
        # print(params)
        if response.status_code == 200:
            server_prices = response.json()
            server_prices.sort(key=lambda x: x["start_interval"])
            # timestamps.sort()

            j = 0

            for i in range(len(timestamps)):
                start_interval = timestamp_to_datetime(timestamps[i])
                end_interval = start_interval + timedelta(hours=1)
                data = {
                    "plan": plan,
                    "price": str(Decimal(price[i]).quantize(Decimal("0.01"))),
                }
                data.update(self.time_params(start_interval, end_interval))

                while j < len(server_prices):
                    s = datetime.strptime(
                        server_prices[j]["start_interval"], "%Y-%m-%dT%H:%M:%S%z"
                    )
                    if s < start_interval:
                        j = j + 1
                    else:
                        break

                if j < len(server_prices):
                    s = datetime.strptime(
                        server_prices[j]["start_interval"], "%Y-%m-%dT%H:%M:%S%z"
                    )
                    if s == start_interval:
                        if data["price"] == server_prices[j]["price"]:
                            matched_prices.append(data)
                        else:
                            wrong_price.append(data)
                        j = j + 1
                        continue

                new_prices_to_post.append(data)

        return new_prices_to_post, matched_prices, wrong_price

    def response_to_pretty_table(self, response, plan_slug, unit, status):
        prices_table = PrettyTable(["UTC Date & Time", "Price " + unit, "Status"])
        prices_table.title = " Slug = " + plan_slug
        for val in response:
            prices_table.add_row([val["start_interval"], val["price"], status])
        return prices_table

    def post_prices(self, plan_info, prices):
        print(plan_info)
        unit = prices["unit"]
        price = prices["price"]
        time_slot_in_unix = prices["unix_seconds"]
        plan_slug = plan_info["slug"]
        res = {}
        new_prices_to_post, matched_prices, wrong_price = self.compute_ovelaping_prices(
            plan_slug, time_slot_in_unix, price
        )
        if len(new_prices_to_post) == 0:

            res["info"] = (
                "Skiping update on %s because there is not new prices, Matched prices count = %d"
                % (plan_slug, len(matched_prices))
            )
            return res

        bulk_data = new_prices_to_post
        if len(bulk_data) > 0:
            response = requests.post(
                self.endpoint_base_url + self.prices_url,
                data=json.dumps(bulk_data),
                headers=self.headers,
            )
            if response.status_code == 201:
                return self.response_to_pretty_table(
                    response.json(), plan_slug, unit, "Created"
                )
            else:
                res["error"] = "failed to create bulk data"
        return res


def report_result(res, showInfo=True):
    if isinstance(res, dict):
        if "error" in res.keys():
            print(
                'Error "%s" when processing Target %s token=%.4s..'
                % (res["error"], target["url"], target["token"])
            )
        if showInfo and "info" in res.keys():
            print(
                'Info "%s" when processing Target %s token=%.4s..'
                % (res["info"], target["url"], target["token"])
            )
    else:
        print(res)


def process_scriper(energy_prices_api, target_list):
    for zone in energy_prices_api.billing_zones.keys():
        prices = energy_prices_api.fetch_prices_day_ahead(zone)
        if prices:
            currency, energy_unit = energy_prices_api.get_currency_and_unit(prices)
            energy_prices_api.print_prices(prices, zone)
            for target in target_list:
                try:
                    vei_platform = VeiPlatformAPI(target["url"], token=target["token"])
                    billing_zone_info = vei_platform.check_billing_zone(zone)
                    if "error" in billing_zone_info.keys():
                        report_result(billing_zone_info)
                        continue
                    plan_name = energy_prices_api.get_plan_name(
                        billing_zone_info["name"]
                    )
                    plan_info = vei_platform.get_or_create_plan(
                        zone, plan_name, currency, energy_unit
                    )
                    report_result(plan_info)
                    if "plan" in plan_info.keys():
                        report_result(
                            vei_platform.post_prices(plan_info["plan"], prices)
                        )
                    break
                except Exception as e:
                    message = getattr(e, "message", repr(e))
                    print(
                        "Exception %s when processing Target %s token=%.4s.."
                        % (message, target["url"], target["token"])
                    )
                    raise e
        else:
            print("Fail to fetch zone = " + zone)


if __name__ == "__main__":

    # ENERGY_BOT_TARGETS = config('ENERGY_BOT_TARGETS', '[{"url": "http://127.0.0.1:8000/", "token":"6da8aa16d75593c3d9c7029acc59caf59dd5a446"},{"url":"https://fractionenergy.eu/", "token":"dfgsgfdsfsdgd"}]')
    ENERGY_BOT_TARGETS = config(
        "ENERGY_BOT_TARGETS",
        '[{"url": "http://127.0.0.1:8000/", "token":"6da8aa16d75593c3d9c7029acc59caf59dd5a446"},',
    )

    target_list = json.loads(ENERGY_BOT_TARGETS)

    for target in target_list:
        print("Target %s token=%.4s.." % (target["url"], target["token"]))

    process_scriper(IBexScriper(), target_list)
    process_scriper(EnergyChartsAPI(), target_list)

    # energy_prices_api.fetch_and_print_openapi_specs()

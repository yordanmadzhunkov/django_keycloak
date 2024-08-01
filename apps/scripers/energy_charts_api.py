import requests
from prettytable import PrettyTable


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

    def get_plan_name(self, zone_name):
        plan_name = "Day ahead %s" % zone_name
        return plan_name

    def get_currency_and_unit(self, prices):
        return prices["unit"].split("/")

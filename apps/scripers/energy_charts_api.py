import requests
from prettytable import PrettyTable
from vei_platform_api import VeiPlatformAPI
from datetime import datetime


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

    def fetch_prices_day_ahead(self, billing_zone="BG", start=None, end=None):
        params = {
            "bzn": billing_zone,
        }
        if start:
            params["start"] = int(start.strftime("%s"))
        if end:
            params["end"] = int(end.strftime("%s"))
        # Returns the day-ahead spot market price for a specified bidding zone in EUR/MWh.
        # Available bidding zones (bzn) are shown above.
        # Response schema:
        # json
        # {
        #    "license_info": str,
        #    "unix_seconds": [int],
        #    "price": [float],
        #    "unit": str,
        #    "deprecated": bool
        # }'
        prices = requests.get(self.base_url + "/price", params)
        if prices.status_code == 200:
            return prices.json()
        return None

    def get_plan_name(self, zone_name):
        plan_name = "Day ahead %s" % zone_name
        return plan_name

    def get_currency_and_unit(self, prices):
        return prices["unit"].split("/")

    def process(self, target_list, start: datetime = None, end: datetime = None):
        for zone in self.billing_zones.keys():
            prices_response = self.fetch_prices_day_ahead(zone, start, end)
            if prices_response:
                for target in target_list:
                    try:
                        vei_platform = VeiPlatformAPI(
                            target["url"], token=target["token"]
                        )
                        res = vei_platform.prepare_and_post_prices(
                            self, zone, prices_response
                        )
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

import requests
from prettytable import PrettyTable
from vei_platform_api import VeiPlatformAPI
from datetime import datetime, timezone
from utils import timestamp_to_datetime, str_to_datetime, datetime_to_str
from utils import print_green, print_yellow, print_blue, print_red, green, yellow
from decimal import Decimal


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

    def fetch_prices_day_ahead(self, billing_zone="BG", start: datetime = None, end: datetime = None):
        params = {
            "bzn": billing_zone,
        }
        if start:
            params["start"] = int(start.timestamp())
        if end:
            params["end"] = int(end.timestamp()) - 1
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
        #print(params)
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
            self.process_zone(zone, target_list, start, end)
    
    def process_zone(self, zone, target_list, start: datetime = None, end: datetime = None):
        prices_response = self.fetch_prices_day_ahead(zone, start, end)
        if prices_response:
            for target in target_list:
                self.process_prices_response(zone, prices_response, target)
        else:
            print("Fail to fetch zone = " + zone)

    
    def process_prices_response(self, zone, prices_response, target):
        try:
            if isinstance(target, dict):
                vei_platform = VeiPlatformAPI(target["url"], token=target["token"])
            if isinstance(target, VeiPlatformAPI):
                vei_platform = target
            res = vei_platform.prepare_and_post_prices(self, zone, prices_response)
            vei_platform.report_result(res)
            # break
        except Exception as e:
            message = getattr(e, "message", repr(e))
            print_red(
                "Exception %s when processing Target %s token=%.4s.."
                % (message, target["url"], target["token"])
            )
            #raise e


    def process_historical(self, target_list, months = 12):
        for target in target_list:
            vei_platform = VeiPlatformAPI(target["url"], token=target["token"])
            for zone in self.billing_zones.keys():
                plans = vei_platform.get_all_plans_in_zone(billing_zone=zone)
                my_plan_name = self.get_plan_name(zone_name=self.billing_zones[zone])
                for plan in plans:
                    if plan['owner'] == 'energy_bot' and plan['name'] == my_plan_name:
                        self.process_historical_for_plan(vei_platform, plan, months)

    def check_for_missing_prices(self, 
                                 vei_platform: VeiPlatformAPI, 
                                 plan: dict, 
                                 start_interval:datetime, 
                                 end_interval:datetime) -> bool:
        delta = end_interval-start_interval
        total_hours = int(delta.total_seconds() // 3600)
        if total_hours == 0:
            return False
        server_prices = vei_platform.get_server_values_in_timewindow(
            vei_platform.prices_url, start_interval, end_interval, params={"plan": plan["slug"]}
        )
        has_missing = total_hours > len(server_prices)
        return has_missing

    def begining_of_month(self, date_in_month: datetime)-> datetime:
        return date_in_month.replace(day=1, hour=0, minute=0, second = 0, microsecond=0)
    
    def previous_month(self, start_of_month: datetime) -> datetime:
        month = start_of_month.month
        year = start_of_month.year
        if month > 1:
            month -= 1
        else:
            year -= 1
            month = 12
        return start_of_month.replace(year=year, month=month, day=1, hour=0, minute=0, second = 0, microsecond=0)


    def process_historical_for_plan(self, vei_platform: VeiPlatformAPI, plan, months: int):
        zone = plan['billing_zone']
        # Current month
        end_interval = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second = 0, microsecond=0)
        start_interval = self.begining_of_month(end_interval)
        if self.check_for_missing_prices(vei_platform, plan, start_interval, end_interval):
            self.process_zone(zone, [vei_platform], start_interval, end_interval)        

        for m in range(months):
            end_interval = start_interval
            start_interval = self.previous_month(end_interval)
            if self.check_for_missing_prices(vei_platform, plan, start_interval, end_interval):
                self.process_zone(zone, [vei_platform], start_interval, end_interval)

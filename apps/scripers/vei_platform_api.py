import requests
from prettytable import PrettyTable
from datetime import datetime, timedelta
from decimal import Decimal
from utils import timestamp_to_datetime, str_to_datetime, datetime_to_str
from utils import print_green, print_yellow, print_blue, print_red, green, yellow

# pip install requests
from prettytable import PrettyTable
from decimal import Decimal
from datetime import datetime, timedelta
from tzlocal import get_localzone  # $ pip install tzlocal
import json


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


def print_prices(prices, billing_zone):
    unit = prices["unit"]
    price = prices["price"]
    time_slot_in_unix = prices["unix_seconds"]

    prices_table = PrettyTable(
        ["UTC Date", "UTC Time", "Price " + unit, "Local Time", "Local Date"]
    )
    prices_table.title = "Billing zone = " + billing_zone
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


class VeiPlatformAPI:
    token = None
    endpoint_base_url = "http://127.0.0.1:8000/"
    hello_url = "api/v1/hello"
    billing_zone_url = "api/v1/billing_zones"
    plans_url = "api/v1/plans"
    prices_url = "api/v1/prices"

    factories_url = "api/v1/factories"
    production_url = "api/v1/production"

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
                        print_yellow("skipping %s" % str(plan))

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
        print_green(res)
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
            "start_interval": datetime_to_str(start_interval),
            "end_interval": datetime_to_str(end_interval),
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

        # print('compute_ovelaping_prices')
        if response.status_code == 200:
            server_prices = response.json()
            server_prices.sort(key=lambda x: x["start_interval"])
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
                    s = str_to_datetime(server_prices[j]["start_interval"])
                    if s < start_interval:
                        j = j + 1
                    else:
                        break

                if j < len(server_prices):
                    s = str_to_datetime(server_prices[j]["start_interval"])
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

    def render_row(self, val, status):
        return [
            str_to_datetime(val["start_interval"]).strftime("%Y-%m-%d"),
            str_to_datetime(val["start_interval"]).strftime("%H")
            + " - "
            + str_to_datetime(val["end_interval"]).strftime("%H"),
            val["price"],
            status,
        ]

    def render_request_table(self, plan_info, new, match, different):
        currency = plan_info["currency"]
        electricity_unit = plan_info["electricity_unit"]
        table = PrettyTable(
            [
                "Date UTC",
                "Time window UTC",
                "Price " + currency + "/" + electricity_unit,
                "Status",
            ]
        )
        table.title = plan_info["name"] + "Billing zone = " + plan_info["billing_zone"]
        rows = (
            [self.render_row(val, green("Match")) for val in match]
            + [self.render_row(val, green("New")) for val in new]
            + [self.render_row(val, yellow("For update")) for val in different]
        )
        rows = sorted(rows, key=lambda x: (x[0], x[1]))
        table.add_rows(rows)
        return table

    def post_prices(self, plan_info, prices):
        # print(plan_info)
        unit = prices["unit"]
        price = prices["price"]
        time_slot_in_unix = prices["unix_seconds"]
        plan_slug = plan_info["slug"]
        res = {}
        new_prices_to_post, matched_prices, wrong_price = self.compute_ovelaping_prices(
            plan_slug, time_slot_in_unix, price
        )

        table = self.render_request_table(
            plan_info, new_prices_to_post, matched_prices, wrong_price
        )
        print(table)
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

    def prepare_and_post_prices(self, scriper, zone, prices):
        billing_zone_info = self.check_billing_zone(zone)
        if "error" in billing_zone_info.keys():
            self.report_result(billing_zone_info)
            return
        plan_name = scriper.get_plan_name(billing_zone_info["name"])
        currency, energy_unit = scriper.get_currency_and_unit(prices)

        plan_info = self.get_or_create_plan(zone, plan_name, currency, energy_unit)
        self.report_result(plan_info)
        if "plan" in plan_info.keys():
            self.report_result(self.post_prices(plan_info["plan"], prices))

    def report_result(self, res, showInfo=True):
        url = self.endpoint_base_url
        token = self.token

        if isinstance(res, dict):
            if "error" in res.keys():
                print_red(
                    'Error "%s" when processing Target %s token=%.4s..'
                    % (res["error"], url, token)
                )
            if showInfo and "info" in res.keys():
                print_blue(
                    'Info "%s" when processing Target %s token=%.4s..'
                    % (res["info"], url, token)
                )
        else:
            print(res)

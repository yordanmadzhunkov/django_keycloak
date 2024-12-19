import requests
from prettytable import PrettyTable
from datetime import datetime, timedelta
from decimal import Decimal
from utils import timestamp_to_datetime, str_to_datetime, datetime_to_str
from utils import print_green, print_yellow, print_blue, print_red, green, yellow

# pip install requests
from decimal import Decimal
from tzlocal import get_localzone  # $ pip install tzlocal
import json

import time


class VeiPlatformAPI:
    token = None
    endpoint_base_url = "http://127.0.0.1:8000/"
    hello_url = "api/v1/hello"
    billing_zone_url = "api/v1/zones"
    plans_url = "api/v1/plans"
    plan_summary_url = "api/v1/plan/summary"
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
        print_blue("GET REQUEST TO " + full_url + " HEADERS = " + str(self.headers))
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
            print_red(
                "Response CODE = "
                + str(response.status_code)
                + " REASON = "
                + str(response.reason)
            )
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

    def get_all_plans_in_zone(self, billing_zone):
        response = requests.get(
            self.endpoint_base_url + self.plans_url,
            data={},
            headers=self.headers,
        )
        if response.status_code == 200:
            res = []
            for plan in response.json():
                if plan["billing_zone"] == billing_zone:
                    res.append(plan)
            return res
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
        # print_green(res)
        if not "error" in res.keys() and "plan" in res.keys():
            if res["plan"] is None:
                new_plan = self.create_plan(
                    billing_zone=billing_zone,
                    name=plan_name,
                    currency=currency,
                    electricity_unit=energy_unit,
                )
                # print(new_plan)
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

    def get_server_values_in_timewindow(
        self, url, start_interval: datetime, end_interval: datetime, params
    ):
        # start_interval, end_interval = self.compute_time_windows(timestamps)
        params.update(self.time_params(start_interval, end_interval))
        response = requests.get(
            self.endpoint_base_url + url,
            params=params,
            headers=self.headers,
        )
        return response.json() if response.status_code == 200 else None

    def compute_ovelaping_prices(
        self, initial_data, value_key, timestamps, values, server_values
    ):
        new_prices_to_post = []
        matched_prices = []
        wrong_price = []
        server_values.sort(key=lambda x: x["start_interval"])
        j = 0
        for i in range(len(timestamps)):
            start_interval = timestamp_to_datetime(timestamps[i])
            end_interval = start_interval + timedelta(hours=1)
            data = initial_data.copy()
            if values[i] is None:
                print_yellow("None price for start_interval = %s" % str(start_interval))
                continue
            else:
                data.update(
                    {
                        # slug_key: slug,
                        value_key: str(Decimal(values[i]).quantize(Decimal("0.01"))),
                    }
                )
                data.update(self.time_params(start_interval, end_interval))

                while j < len(server_values):
                    s = str_to_datetime(server_values[j]["start_interval"])
                    if s < start_interval:
                        j = j + 1
                    else:
                        break

                if j < len(server_values):
                    s = str_to_datetime(server_values[j]["start_interval"])
                    if s == start_interval:
                        if data[value_key] == server_values[j][value_key]:
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
        table.title = plan_info["name"] + " Billing zone = " + plan_info["billing_zone"]
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
        scriper_prices = prices["price"]
        time_slot_in_unix = prices["unix_seconds"]
        plan_slug = plan_info["slug"]
        res = {}
        start_interval, end_interval = self.compute_time_windows(time_slot_in_unix)

        server_prices = self.get_server_values_in_timewindow(
            self.prices_url,
            start_interval,
            end_interval,
            params={"plan": plan_info["slug"]},
        )
        if server_prices is None:
            res["error"] = "failed to get server prices for comparisons"
            return res

        new_prices_to_post, matched_prices, wrong_price = self.compute_ovelaping_prices(
            {"plan": plan_slug},
            "price",
            time_slot_in_unix,
            scriper_prices,
            server_prices,
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
            return billing_zone_info

        plan_name = scriper.get_plan_name(billing_zone_info["name"])
        currency, energy_unit = scriper.get_currency_and_unit(prices)

        plan_info = self.get_or_create_plan(zone, plan_name, currency, energy_unit)
        if "plan" in plan_info.keys():
            self.get_plan_summary_and_update_plan(plan_info["plan"])
            self.show_plan_info(plan_info["plan"])
            return self.post_prices(plan_info["plan"], prices)
        else:
            return plan_info

    def get_plan_summary_and_update_plan(self, plan):
        params = {"plan": plan["slug"]}
        response = requests.get(
            self.endpoint_base_url + self.plan_summary_url,
            params=params,
            headers=self.headers,
        )
        if response.status_code == 200:
            plan.update(response.json())

        # return response.json() if response.status_code == 200 else None
        # reverse("plan_summary_api"), data
        # return None

    def show_plan_info(self, plan):
        table = PrettyTable(["-", plan["name"]])
        table.title = plan["name"] + " Billing zone = " + plan["billing_zone"]
        table.add_rows(
            [
                ["Description", plan["description"]],
                ["Slug", plan["slug"]],
                ["Currency", plan["currency"]],
                ["Electricity unit", plan["electricity_unit"]],
                ["Owner", plan["owner"]],
            ]
        )
        if "last_price_start_interval" in plan.keys():
            table.add_row(["Last update", plan["last_price_start_interval"]])
        if "last_gap" in plan.keys():
            table.add_row(["Last gap", plan["last_gap"]])
        if "last_overlap" in plan.keys():
            table.add_row(["Last overlap", plan["last_overlap"]])
        print_green(table)

    def get_my_factories(self):
        data = {}
        response = requests.get(
            self.endpoint_base_url + self.factories_url,
            data=json.dumps(data),
            headers=self.headers,
        )
        if response.status_code == 200:
            factories = response.json()
            # print("created " + str(plan))
            return {"factories": factories}
        else:
            return {
                "error": "response Status is not OK, probably missing authentication token"
            }

    def find_factory_slug(self, factory_name, num_retries=3):
        factories = {}
        for i in range(num_retries):
            factories = self.get_my_factories()
            if "factories" in factories.keys():
                break
            # Sleep 3 seconds
            time.sleep(3)
        if "factories" in factories.keys():
            for f in factories["factories"]:
                if f["name"] == factory_name:
                    factory_slug = f["slug"]
                    return factory_slug
        return None

    def prepare_and_post_production(self, factory_name, production):
        factory_slug = self.find_factory_slug(factory_name)
        if factory_slug:
            timestamps = production["unix_seconds"]
            volume_in_kwh = production["volume_in_kwh"]
            start_interval, end_interval = self.compute_time_windows(timestamps)

            server_values = self.get_server_values_in_timewindow(
                self.production_url,
                start_interval,
                end_interval,
                params={"factory": factory_slug},
            )
            new, matched, different = self.compute_ovelaping_prices(
                {"factory": factory_slug},
                "energy_in_kwh",
                timestamps,
                volume_in_kwh,
                server_values,
            )
            if len(new) == 0:
                return {
                    "info": "Skiping update on %s because there is not new production, Matched production count = %d"
                    % (factory_slug, len(matched))
                }
            else:
                response = requests.post(
                    self.endpoint_base_url + self.production_url,
                    data=json.dumps(new),
                    headers=self.headers,
                )
                if response.status_code == 201:
                    return {"info": response.json()}
                else:
                    return {"error": "failed to create bulk production data"}
        else:
            return {"error": "failed to find factory"}

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

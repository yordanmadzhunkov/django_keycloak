# pip install requests
import requests
from prettytable import PrettyTable
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from tzlocal import get_localzone # $ pip install tzlocal


from decouple import config


# Send a GET request to a website
#res = requests.get(
#    "https://www.example.com/", # The URL of the API you want to access
#    params={"key1": "value1", "key2": "value2"}, # The parameters you want to pass to the API (like "?key=value" at the end of the URL)
#    data={"key1": "value1", "key2": "value2"}, # The data you want to send to the API
#    headers={"header1": "value1", "header2": "value2"}, # The headers you want to send to the API
#    cookies={"cookie1": "value1", "cookie2": "value2"}, # The cookies you want to send to the API
#    auth=("username", "password"), # The authentication credentials you want to send to the API (some websites require this)
#    timeout=5, # The maximum site response time (in seconds) 
#    allow_redirects=True, # Whether or not to follow redirects
#)

# Send a POST request to a website
#res = requests.post(...)

# Send a PUT request to a website
#res = requests.put(...)

# Send a DELETE request to a website
#res = requests.delete(...)


#if res.status_code == 200:
#    output = res.json()
#    print(output)

class EnergyPrices:
    base_url = 'https://api.energy-charts.info'
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
        openapi_spec = requests.get(self.base_url + '/openapi.json')
        if openapi_spec.status_code == 200:
            openapi_spec = openapi_spec.json()

            openapi    = openapi_spec['openapi']
            info       = openapi_spec['info']
            paths      = openapi_spec['paths']
            components = openapi_spec['components']
            tags       = openapi_spec['tags']

            print("OpenAPI version: " + openapi)
            print(info.keys())
            print(info['title'] + ': v' + info['version']) 
            print(info['description'])
            print('-------------------------------------------------')
            table = PrettyTable(["Path", "Summary"])
            table.align["Path"] = "l"
            table.align["Summary"] = "c"
            for p in paths.keys():
                table.add_row([p, paths[p]['get']['summary']])
            print(table)

    def fetch_prices_day_ahead(self, billing_zone='BG'):
        prices = requests.get(
            self.base_url + '/price', # The URL of the API you want to access
            params={"bzn": billing_zone,}, # The parameters you want to pass to the API (like "?key=value" at the end of the URL)
        )
        if prices.status_code == 200:
            return prices.json()
        return None
    
    def print_prices(self, prices, billing_zone):
        unit = prices['unit']
        price = prices['price']
        time_slot_in_unix = prices['unix_seconds']

        prices_table = PrettyTable(["UTC Date", "UTC Time", "Price " + unit, "Local Time", "Local Date"])
        prices_table.title = 'Billing zone = ' + self.billing_zones[billing_zone]
        for i in range(len(price)):
            d = datetime.fromtimestamp(time_slot_in_unix[i], tz=timezone.utc)
            p = Decimal(price[i]).quantize(Decimal('0.01'))
            #print(d + ' '  + str(price[i]) + ' ' + unit)
            ld = d.astimezone(get_localzone())
            prices_table.add_row([d.strftime('%Y-%m-%d'), 
                                      d.strftime('%H:%M:%S %Z'), 
                                      p, 
                                      ld.strftime('%H:%M:%S %Z'),
                                      ld.strftime('%Y-%m-%d')])
        print(prices_table)



class VeiPlatformAPI:
    token = None
    endpoint_base_url = 'http://127.0.0.1:8000/'
    hello_url         = 'api/v1/hello'
    billing_zone_url  = 'api/v1/billing_zones'
    plans_url         = 'api/v1/plans'
    prices_url        = 'api/v1/prices'


    def __init__(self, endpoint_url, token):
        self.token = token
        self.endpoint_base_url = endpoint_url
        self.headers = {'Authorization': 'Token ' + token}

    def check_billing_zone(self, billing_zone):
        response = requests.get(self.endpoint_base_url + self.billing_zone_url,
                data={}, 
                headers=self.headers,
        )
        if response.status_code == 200:
            found = None
            for zone in response.json():
                if zone['code'] == billing_zone:
                    found = zone
        else:
            return {'error': 'response Status is not OK'}
        
        if not found:
            return {'error': 'Billing zone ' + billing_zone + 'is NOT supported'}
        
        return {'check_billing_zone': 'OK', 
                'code': found['code'], 
                'name': found['name']
                }
    
    def get_plan(self, billing_zone, name=None):
        response = requests.get(self.endpoint_base_url + self.plans_url,
                data={}, 
                headers=self.headers,
        )
        if response.status_code == 200:
            target_plan = None
            for plan in response.json():
                if plan['billing_zone'] == billing_zone:
                    if name is None or name == plan['name']:
                        target_plan = plan
                        break
                    else:
                        print('skipping %s' % str(plan) )

            return {'plan': target_plan}
        else:
            return {'error': 'response Status is not OK'}
        
    def create_plan(self, billing_zone, name):
        data = {
                    'name': name, 
                    'billing_zone': billing_zone, 
                    'description': 'Most basic day ahead plan', 
                    'currency': 'EUR',
                    'electricity_unit': 'MWh',
        }
        response = requests.post(self.endpoint_base_url + self.plans_url,
                data=data, 
                headers=self.headers,
        )
        if response.status_code == 201:
            plan = response.json()
            # plan ['name'] == 'Day ahead'
            # plan ['billing_zone'] == 'BG')
            # plan ['description'], 'Most basic test plan')
            # plan ['currency'] == 'EUR'
            # plan ['electricity_unit'] == 'MWh'
            # plan ['slug'] == 'day-ahead-1')
            # paln ['owner'] == 'energy_bot
            print('created ' + str(plan))
            return {'plan': plan}
        else:
            return {'error': 'response Status is not CREATED'}
        

    def get_or_create_plan(self, billing_zone):
        res = self.check_billing_zone(billing_zone)
        if 'error' in res.keys():
            return res
        zone_name = res['name']
        plan_name = 'Day ahead %s' % zone_name
        res.update(self.get_plan(billing_zone=billing_zone, name=plan_name))

        if not 'error' in res.keys() and 'plan' in res.keys():
            if res['plan'] is None:
                res.update(self.create_plan(billing_zone=billing_zone, name=plan_name))
        return res


    def post_prices(self, billing_zone, prices):
        res = self.get_or_create_plan(billing_zone)
        if 'error' in res.keys() or not 'plan' in res.keys():
            return res
        # print('We have a plan = ' + str(res))
        # print(prices)
        data = {
            'blz': billing_zone,
            'unit': prices['unit'],
            'price': prices['price'],
            'unix_seconds': prices['unix_seconds'],
        }

        unit = prices['unit']
        price = prices['price']
        time_slot_in_unix = prices['unix_seconds']
        plan_slug = res['plan']['slug']

        prices_table = PrettyTable(["UTC Date", "UTC Time", "Price " + unit, "Status"])
        prices_table.title = 'Name = ' + res['plan']['name'] + \
                            ' Slug = ' + res['plan']['slug']
        # skipping {
        # 'name': 'Day ahead', 
        # 'billing_zone': 'SK', 
        # 'description': 'Most basic day ahead plan', 
        # 'currency': 'EUR', 
        # 'electricity_unit': 'MWh', 
        # 'slug': 'day-ahead-17fb', 
        # 'owner': 'energy_bot'}


        for i in range(len(price)):
            start_interval = datetime.fromtimestamp(time_slot_in_unix[i], tz=timezone.utc)
            end_interval = start_interval + timedelta(hours=1)
            p = Decimal(price[i]).quantize(Decimal('0.01'))
            data = {
                'plan': plan_slug, 
                'price': str(p),
                'start_interval': start_interval.strftime("%Y-%m-%dT%H:%M:%S%z"),
                'end_interval': end_interval.strftime("%Y-%m-%dT%H:%M:%S%z"),
            }

            params = {
                'plan': plan_slug, 
                'start_interval': start_interval.strftime("%Y-%m-%dT%H:%M:%S%z"),
                'end_interval': end_interval.strftime("%Y-%m-%dT%H:%M:%S%z"),
            }

            response = requests.get(self.endpoint_base_url + self.prices_url,
                params=params, 
                headers=self.headers,
            )
            if response.status_code == 200:
                if len(response.json()) == 0:
                    response = requests.post(self.endpoint_base_url + self.prices_url,
                        data=data, 
                        headers=self.headers,
                    )
                    if response.status_code == 201:
                        status = 'Created'
                    else:
                        status = str(response.json())
                else:
                    if p == Decimal(response.json()[0]['price']):
                        status = 'Price match'
                    else:
                        status = 'Price don''t match ' + str(response.json()[0]['price'])
            else:
                status = str(response.json())

            prices_table.add_row([start_interval.strftime('%Y-%m-%d'), 
                                  start_interval.strftime('%H:%M:%S %Z'), 
                                  p, status,])

        return prices_table


import json


if __name__ == '__main__':

    ENERGY_BOT_TARGETS = config('ENERGY_BOT_TARGETS', '[{"url": "http://127.0.0.1:8000/", "token":"6da8aa16d75593c3d9c7029acc59caf59dd5a446"},{"url":"https://fractionenergy.eu/", "token":"dfgsgfdsfsdgd"}]')

    target_list = json.loads(ENERGY_BOT_TARGETS)

    for target in target_list:
        print("Target %s token=%.4s.." % (target['url'], target['token']))

    energy_prices_api = EnergyPrices()
    #energy_prices_api.fetch_and_print_openapi_specs()

    
    
    for zone in energy_prices_api.billing_zones.keys():
        prices = energy_prices_api.fetch_prices_day_ahead(zone)
        if prices:
            energy_prices_api.print_prices(prices, zone)
            for target in target_list:
                try:
                    vei_platform = VeiPlatformAPI(target['url'], token=target['token'])
                    res = vei_platform.post_prices(zone, prices)
                    if isinstance(res, dict) and 'error' in res.keys():
                        print("Error \"%s\" when processing Target %s token=%.4s.." % (res['error'], target['url'], target['token']))
                    print(res)
                except Exception as e:
                    message = getattr(e, 'message', repr(e))
                    print("Exception %s when processing Target %s token=%.4s.." % (message, target['url'], target['token']))
        else:
            print("Fail to fetch zone = " + zone)


 
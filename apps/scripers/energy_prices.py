# pip install requests
import requests
from prettytable import PrettyTable
from decimal import Decimal
from datetime import datetime, timezone
from tzlocal import get_localzone # $ pip install tzlocal

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

    def __init__(self, endpoint_url, token):
        self.token = token
        self.endpoint_base_url = endpoint_url
        self.headers = {'Authorization': 'Token ' + token}


    def post_prices(self, billing_zone, prices):
        data = {
            'blz': billing_zone,
            'unit': prices['unit'],
            'price': prices['price'],
            'unix_seconds': prices['unix_seconds'],
        }
        res = requests.post(
               self.endpoint_base_url + "api/hello", # The URL of the API you want to access
                data=data, # The data you want to send to the API
                headers=self.headers, # The headers you want to send to the API
        )
        return res


if __name__ == '__main__':
    print('Running Energy prices as main function')
    energy_prices_api = EnergyPrices()
    vei_platform = VeiPlatformAPI('http://127.0.0.1:8000/', 
                                  token='6da8aa16d75593c3d9c7029acc59caf59dd5a446')
    #energy_prices_api.fetch_and_print_openapi_specs()
    for zone in energy_prices_api.billing_zones.keys():
        prices = energy_prices_api.fetch_prices_day_ahead(zone)
        if prices:
            energy_prices_api.print_prices(prices, zone)
            res = vei_platform.post_prices(zone, prices)
            break
        else:
            print("Fail to fetch zone = " + zone)


 
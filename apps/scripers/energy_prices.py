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

if __name__ == '__main__':
    print('Running Energy prices as main function')
    base_url = 'https://api.energy-charts.info'
    openapi_spec = requests.get(base_url + '/openapi.json')
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
            print(str(p) + ' -> ' + str(paths[p]['get']['parameters']))
        print(table)


        prices = requests.get(
            base_url + '/price', # The URL of the API you want to access
            params={"bzn": "BG",}, # The parameters you want to pass to the API (like "?key=value" at the end of the URL)
        )
        if prices.status_code == 200:
            prices = prices.json()
            #datetime.utcfromtimestamp(posix_time).strftime('%Y-%m-%dT%H:%M:%SZ')
            #print(prices['unix_seconds'])
            #print(prices['price'])
            unit = prices['unit']
            price = prices['price']
            time_slot_in_unix = prices['unix_seconds']

            prices_table = PrettyTable(["UTC Date", "UTC Time", "Price " + unit, "Local Time", "Local Date"])
   
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
            dest_url = "http://127.0.0.1:8000/api/hello"
            headers = {'Authorization': 'Token 6da8aa16d75593c3d9c7029acc59caf59dd5a446'}
            res = requests.post(
                "http://127.0.0.1:8000/api/hello", # The URL of the API you want to access
#    params={"key1": "value1", "key2": "value2"}, # The parameters you want to pass to the API (like "?key=value" at the end of the URL)
                data={"key1": "value1", "key2": "value2"}, # The data you want to send to the API
                headers=headers, # The headers you want to send to the API
#    cookies={"cookie1": "value1", "cookie2": "value2"}, # The cookies you want to send to the API
#    auth=("username", "password"), # The authentication credentials you want to send to the API (some websites require this)
#    timeout=5, # The maximum site response time (in seconds) 
#    allow_redirects=True, # Whether or not to follow redirects
                )
            if res.status_code == 200:
                print(res.json())
            
        #print(info['termsOfService'])
        #print(info['contact']) 
        #print(info['license'])
                  
 
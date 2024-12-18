import json

from ibex import IBexScriper
from energy_charts_api import EnergyChartsAPI

from decouple import config
from datetime import datetime, timezone

if __name__ == "__main__":

    # ENERGY_BOT_TARGETS = config('ENERGY_BOT_TARGETS', '[{"url": "http://127.0.0.1:8000/", "token":"6da8aa16d75593c3d9c7029acc59caf59dd5a446"},{"url":"https://fractionenergy.eu/", "token":"dfgsgfdsfsdgd"}]')
    ENERGY_BOT_TARGETS = config(
        "ENERGY_BOT_TARGETS",
        '[{"url": "http://127.0.0.1:8000/", "token":"6da8aa16d75593c3d9c7029acc59caf59dd5a446"},',
    )

    target_list = json.loads(ENERGY_BOT_TARGETS)

    for target in target_list:
        print("Target %s token=%.4s.." % (target["url"], target["token"]))

    IBexScriper().process(target_list)
    EnergyChartsAPI().process(target_list)
    EnergyChartsAPI().process_historical(target_list, months=3)

    # start_time = datetime(2024, 10, 1, 00, 00, 00, tzinfo=timezone.utc)
    # end_time = datetime(2024, 11, 1, 00, 00, 00, tzinfo=timezone.utc)
    # EnergyChartsAPI().process(target_list, start=start_time, end=end_time)

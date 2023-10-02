from bs4 import BeautifulSoup
import requests
from time import sleep
import re
import datetime
from decimal import Decimal

from django_q.tasks import async_task

from .models import add_factory, ElectricityFactory

from .scripers.veiregistar import VEIEegistarScriper
from .scripers.papagal import PapagalScriper


def add_factory_hook(task):
    add_factory(task)


def scripe_factories_list(page_number):
    scriper = VEIEegistarScriper()
    factories = scriper.scripe_factories_list(page_number)
    for href in factories:
        async_task("core.tasks.scripe_factory_page",
                   href,
                   task_name=href,
                   hook=add_factory_hook)
    next_page = page_number + 1
    if len(factories) > 0:
        async_task("core.tasks.scripe_factories_list",
                   next_page,
                   task_name=scriper.factories_list_url(next_page),
                   )


def scripe_factory_page(href):
    return VEIEegistarScriper().scripe_factory(href)


def scripe_factory_legal_entity(factory):
    if isinstance(factory, ElectricityFactory):
        scriper = PapagalScriper()
        info = None
        if info is None:
            info = scriper.scripe(factory.tax_id)
        if info is None:
            info = scriper.scripe(factory.owner_name)
        if info is not None:
            info['source'] = scriper.base_url
        print(info)
        return info
    return None


def scripe_legal_entty(params):
    print(params)

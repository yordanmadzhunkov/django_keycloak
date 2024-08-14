from bs4 import BeautifulSoup
import requests
from time import sleep
import re
import datetime
from decimal import Decimal

from django_q.tasks import async_task

from .models.factory import ElectricityFactory

from scripers.veiregistar import VEIEegistarScriper
from scripers.papagal import PapagalScriper


def parse_energy_type(energy_type_in_bg):
    map = {
        "ВЕЦ": ElectricityFactory.HYDROPOWER,
        "МВЕЦ": ElectricityFactory.HYDROPOWER,
        "ПАВЕЦ": ElectricityFactory.HYDROPOWER,
        "Каскада": ElectricityFactory.HYDROPOWER,
        "БиоЕЦ": ElectricityFactory.BIOMASS,
        "БиоГЕЦ": ElectricityFactory.REN_GAS,
        "ФЕЦ": ElectricityFactory.PHOTOVOLTAIC,
        "ФтЦ": ElectricityFactory.PHOTOVOLTAIC,
        "ВтЕЦ": ElectricityFactory.WIND_TURBINE,
    }
    return map[energy_type_in_bg.replace('"', "")]


def add_factory(task):
    result = task.result
    factories = ElectricityFactory.objects.filter(name=result["name"])
    factory_type = parse_energy_type(result["energy"])
    if len(factories) == 0:
        factory = ElectricityFactory(
            name=result["name"],
            factory_type=factory_type,
            manager=None,
            location=result["location"],
            opened=result["opened"],
            capacity_in_mw=result["capacity"],
            primary_owner=None,
            tax_id=result["eik"],
            owner_name=result["owner"],
        )
        factory.save()
    else:
        factory = factories[0]
        if factory.manager is None:
            # trigger scriping of legal entity
            factory.save()
        print(
            "Factory found name='%s' type='%s'" % (factory.name, factory.factory_type)
        )


def scripe_factories_list(page_number, limit=-1):
    scriper = VEIEegistarScriper()
    factories = scriper.scripe_factories_list(page_number)
    for href in factories:
        async_task(
            "vei_platform.tasks.scripe_factory_page",
            href,
            task_name=href,
            hook=add_factory,
        )
    next_page = page_number + 1
    if len(factories) > 0 and limit > 0:
        async_task(
            "vei_platform.tasks.scripe_factories_list",
            next_page,
            task_name=scriper.factories_list_url(next_page),
            limit=limit - 1,
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
            info["source"] = scriper.base_url
        return info
    return None


def scripe_legal_entity(tax_id):
    scriper = PapagalScriper()
    info = scriper.scripe(tax_id)
    if info is not None:
        info["source"] = scriper.base_url
    return info

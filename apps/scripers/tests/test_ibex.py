
from scripers.ibex import parse_ibex
from bs4 import BeautifulSoup
from django.test import TestCase


class IbexScriperTest(TestCase):
    def test_parse_ibex_0_html(self):
        with open("output1.html", "r") as file:
            content = file.read()
            soup = BeautifulSoup(content, 'html.parser')
            res = parse_ibex(soup)
            print(res)
            #soup = 
            #file.write(str(soup))
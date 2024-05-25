from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
#from rest_framework.test import APIRequestFactory
#from myproject.apps.core.models import Account
import json
from rest_framework.exceptions import ErrorDetail
from api.electricity_prices import ElectricityPricesSerializer

class ElectricityPriceAPITestCases(APITestCase):
    def test_billing_zones_get_objects(self):
        """
        Ensure we have at least one billing zone in data base
        """
        url = reverse('billing_zones')
        data = {}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 45)
        self.assertEqual(self.client.post  (url, data, format='json').status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.put   (url, data, format='json').status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.delete(url, data, format='json').status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_billing_zones_has_bulgaria(self):
        """
        Ensure we have at least one billing zone for Bulgaria
        """
        url = reverse('billing_zones')
        data = {}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 45)
        bg_code = {'code':'BG', 'name': 'Bulgaria'}
        foundBG = False
        for c in response.data:
            if c == bg_code:
                foundBG = True
                break
        self.assertTrue(foundBG)

    def test_create_electricity_price_plan(self):
        """
        Ensure we have at least one billing zone for Bulgaria
        """
        url = reverse('price_series')
        data = {}
        response = self.client.get(url, data, format='json')
       # print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        

    def test_create_electricity_price_plan(self):
        """
        Ensure we have at least one billing zone for Bulgaria
        """
        url = reverse('price_series')
        bg_code = {'code':'BG', 'name': 'Bulgaria'}
        data = {
            'name': 'Test plan 1', 
            'billing_zone': bg_code['code'], 
            'description': 'Most basic test plan', 
            'currency': 'EUR',
            'electricity_unit': 'MWh',
            }
        response = self.client.post(url, data, format='json')
        #print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test plan 1')
        self.assertEqual(response.data['billing_zone'], 'BG')
        self.assertEqual(response.data['description'], 'Most basic test plan')
        self.assertEqual(response.data['currency'], 'EUR')
        self.assertEqual(response.data['electricity_unit'], 'MWh')
        self.assertEqual(response.data['slug'], 'test-plan-1')
        self.assertFalse('pk' in response.data.keys())




    def test_create_electricity_price_plan_wrong_unit(self):
        """
        Ensure we have at least one billing zone for Bulgaria
        """
        url = reverse('price_series')
        bg_code = {'code':'BG', 'name': 'Bulgaria'}
        data = {
            'name': 'Test plan 1', 
            'billing_zone': bg_code['code'], 
            'description': 'Most basic test plan', 
            'currency': 'EUR',
            'electricity_unit': 'dWh',
            }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['electricity_unit'], 
                         [ErrorDetail(string='"dWh" is not a valid choice.', code='invalid_choice')])

 

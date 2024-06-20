from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
#from rest_framework.test import APIRequestFactory
#from myproject.apps.core.models import Account
import json
from rest_framework.exceptions import ErrorDetail
from api.electricity_prices import ElectricityPricesSerializer

from django.contrib.auth.models import User
#from django.contrib.auth import get_user_model
#UserModel = get_user_model()
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token


from vei_platform.models.electricity_price import ElectricityPricePlan, ElectricityBillingZone
from vei_platform.api.electricity_prices import ElectricityPriceSerializer

class ElectricityPriceAPIWithUserTestCases(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='123')
        self.client.force_authenticate(self.user)
        
    def tearDown(self):
        self.user.delete()

    def test_create_electricity_price_plan_with_user(self):
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
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test plan 1')
        self.assertEqual(response.data['billing_zone'], 'BG')
        self.assertEqual(response.data['description'], 'Most basic test plan')
        self.assertEqual(response.data['currency'], 'EUR')
        self.assertEqual(response.data['electricity_unit'], 'MWh')
        self.assertEqual(response.data['slug'], 'test-plan-1')
        self.assertEqual(response.data['owner'], 'testuser')

    def test_create_electricity_price_plan_twice(self):
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
        self.assertEqual(response.data['owner'], 'testuser')

        self.assertFalse('pk' in response.data.keys())

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test plan 1')
        self.assertEqual(response.data['billing_zone'], 'BG')
        self.assertEqual(response.data['description'], 'Most basic test plan')
        self.assertEqual(response.data['currency'], 'EUR')
        self.assertEqual(response.data['electricity_unit'], 'MWh')
        self.assertEqual(response.data['owner'], 'testuser')
        self.assertNotEqual(response.data['slug'], 'test-plan-1')
        self.assertFalse('pk' in response.data.keys())

    def test_get_electricity_price_plans(self):
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
        data = {}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test plan 1')
        self.assertEqual(response.data[0]['billing_zone'], 'BG')
        self.assertEqual(response.data[0]['description'], 'Most basic test plan')
        self.assertEqual(response.data[0]['currency'], 'EUR')
        self.assertEqual(response.data[0]['electricity_unit'], 'MWh')
        self.assertEqual(response.data[0]['slug'], 'test-plan-1')
        self.assertEqual(response.data[0]['owner'], 'testuser')

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

    def test_get_electricity_price_plan(self):
        """
        Ensure we have at least one billing zone for Bulgaria
        """
        url = reverse('price_series')
        data = {}
        response = self.client.get(url, data, format='json')
       # print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_electricity_price_plan_no_access(self):
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
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_create_electricity_price_plan_no_user(self):
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
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


        
    
class ElectricityPricePriceSeriesAPITestCases(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='123')
        self.client.force_authenticate(self.user)
        self.billing_zone_object = ElectricityBillingZone.objects.filter(code='BG')[0]
        self.plan = ElectricityPricePlan.objects.create(
            name='Day ahead price pac',
            electricity_unit = 'kWh',
            billing_zone = self.billing_zone_object,
            currency = 'EUR',
            owner=self.user,
        )
        self.plan.save()
        
    def tearDown(self):
        self.plan.delete()
        self.user.delete()
        
    def test_get_price_day_1_hour(self):
        """
        Get price for specific plan by a slug
        """
        url = reverse('prices')
        data = {'plan_slug': self.plan.slug,}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 0)

    def test_electricity_price_serializer(self):
        data = {'plan': self.plan.slug, 
                'price': '10.19',
                'start_interval': '2024-05-19T11:00+00:00',
                'interval_length': 3600,
        }
        serializer = ElectricityPriceSerializer(data=data)
        self.assertTrue(serializer.is_valid(raise_exception=False))
 

    def test_create_price_day_1_hour(self):
        """
        Get price for specific plan by a slug
        """
        url = reverse('prices')
        data = {'plan': self.plan.slug, 
                'price': '10.19',
                'start_interval': '2024-05-19T11:00',
                'interval_length': 3600,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(len(response.data), 1)


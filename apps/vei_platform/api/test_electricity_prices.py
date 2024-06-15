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
        self.assertFalse('pk' in response.data.keys())

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test plan 1')
        self.assertEqual(response.data['billing_zone'], 'BG')
        self.assertEqual(response.data['description'], 'Most basic test plan')
        self.assertEqual(response.data['currency'], 'EUR')
        self.assertEqual(response.data['electricity_unit'], 'MWh')
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
        #print(ElectricityPricePlan.objects.all())
        self.plan = ElectricityPricePlan.objects.create(
            name='Day ahead price pac',
            electricity_unit = 'kWh',#  ElectricityPricePlan.ELECTRICITY_UNIT_CHOISES.kWh,
            billing_zone = self.billing_zone_object,
            currency = 'EUR',
            owner=self.user,
        )
        self.plan.save() # generate slug
        
        #print("plan pk = %d" % self.plan.pk)
        #print(ElectricityPricePlan.objects.all())

        #self.plan = ElectricityPricePlan.objects.create(name='Test plan 1', )
        #url = reverse('price_series')
        #bg_code = {'code':'BG', 'name': 'Bulgaria'}
        #data = {
        #    'name': 'Test plan 1', 
        #    'billing_zone': bg_code['code'], 
        #    'description': 'Most basic test plan', 
        #    'currency': 'EUR',
        #    'electricity_unit': 'MWh',
        #    }
        #response = self.client.post(url, data, format='json')
        #self.plan_slug = response
        
    def tearDown(self):
        #print('tear down')
        #self.plan = None
        #print(self.plan.slug)
        self.plan.delete()
        #print(ElectricityPricePlan.objects.filter(slug=self.plan.slug).delete())
        #ElectricityPricePlan.objects.all().delete()
        #print(ElectricityPricePlan.objects.all())

        #   pass    
        #self.plan.

        self.user.delete()
        #self.plan = 
        #print(ElectricityPricePlan.objects.all())
        #ElectricityPricePlan.objects.filter(pk=self.plan.pk).delete()
        #print(ElectricityPricePlan.objects.all())
        

 
    def test_create_price_day_1_hour(self):
        pass
        #print('\n')
        #print(self.billing_zone_object)
        #print('\n')
        #self.plan = ElectricityPricePlan.objects.create(
        #    name='Day ahead price',
        #    electricity_unit = 'kWh',#  ElectricityPricePlan.ELECTRICITY_UNIT_CHOISES.kWh,
        #    billing_zone = self.billing_zone_object,
        #)
        #self.plan.save()
        #print(self.plan.slug)

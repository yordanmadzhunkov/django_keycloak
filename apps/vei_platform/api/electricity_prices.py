from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import generics, serializers
from vei_platform.models.electricity_price import ElectricityPrice, ElectricityPricePlan, ElectricityBillingZone




# This tutorial basically covers all REST + token auth
# https://learndjango.com/tutorials/official-django-rest-framework-tutorial-beginners
class HelloView(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    def get(self, request):
        print(request.headers)
        content = {'message': 'Hello, World!'}
        return Response(content)
    
    def post(self, request):
        #print(request.data)
        #print(request.data.keys())
        if request.data:
            content = {'message': 'Hello, ' + str(request.user) + " Your data is = " + str(request.data)}
            print(request.data)
        else:
            content = {'message': 'Invalid data!!!'}
        return Response(content)
    



class ElectricityBillingZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectricityBillingZone
        fields = (
            "code",
            "name",
        )


class ElectricityBillingZoneListView(generics.ListAPIView):
    queryset = ElectricityBillingZone.objects.all()
    serializer_class = ElectricityBillingZoneSerializer


class ElectricityPricesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectricityPricePlan
        fields = ( "__all__")


class ElectricityPricesListView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = ElectricityPricePlan.objects.all()
    serializer_class = ElectricityPricesSerializer

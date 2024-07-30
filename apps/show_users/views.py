from django.http import HttpResponse
from django import template


def home(request):

    return HttpResponse("My First Home")

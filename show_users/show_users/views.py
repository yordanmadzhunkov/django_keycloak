from django.http import HttpResponse


def home(request):

    return HttpResponse('My First Home')

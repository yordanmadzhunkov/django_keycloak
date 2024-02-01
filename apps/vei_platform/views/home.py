from . import common_context

from django.shortcuts import render
from django.views import View

class Home(View):
    def get(self, request, *args, **kwargs):
        context = common_context(request)
        return render(request, "home.html", context)
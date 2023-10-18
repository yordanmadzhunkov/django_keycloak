from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from . import common_context
from vei_platform.forms import FactoryScriperForm
from vei_platform.models.profile import get_user_profile
from django.contrib import messages
from django_q.tasks import async_task


@login_required(login_url='/oidc/authenticate/')
def view_dashboard(request):
    context = common_context()
    context['profile'] = get_user_profile(request.user)
    scripe_form = FactoryScriperForm(request.POST)
    if request.method == "POST":
        # TODO, only admin should be able to trigger this
        if 'scripe_page' in request.POST and scripe_form.is_valid():

            # messages.error(request, 'Profile error')
            page_number = int(scripe_form.cleaned_data.get('page_number'))
            limit = 1
            async_task("vei_platform.tasks.scripe_factories_list",
                       page_number, limit)
            messages.success(
                request, 'Form is valid with number = %d' % page_number)

        if 'scripe_all' in request.POST:
            page_number = 1
            limit = 10000
            async_task("vei_platform.tasks.scripe_factories_list",
                       page_number, limit)
            messages.success(request, 'Scriping all pages!')
    context['scripe_form'] = scripe_form
    return render(request, "dashboard.html", context)
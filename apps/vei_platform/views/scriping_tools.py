from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from . import common_context
from vei_platform.forms import FactoryScriperForm
from vei_platform.models.profile import get_user_profile
from vei_platform.models.legal import LegalEntity, find_legal_entity, add_legal_entity
from django.contrib import messages
from django_q.tasks import async_task


@login_required(login_url='/oidc/authenticate/')
def view_scriping_tools(request):
    context = common_context()
    context['profile'] = get_user_profile(request.user)
    scripe_form = FactoryScriperForm(request.POST)
    if request.method == "POST":
        # TODO, only admin should be able to trigger this
        if 'scripe_page' in request.POST and scripe_form.is_valid():

            try:
                page_number = int(scripe_form.cleaned_data.get('page_number'))
                limit = 1
                async_task("vei_platform.tasks.scripe_factories_list",
                       page_number, limit)
                messages.success(request, 'Form is valid with number = %d' % page_number)
            except ValueError:
                messages.error(request, 'Form cleaned data = ' + str(scripe_form.cleaned_data))
            

        if 'scripe_all' in request.POST:
            page_number = 1
            limit = 10000
            async_task("vei_platform.tasks.scripe_factories_list",
                       page_number, limit)
            messages.success(request, 'Scriping all pages!')

        if 'scripe_tax_id' in request.POST and scripe_form.is_valid():
            tax_id = scripe_form.cleaned_data.get('tax_id')
            task_name="LegalEntity-for-%s" % tax_id
            async_task("vei_platform.tasks.scripe_legal_entity",
                       tax_id=tax_id,
                       hook=add_legal_entity)
            messages.success(request, 'Spawned %s' % task_name)

    context['scripe_form'] = scripe_form
    return render(request, "scriping_tools.html", context)